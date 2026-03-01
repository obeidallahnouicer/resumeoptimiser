"""LLMMatchAnalyzerAgent – deep LLM-powered CV↔Job comparison.

This agent runs BEFORE or alongside the embedding-based SemanticMatcher.
It uses the LLM to do a field-by-field analysis: skills, experience,
education, languages.  The output feeds into the final blended score.

Design:
- LLM injected via LLMClientProtocol
- Input: SemanticMatcherInput (cv + job)
- Output: LLMMatchAnalysisSchema
- Bilingual: works on French and English content natively
- Retries up to 2 times on JSON parse / validation failure
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.scoring import LLMMatchAnalysisSchema, SemanticMatcherInput

logger = get_logger(__name__)

_MAX_RETRIES = 2

_SYSTEM_PROMPT = """\
role: cv_job_match_analyzer
version: "1.0"
description: |
  You are a bilingual (FR/EN) recruitment matching engine.
  Given a STRUCTURED CV and a STRUCTURED JOB DESCRIPTION (both as JSON),
  perform a deep, field-by-field comparison and return a match analysis.

analysis_dimensions:

  skills_match:
    - Compare CV hard_skills + soft_skills + tools against Job hard_skills + soft_skills + tools.
    - For EACH skill the job requires, determine if the CV demonstrates it.
    - Account for synonyms and near-matches:
        "Python" ≈ "Python 3", "MS Excel" ≈ "Excel", "Gestion de projet" ≈ "Project Management"
    - Score 0.0–1.0 based on coverage ratio (found / total required).

  experience_match:
    - Compare CV total_years_experience vs Job min_years_experience.
    - Also compare the nature of experience (domains, seniority, relevance).
    - Score: 1.0 if meets/exceeds, proportionally less if under.

  education_match:
    - Compare CV education_level vs Job education_level.
    - Account for equivalences: a PhD exceeds a Master requirement, etc.
    - Check for relevant field of study if mentioned.
    - Score: 1.0 if meets/exceeds, 0.5 if close, 0.0 if far below.

  languages_match:
    - Compare CV languages_spoken vs Job languages_required.
    - Match language names regardless of format ("Français" ≈ "French").
    - Score: 1.0 if all required languages found, proportionally less otherwise.

  overall_llm_score:
    - Weighted blend: skills 40%, experience 30%, education 15%, languages 15%.
    - You MAY adjust slightly based on qualitative fit.

  skill_details:
    - For each job required skill (hard + soft + tools), provide:
        {"skill": "...", "found_in_cv": true/false, "cv_evidence": "brief quote or note"}

  strengths:
    - 3-5 bullet points: what the candidate does well for this role.
    - Use the language of the job posting.

  gaps:
    - 3-5 bullet points: what the candidate lacks for this role.
    - Use the language of the job posting.

  reasoning:
    - 2-4 sentences explaining the overall assessment.
    - Use the language of the job posting.

output_format:
  Return ONLY a valid JSON object. No markdown fences. No extra text.
  Schema:
    {
      "skills_match_score": 0.0,
      "experience_match_score": 0.0,
      "education_match_score": 0.0,
      "languages_match_score": 0.0,
      "overall_llm_score": 0.0,
      "skill_details": [
        {"skill": "...", "found_in_cv": true, "cv_evidence": "..."}
      ],
      "strengths": ["..."],
      "gaps": ["..."],
      "reasoning": "..."
    }

critical_rules:
  - ALL scores are floats between 0.0 and 1.0.
  - Return ONLY the JSON object. No markdown. No explanation outside the JSON.
  - JSON must be complete and valid. Do NOT let it get cut off.
  - Be generous but honest: a 0.7 skills match is very different from a 0.3.
""".strip()


class LLMMatchAnalyzerAgent(BaseAgent[SemanticMatcherInput, LLMMatchAnalysisSchema]):
    """Deep LLM-powered field-by-field CV↔Job comparison."""

    meta = AgentMeta(name="LLMMatchAnalyzerAgent", version="1.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def execute(self, input: SemanticMatcherInput) -> LLMMatchAnalysisSchema:  # noqa: A002
        logger.info("llm_match_analyzer.start")

        user_payload = self._build_user_message(input)
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                raw_json = self._llm.complete(system=_SYSTEM_PROMPT, user=user_payload)
                data = json.loads(raw_json)
                result = LLMMatchAnalysisSchema.model_validate(data)
                logger.info(
                    "llm_match_analyzer.success",
                    overall=result.overall_llm_score,
                    skills=result.skills_match_score,
                    attempt=attempt,
                )
                return result
            except Exception as exc:
                last_error = exc
                logger.warning("llm_match_analyzer.retry", attempt=attempt, error=str(exc))

        raise AgentExecutionError(self.meta.name, f"Failed after {_MAX_RETRIES + 1} attempts: {last_error}")

    @staticmethod
    def _build_user_message(input: SemanticMatcherInput) -> str:  # noqa: A002
        """Serialize the CV and Job into a compact JSON payload for the LLM."""
        cv_dict = input.cv.model_dump(mode="json", exclude={"raw_text"})
        job_dict = input.job.model_dump(mode="json", exclude={"raw_text"})
        return json.dumps({"cv": cv_dict, "job": job_dict}, ensure_ascii=False, indent=1)
