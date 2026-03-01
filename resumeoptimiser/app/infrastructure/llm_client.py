"""LLM client abstraction.

Wraps the OpenAI SDK (or any OpenAI-compatible provider such as NVIDIA NIM)
behind a Protocol so agents receive a clean, injectable interface with no
vendor lock-in.

Responsibilities:
- Send a chat-completion request with a structured prompt
- Return the raw string content of the first choice
- Strip any <think>…</think> reasoning blocks before returning
- Attempt to repair truncated JSON when the LLM hits max_tokens
- Raise LLMError on any API failure

NOT responsible for:
- Prompt construction (belongs to each agent)
- Response parsing (belongs to each agent)
- Retry logic (can be layered separately)
"""

from __future__ import annotations

import json
import re
from typing import Protocol, runtime_checkable

from openai import OpenAI, APIError

from app.core.config import LLMSettings
from app.core.exceptions import LLMError
from app.core.logging import get_logger

logger = get_logger(__name__)

# DeepSeek-R1 wraps its chain-of-thought in <think>…</think> before the
# actual answer.  Strip it so agents always receive clean output.
# Pattern 1: full <think>…</think> block
# Pattern 2: orphaned </think> close-tag and everything before it (when the
#             opening tag was cut off, e.g. the model emits reasoning without
#             the opening <think>)
_THINK_FULL_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_THINK_TAIL_RE = re.compile(r"^.*?</think>", re.DOTALL)

# The model often wraps JSON in markdown fences (```json … ```) despite
# being told not to.  Strip them so agents can call json.loads() directly.
_MD_FENCE_RE = re.compile(r"^```[a-zA-Z]*\n?(.*?)\n?```$", re.DOTALL)


def _strip_think(text: str) -> str:
    """Remove DeepSeek-R1 reasoning blocks from a completion string."""
    text = _THINK_FULL_RE.sub("", text)
    # If a dangling </think> remains the model started reasoning without the
    # opening tag — strip everything up to and including it.
    if "</think>" in text:
        text = _THINK_TAIL_RE.sub("", text)
    return text.strip()


def _strip_markdown_fence(text: str) -> str:
    """Unwrap ```json … ``` or ``` … ``` fences if present."""
    m = _MD_FENCE_RE.match(text.strip())
    return m.group(1).strip() if m else text


def _repair_json(text: str) -> str:
    """Best-effort repair of truncated / malformed JSON from the LLM.

    Common failure modes:
      - Truncated at max_tokens → missing closing brackets / braces
      - Trailing comma before closing bracket
      - Unterminated string literal

    If the text already parses, or doesn't look like JSON at all, return as-is.
    """
    stripped = text.strip()

    # Only attempt repair on text that looks like JSON (starts with { or [)
    if not stripped or stripped[0] not in ('{', '['):
        return text

    # Fast path: already valid
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    repaired = text.rstrip()

    # Strip trailing incomplete string value (unterminated quote)
    # e.g.  ..."some text that got cut
    # We drop everything after the last complete key-value pair.
    if repaired.count('"') % 2 != 0:
        # Find the last unmatched quote and truncate there
        last_quote = repaired.rfind('"')
        # Walk back to find the comma or opening bracket before this key
        before = repaired[:last_quote].rstrip()
        # If the char before the quote is a colon, this is a value – drop the whole k:v
        if before.endswith(':'):
            # Drop back to the comma or bracket before the key
            key_start = before.rfind('"')
            if key_start > 0:
                before_key = repaired[:key_start].rstrip().rstrip(',').rstrip()
                repaired = before_key
            else:
                repaired = before.rstrip(':').rstrip().rstrip(',').rstrip()
        elif before.endswith(','):
            repaired = before.rstrip(',').rstrip()
        else:
            # Inside an array element or value – just close the quote
            repaired = repaired[:last_quote] + '...'  + '"'

    # Strip any trailing comma(s)
    repaired = re.sub(r',\s*$', '', repaired)

    # Count open vs close brackets/braces and close them
    open_braces = repaired.count('{') - repaired.count('}')
    open_brackets = repaired.count('[') - repaired.count(']')

    # Close arrays first (inner), then objects (outer)
    repaired += ']' * max(open_brackets, 0)
    repaired += '}' * max(open_braces, 0)

    # Final trailing-comma cleanup (inside the now-closed structure)
    repaired = re.sub(r',\s*([}\]])', r'\1', repaired)

    # Verify the repair worked
    try:
        json.loads(repaired)
        logger.warning("llm_json_repaired", original_len=len(text), repaired_len=len(repaired))
        return repaired
    except json.JSONDecodeError:
        # Return original – let the caller raise a proper error
        logger.warning("llm_json_repair_failed", text_tail=text[-200:])
        return text


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Structural protocol for any LLM client."""

    def complete(self, system: str, user: str) -> str:
        """Return the assistant reply as a plain string."""
        ...


class OpenAILLMClient:
    """Concrete LLM client backed by any OpenAI-compatible Chat Completions API.

    Works with OpenAI, NVIDIA NIM, or any other provider that exposes
    the same ``/v1/chat/completions`` interface.

    Currently configured for the NVIDIA NIM ``openai/gpt-oss-120b`` model
    which supports proper ``system`` and ``user`` roles.

    Any ``<think>…</think>`` reasoning blocks are still stripped as a safety
    net in case a model emits them.
    """

    def __init__(self, settings: LLMSettings) -> None:
        self._settings = settings
        self._client = OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url if settings.base_url else None,
        )

    def complete(self, system: str, user: str) -> str:
        """Send a chat request and return the clean response text."""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        try:
            response = self._client.chat.completions.create(
                model=self._settings.model,
                temperature=self._settings.temperature,
                top_p=self._settings.top_p,
                max_tokens=self._settings.max_tokens,
                stream=False,
                messages=messages,
            )
        except APIError as exc:
            logger.error("llm_api_error", error=str(exc))
            raise LLMError(str(exc)) from exc

        return self._extract_and_clean(response)

    def _extract_and_clean(self, response: object) -> str:
        """Pull content from the response and strip reasoning blocks."""
        try:
            text = response.choices[0].message.content  # type: ignore[union-attr]
        except (AttributeError, IndexError) as exc:
            raise LLMError(f"Unexpected LLM response shape: {exc}") from exc

        if text is None:
            raise LLMError("LLM returned null content.")

        # Strip <think>…</think> reasoning blocks (safety net)
        text = _strip_think(text)
        # Unwrap ```json … ``` markdown fences the model adds despite instructions
        text = _strip_markdown_fence(text)
        # Attempt to repair truncated JSON (e.g. when max_tokens is hit)
        text = _repair_json(text)

        if not text:
            raise LLMError("LLM returned empty content after stripping reasoning blocks.")

        logger.debug("llm_response", chars=len(text), preview=text[:120])
        return text
