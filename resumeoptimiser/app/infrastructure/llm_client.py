"""LLM client abstraction.

Wraps the OpenAI SDK (or any OpenAI-compatible provider such as NVIDIA NIM)
behind a Protocol so agents receive a clean, injectable interface with no
vendor lock-in.

Responsibilities:
- Send a chat-completion request with a structured prompt
- Stream the response and accumulate the full text
- Return the raw string content of the first choice
- Raise LLMError on any API failure

NOT responsible for:
- Prompt construction (belongs to each agent)
- Response parsing (belongs to each agent)
- Retry logic (can be layered separately)
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from openai import OpenAI, APIError

from app.core.config import LLMSettings
from app.core.exceptions import LLMError
from app.core.logging import get_logger

logger = get_logger(__name__)


@runtime_checkable
class LLMClientProtocol(Protocol):
    """Structural protocol for any LLM client."""

    def complete(self, system: str, user: str) -> str:
        """Return the assistant reply as a plain string."""
        ...


class OpenAILLMClient:
    """Concrete LLM client backed by any OpenAI-compatible Chat Completions API.

    Works with OpenAI, NVIDIA NIM, or any other provider that exposes
    the same ``/v1/chat/completions`` interface.  When ``base_url`` is set
    in settings the client is pointed at that endpoint instead of api.openai.com.
    Responses are streamed so large outputs don't time out.
    """

    def __init__(self, settings: LLMSettings) -> None:
        self._settings = settings
        self._client = OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url if settings.base_url else None,
        )

    def complete(self, system: str, user: str) -> str:
        """Send a two-message chat request, stream the reply, and return the full text."""
        try:
            stream = self._client.chat.completions.create(
                model=self._settings.model,
                temperature=self._settings.temperature,
                top_p=self._settings.top_p,
                max_tokens=self._settings.max_tokens,
                stream=True,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
        except APIError as exc:
            logger.error("llm_api_error", error=str(exc))
            raise LLMError(str(exc)) from exc

        return self._collect_stream(stream)

    def _collect_stream(self, stream: object) -> str:
        """Iterate over streamed chunks and concatenate content deltas."""
        parts: list[str] = []
        try:
            for chunk in stream:  # type: ignore[union-attr]
                delta_content = chunk.choices[0].delta.content
                if delta_content is not None:
                    parts.append(delta_content)
        except (AttributeError, IndexError) as exc:
            raise LLMError(f"Unexpected LLM stream shape: {exc}") from exc

        text = "".join(parts)
        if not text:
            raise LLMError("LLM returned empty content.")
        return text
