"""CVRewriteAgent – rewrites CV sections to better match the job.

Constraint: LLM may only rewrite language. It must not invent experience.
The agent passes the explanation report to give the LLM specific targets.
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.report import CVRewriteInput, OptimizedCVSchema

logger = get_logger(__name__)

_SYSTEM_PROMPT = """
You are a professional CV writer. Rewrite the provided CV sections to better
align with the job description WITHOUT inventing experience that does not exist.

You receive:
- The original CV sections
- The job description
- A list of identified gaps

Return ONLY a valid JSON object matching this schema:
{
  "contact": {<same contact as input>},
  "sections": [
    {
      "section_type": "string",
      "raw_text": "string (rewritten text)",
      "items": ["string"]
    }
  ],
  "changes_summary": ["string (brief description of each change made)"]
}

Rules:
- Do NOT invent skills, degrees, or experience.
- Only rephrase, reorder, and emphasise existing content.
- Return ONLY the JSON.
""".strip()


class CVRewriteAgent(BaseAgent[CVRewriteInput, OptimizedCVSchema]):
    """Rewrites CV text to better match the target job (LLM-powered)."""

    meta = AgentMeta(name="CVRewriteAgent", version="1.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def execute(self, input: CVRewriteInput) -> OptimizedCVSchema:  # noqa: A002
        """Rewrite CV sections guided by the explanation report."""
        logger.info("cv_rewrite.start", job=input.job.title)

        user_prompt = self._build_prompt(input)
        raw_json = self._call_llm(user_prompt)
        schema = self._parse_and_validate(raw_json)

        logger.info("cv_rewrite.success", changes=len(schema.changes_summary))
        return schema

    def _build_prompt(self, input: CVRewriteInput) -> str:  # noqa: A002
        """Construct the user message with all context."""
        gaps = "\n".join(
            f"- {m.field}: {m.explanation}" for m in input.explanation.mismatches
        )
        sections = "\n".join(
            f"[{s.section_type.value}]\n{s.raw_text}" for s in input.cv.sections
        )
        return (
            f"Job: {input.job.title}\n"
            f"Required skills: {', '.join(s.skill for s in input.job.required_skills)}\n\n"
            f"Identified gaps:\n{gaps}\n\n"
            f"Current CV sections:\n{sections}"
        )

    def _call_llm(self, user_prompt: str) -> str:
        try:
            return self._llm.complete(system=_SYSTEM_PROMPT, user=user_prompt)
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, str(exc)) from exc

    def _parse_and_validate(self, raw_json: str) -> OptimizedCVSchema:
        try:
            data = json.loads(raw_json)
            return OptimizedCVSchema.model_validate(data)
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, f"Parse failed: {exc}") from exc
