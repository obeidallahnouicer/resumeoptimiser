"""MarkdownRewriteAgent – improves CV wording while preserving Markdown structure.

This is Step 2 of the layout-safe pipeline:
  original_cv.md → [this agent] → improved_cv.md

The LLM operates on structured Markdown and is STRICTLY forbidden from:
  - Changing section headings or their order
  - Inventing new bullet points, roles, or skills
  - Restructuring the document
  - Removing entire sections or bullets

The only allowed changes are:
  - Grammar corrections
  - Stronger action verbs
  - Clearer phrasing
  - Removing redundant words within existing bullets
"""

from __future__ import annotations

import json
import re

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.markdown import MarkdownRewriteInput, MarkdownRewriteOutput

logger = get_logger(__name__)

_MAX_RETRIES = 2

_SYSTEM_PROMPT = """\
role: cv_content_editor
version: "1.1"
description: |
  You are a senior technical CV editor. You receive a CV in structured Markdown
  and a target job description. Your task is to make the CV more impactful and
  better aligned with the job — without altering its structure or inventing facts.

STRICT STRUCTURE RULES — NEVER VIOLATE:
  1. Keep ALL headings (# ## ###) exactly as they are. Do not rename or reorder.
  2. Keep every bullet point (-). Do not add or delete bullets.
  3. Keep section order unchanged.
  4. Keep sub-headings (company, role, institution, dates) unchanged.
  5. Keep the candidate name and contact information unchanged.

CONTENT IMPROVEMENT RULES — APPLY AGGRESSIVELY:
  You MUST make at least 5 genuine wording improvements. Empty changes are unacceptable.
  
  Allowed improvements:
    a. Replace weak/passive verbs with strong action verbs:
         "was responsible for" → "owned"
         "helped with" → "contributed to"
         "worked on" → "engineered / built / delivered"
         "managed" → "led" / "directed" / "spearheaded"
    b. Add quantification where reasonable from existing context:
         "processed data" → "processed large-scale data pipelines"
         "improved performance" → "improved system performance significantly"
         Do NOT invent specific numbers that are not in the original.
    c. Align phrasing with the job description keywords naturally.
    d. Make sentences punchier: remove filler words, cut passive constructions.
    e. Fix any grammar errors.
    f. Strengthen the summary to mirror the target job title and key requirements.

  FORBIDDEN:
    - Adding new bullet points or new sections.
    - Deleting any bullet point or section.
    - Changing job titles, company names, dates, or education entries.
    - Inventing responsibilities, metrics, or skills not in the original.
    - Reordering sections.
    - Only changing hyphens or punctuation marks — that is NOT a real improvement.
    - Returning the same text with cosmetic Unicode changes (non-breaking hyphens, etc.)

IMPORTANT: Use only standard ASCII hyphens (-) in your output. Do NOT use:
  - non-breaking hyphens (‑)
  - en dashes (–)
  - em dashes (—)
  Use a regular hyphen (-) or rewrite the sentence to avoid it entirely.

OUTPUT FORMAT:
  Return a JSON object:
    {
      "improved_markdown": "<full improved Markdown as a single string>",
      "changes_summary": ["<change 1>", "<change 2>", ...]
    }
  - improved_markdown: the full Markdown text with improvements applied.
  - changes_summary: 5 to 10 concrete descriptions of changes made.
    Each entry should read like: "Replaced 'managed' with 'led' in STB Bank bullet 2"
  - No markdown fences inside the JSON string values.
  - Return ONLY the JSON object. No explanation outside the JSON.
""".strip()


class MarkdownRewriteAgent(BaseAgent[MarkdownRewriteInput, MarkdownRewriteOutput]):
    """Rewrites CV Markdown wording without touching structure or facts."""

    meta = AgentMeta(name="MarkdownRewriteAgent", version="1.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def execute(self, input: MarkdownRewriteInput) -> MarkdownRewriteOutput:  # noqa: A002
        logger.info("markdown_rewrite.start", job=input.job_title)

        user_prompt = self._build_prompt(input)
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                raw = self._call_llm(user_prompt)
                result = self._parse(raw)
                logger.info(
                    "markdown_rewrite.success",
                    changes=len(result.changes_summary),
                    attempt=attempt,
                )
                return result
            except AgentExecutionError as exc:
                last_error = exc
                logger.warning("markdown_rewrite.retry", attempt=attempt, error=str(exc))

        raise last_error  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_prompt(self, inp: MarkdownRewriteInput) -> str:
        parts = [
            "=== TARGET JOB ===",
            f"Title: {inp.job_title}" if inp.job_title else "(no job title provided)",
        ]

        if inp.job_description:
            # Truncate very long job descriptions
            jd = inp.job_description[:2000]
            parts += ["", "Job Description (excerpt):", jd]

        if inp.gap_analysis:
            parts += ["", "=== GAP ANALYSIS ===", inp.gap_analysis]

        parts += [
            "",
            "=== ORIGINAL CV (do not alter structure) ===",
            inp.original_markdown,
        ]
        return "\n".join(parts)

    def _call_llm(self, user_prompt: str) -> str:
        try:
            return self._llm.complete(system=_SYSTEM_PROMPT, user=user_prompt)
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, f"LLM call failed: {exc}") from exc

    def _parse(self, raw: str) -> MarkdownRewriteOutput:
        """Parse LLM JSON output, with fallback fence stripping."""
        text = raw.strip()
        # Strip accidental markdown fences
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        try:
            data = json.loads(text)
            return MarkdownRewriteOutput(
                improved_markdown=data["improved_markdown"],
                changes_summary=data.get("changes_summary", []),
            )
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, f"Parse failed: {exc}") from exc
