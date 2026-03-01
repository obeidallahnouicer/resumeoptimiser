"""ScoreExplainerAgent – uses the LLM to explain CV/Job mismatches.

Input: StructuredCV + StructuredJob + SimilarityScore
Output: ExplanationReport listing specific gaps with explanations.
Retries up to 2 times on JSON/validation failure.
Bilingual: adapts to the detected language of the CV/Job.
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError, LLMError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.report import ExplanationReportSchema, ScoreExplainerInput

logger = get_logger(__name__)

_MAX_RETRIES = 2

_SYSTEM_PROMPT = """\
role: career_gap_analyzer
version: "2.0"
description: |
  You are a bilingual (FR/EN) career coach.
  Given a structured CV, a structured job description, similarity scores,
  and optionally an LLM match analysis, identify and explain the SPECIFIC
  gaps between the candidate and the role.

language_rules:
  - Detect the language from the CV/Job data (detected_language field).
  - Write ALL output in that language.
  - If mixed, prefer the job posting language.

analysis_approach:
  - Use the enriched fields: hard_skills, soft_skills, tools, education_level,
    total_years_experience, languages_spoken (CV) vs the job equivalents.
  - If LLM analysis data is provided, leverage skill_details, strengths, gaps.
  - Focus on ACTIONABLE gaps the candidate can address.

  mismatches:
    - Each mismatch must have:
        field: category (e.g. "hard_skills", "experience", "education", "languages", "soft_skills")
        cv_value: what the candidate actually has
        job_expectation: what the job requires
        explanation: why it's a gap AND a concrete suggestion to fix it

  summary:
    - 2-3 sentence overall assessment.
    - Mention the strongest match areas and the biggest gaps.

output_format:
  Return ONLY a valid JSON object. No markdown fences. No explanation.
  Schema:
    {
      "mismatches": [
        {
          "field": "...",
          "cv_value": "...",
          "job_expectation": "...",
          "explanation": "..."
        }
      ],
      "summary": "..."
    }

critical_rules:
  - Be concise but specific. No vague advice.
  - Return ONLY the JSON. No markdown. No extra text.
  - JSON must be complete and valid.
  - Limit to 5-8 most important mismatches.
""".strip()


class ScoreExplainerAgent(BaseAgent[ScoreExplainerInput, ExplanationReportSchema]):
    """Generates a human-readable explanation of CV/Job mismatches via LLM."""

    meta = AgentMeta(name="ScoreExplainerAgent", version="2.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def execute(self, input: ScoreExplainerInput) -> ExplanationReportSchema:  # noqa: A002
        logger.info("score_explainer.start", overall_score=input.score.overall)

        user_prompt = self._build_prompt(input)

        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            raw_json = self._call_llm(user_prompt)
            try:
                schema = self._parse_and_validate(raw_json)
                logger.info("score_explainer.success", mismatches=len(schema.mismatches), attempt=attempt)
                return schema
            except (AgentExecutionError, LLMError) as exc:
                last_error = exc
                logger.warning("score_explainer.retry", attempt=attempt, error=str(exc))

        raise last_error  # type: ignore[misc]

    def _build_prompt(self, input: ScoreExplainerInput) -> str:  # noqa: A002
        """Build a rich user message using all enriched fields."""
        cv = input.cv
        job = input.job
        score = input.score

        lines = [
            "=== JOB ===",
            f"Title: {job.title}",
            f"Language: {job.detected_language}",
            f"Hard skills: {', '.join(job.hard_skills)}",
            f"Soft skills: {', '.join(job.soft_skills)}",
            f"Tools: {', '.join(job.tools)}",
            f"Min experience: {job.min_years_experience} years",
            f"Education: {job.education_level}",
            f"Languages required: {', '.join(job.languages_required)}",
            f"Methodologies: {', '.join(job.methodologies)}",
            f"Domain: {job.domain}",
            "",
            "=== CV ===",
            f"Name: {cv.contact.name}",
            f"Language: {cv.detected_language}",
            f"Hard skills: {', '.join(cv.hard_skills)}",
            f"Soft skills: {', '.join(cv.soft_skills)}",
            f"Tools: {', '.join(cv.tools)}",
            f"Experience: {cv.total_years_experience} years",
            f"Education: {cv.education_level}",
            f"Languages: {', '.join(cv.languages_spoken)}",
            f"Certifications: {', '.join(cv.certifications)}",
            "",
            "=== SCORES ===",
            f"Overall: {score.overall:.2f}",
            f"Embedding: {score.embedding_score:.2f}",
        ]

        for s in score.section_scores:
            lines.append(f"  {s.section_type.value}: {s.score:.2f}")

        if score.llm_analysis:
            a = score.llm_analysis
            lines.extend([
                "",
                "=== LLM ANALYSIS ===",
                f"Skills match: {a.skills_match_score:.2f}",
                f"Experience match: {a.experience_match_score:.2f}",
                f"Education match: {a.education_match_score:.2f}",
                f"Languages match: {a.languages_match_score:.2f}",
                f"Strengths: {'; '.join(a.strengths)}",
                f"Gaps: {'; '.join(a.gaps)}",
            ])

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
