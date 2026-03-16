"""IdealProfileAgent – generates an ideal candidate profile from the job description.

Purpose:
  Given a normalized job description, extract and synthesize what the ideal
  candidate profile looks like. This includes:
    - Role summary
    - Core competencies
    - Technical stack
    - Preferred action verbs
    - Impact patterns
    - Domain language

Output guides the two-stage rewrite process:
  1. Stage1 uses the language to rephrase CV wording
  2. Stage2 uses the competencies to address gaps

Bilingual: writes in the detected language of the job.
Retries up to 2 times on JSON/validation failure.
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError, LLMError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.report import IdealProfileInput, IdealProfileSchema
from app.services.prompt_cache_service import PromptCacheService

logger = get_logger(__name__)

_MAX_RETRIES = 2

# Agent name and version for prompt caching
_AGENT_NAME = "ideal_profile"
_AGENT_VERSION = "1.0"
_NONE_LISTED = "(none listed)"

_SYSTEM_PROMPT = """\
role: ideal_candidate_profiler
version: "1.0"
description: |
  You are a bilingual (FR/EN) job market expert and recruitment strategist.
  Given a structured job description, extract and synthesize the ideal
  candidate profile for that role.

  Your output guides the CV rewriting process. It must be:
    - Specific to the job (not generic)
    - Grounded in the job data (no hallucination)
    - Actionable for rewriting (concrete vocabulary)

language_rules:
  - Detect the language from the job data (detected_language field).
  - Write all output in that language.

analysis_approach:
  1. role_summary
     - 1-2 sentence high-level description of who the ideal candidate is.
     - Synthesize: job title + key responsibilities + domain context.
     - Example: "A Python-focused ML engineer with 5+ years designing
       production-grade ML systems in fintech environments."

  2. core_competencies
     - Extract 4-6 KEY capabilities (not specific tools, but competencies).
     - Base on: responsibilities, qualifications, hard_skills, soft_skills.
     - Example: ["Model Deployment", "Data Pipeline Design", "Infrastructure
       Optimization"]
     - Avoid: generic skills like "communication" unless explicitly required.

  3. technical_stack
     - List all technologies, tools, frameworks from:
       hard_skills, tools, methodologies fields.
     - Order by frequency/importance in the job description.
     - Example: ["Python", "Docker", "AWS", "Kubernetes", "Airflow"]
     - NO duplicates. NO tools not mentioned in the job.

  4. preferred_action_verbs
     - Extract 6-8 strong action verbs from the job description's
       responsibilities and requirements.
     - Focus on high-impact verbs: designed, implemented, optimized, deployed,
       architected, automated, scaled, engineered.
     - Example: ["designed", "deployed", "optimized", "architected", "scaled"]

  5. impact_patterns
     - Identify 5-7 common achievement patterns in the job.
     - These are typical quantifiable or qualitative outcomes for this role.
     - Example: ["improved model performance by X%", "reduced system latency",
       "automated manual workflows", "scaled infrastructure to X million users"]
     - Extract keywords from responsibilities and qualifications.
     - Write as incomplete phrases that can be completed with actual metrics.

  6. domain_language
     - Extract 6-10 domain-specific terms, industry jargon, and specialized
       terminology from the job description.
     - Example (fintech ML): ["production-grade ML systems", "model lifecycle
       management", "scalable data pipelines", "feature engineering",
       "model monitoring and drift detection"]
     - Focus on compound terms and concepts, not single words.

critical_constraints:
  - NEVER hallucinate technologies not in the job.
  - NEVER invent competencies or qualifications.
  - ONLY extract what is explicitly present in the job data.
  - Be concise: order lists by relevance, not quantity.
  - No duplicates in any list.

output_format:
  Return ONLY a valid JSON object. No markdown fences. No explanation.
  Schema:
    {
      "role_summary": "...",
      "core_competencies": ["...", "..."],
      "technical_stack": ["...", "..."],
      "preferred_action_verbs": ["...", "..."],
      "impact_patterns": ["...", "..."],
      "domain_language": ["...", "..."]
    }

  - role_summary: string (1-2 sentences)
  - core_competencies: array of 4-6 strings
  - technical_stack: array of tools/frameworks (no duplicates)
  - preferred_action_verbs: array of 6-8 verbs
  - impact_patterns: array of 5-7 patterns
  - domain_language: array of 6-10 domain terms
""".strip()


class IdealProfileAgent(BaseAgent[IdealProfileInput, IdealProfileSchema]):
    """Generates the ideal candidate profile from a normalized job description."""

    meta = AgentMeta(name="IdealProfileAgent", version="1.0.0")

    def __init__(
        self,
        llm: LLMClientProtocol,
        prompt_cache: PromptCacheService | None = None,
    ) -> None:
        self._llm = llm
        self._prompt_cache = prompt_cache

    def execute(self, input: IdealProfileInput) -> IdealProfileSchema:  # noqa: A002
        logger.info("ideal_profile.start", job_title=input.job.title)

        user_prompt = self._build_prompt(input)

        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                llm_response = self._llm.create_chat_completion(
                    model=self._llm.model,
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=1024,
                )
                response_text = llm_response.choices[0].message.content.strip()

                # Parse JSON response
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.warning(
                        "ideal_profile.json_decode_error",
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    last_error = e
                    continue

                # Validate and construct schema
                try:
                    schema = IdealProfileSchema(**data)
                    logger.info(
                        "ideal_profile.complete",
                        competencies_count=len(schema.core_competencies),
                        tech_stack_count=len(schema.technical_stack),
                    )
                    return schema
                except Exception as e:
                    logger.warning(
                        "ideal_profile.schema_validation_error",
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    last_error = e
                    continue

            except LLMError as e:
                logger.error("ideal_profile.llm_error", attempt=attempt + 1, error=str(e))
                last_error = e
                continue

        # All retries exhausted
        logger.error("ideal_profile.all_retries_exhausted")
        raise AgentExecutionError(
            f"IdealProfileAgent failed after {_MAX_RETRIES} retries: {last_error}"
        )

    def _build_prompt(self, input: IdealProfileInput) -> str:
        """Build the user prompt from the input."""
        job = input.job

        # Detect language (default to English)
        lang = getattr(job, "detected_language", "en") or "en"

        prompt_parts = []

        if lang == "fr":
            prompt_parts.append("Générez le profil candidat idéal à partir de cette offre d'emploi.\n")
        else:
            prompt_parts.append("Generate the ideal candidate profile from this job description.\n")

        # Provide structured job data
        prompt_parts.append(f"Job Title: {job.title}\n")
        if job.company:
            prompt_parts.append(f"Company: {job.company}\n")
        if job.domain:
            prompt_parts.append(f"Domain/Industry: {job.domain}\n")

        prompt_parts.append(f"Employment Type: {job.employment_type}\n")

        if job.min_years_experience > 0:
            prompt_parts.append(f"Experience Required: {job.min_years_experience}+ years\n")

        if job.education_level:
            prompt_parts.append(f"Education Level: {job.education_level}\n")

        prompt_parts.append("\n--- Hard Skills ---\n")
        prompt_parts.append(", ".join(job.hard_skills) if job.hard_skills else _NONE_LISTED)
        prompt_parts.append("\n\n--- Soft Skills ---\n")
        prompt_parts.append(", ".join(job.soft_skills) if job.soft_skills else _NONE_LISTED)
        prompt_parts.append("\n\n--- Tools & Technologies ---\n")
        prompt_parts.append(", ".join(job.tools) if job.tools else _NONE_LISTED)

        if job.methodologies:
            prompt_parts.append("\n\n--- Methodologies ---\n")
            prompt_parts.append(", ".join(job.methodologies))

        prompt_parts.append("\n\n--- Key Responsibilities ---\n")
        for resp in job.responsibilities[:5]:  # Limit to first 5
            prompt_parts.append(f"• {resp}\n")

        if job.qualifications:
            prompt_parts.append("\n--- Qualifications ---\n")
            for qual in job.qualifications[:5]:  # Limit to first 5
                prompt_parts.append(f"• {qual}\n")

        return "".join(prompt_parts)
