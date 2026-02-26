"""ScoreExplainerAgent – uses the LLM to explain CV/Job mismatches.

Input: StructuredCV + StructuredJob + SimilarityScore
Output: ExplanationReport listing specific gaps with explanations.
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError, LLMError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.report import ExplanationReportSchema, ScoreExplainerInput

logger = get_logger(__name__)

_SYSTEM_PROMPT = """
You are a career coach analysing a CV against a job description.
You are given similarity scores per CV section and must explain the mismatches.

Return ONLY a valid JSON object matching this schema:
{
  "mismatches": [
    {
      "field": "string (e.g. 'skills', 'experience')",
      "cv_value": "string (what the CV currently shows)",
      "job_expectation": "string (what the job requires)",
      "explanation": "string (why this is a gap)"
    }
  ],
  "summary": "string (1-2 sentence overall assessment)"
}

Be concise. Focus on actionable gaps. Return ONLY the JSON.
""".strip()


class ScoreExplainerAgent(BaseAgent[ScoreExplainerInput, ExplanationReportSchema]):
    """Generates a human-readable explanation of CV/Job mismatches via LLM."""

    meta = AgentMeta(name="ScoreExplainerAgent", version="1.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def execute(self, input: ScoreExplainerInput) -> ExplanationReportSchema:  # noqa: A002
        """Explain the gap between the CV and the job."""
        logger.info("score_explainer.start", overall_score=input.score.overall)

        user_prompt = self._build_prompt(input)
        raw_json = self._call_llm(user_prompt)
        schema = self._parse_and_validate(raw_json)

        logger.info("score_explainer.success", mismatches=len(schema.mismatches))
        return schema

    def _build_prompt(self, input: ScoreExplainerInput) -> str:  # noqa: A002
        """Build the user message from input data."""
        lines = [
            f"Job title: {input.job.title}",
            f"Required skills: {', '.join(s.skill for s in input.job.required_skills)}",
            f"CV name: {input.cv.contact.name}",
            "CV sections:",
        ]
        for section in input.cv.sections:
            lines.append(f"  [{section.section_type.value}]: {section.raw_text[:300]}")
        lines.append(f"Overall similarity score: {input.score.overall:.2f}")
        for s in input.score.section_scores:
            lines.append(f"  {s.section_type.value}: {s.score:.2f}")
        return "\n".join(lines)

    def _call_llm(self, user_prompt: str) -> str:
        try:
            return self._llm.complete(system=_SYSTEM_PROMPT, user=user_prompt)
        except LLMError:
            raise
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, str(exc)) from exc

    def _parse_and_validate(self, raw_json: str) -> ExplanationReportSchema:
        try:
            data = json.loads(raw_json)
            return ExplanationReportSchema.model_validate(data)
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, f"Parse failed: {exc}") from exc
