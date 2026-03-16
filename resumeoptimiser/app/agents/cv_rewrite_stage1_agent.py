"""CVRewriteStage1Agent – language transformation using ideal profile vocabulary.

Purpose:
  Rewrite CV bullet points using the vocabulary, action verbs, and domain
  language of the ideal profile. This makes the CV sound more aligned with
  the job without inventing new experience.

Focus:
  - Stronger verbs from ideal_profile.preferred_action_verbs
  - Domain terminology from ideal_profile.domain_language
  - Concrete language and specific achievements
  - NO new achievements or skills

Input:
  - Structured CV
  - IdealProfile (from IdealProfileAgent)

Output:
  - OptimizedCVSchema (same structure as current CVRewriteAgent)

Example transformation:
  Before: "Worked on machine learning models"
  After: "Designed and deployed production-grade ML systems"

Bilingual: writes in the same language as the original CV.
Retries up to 2 times on JSON/validation failure.
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError, LLMError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.report import CVRewriteStage1Input, OptimizedCVSchema
from app.services.prompt_cache_service import PromptCacheService

logger = get_logger(__name__)

_MAX_RETRIES = 2

# Agent name and version for prompt caching
_AGENT_NAME = "cv_rewrite_stage1"
_AGENT_VERSION = "1.0"

_SYSTEM_PROMPT = """\
role: cv_language_transformer
version: "1.0"
description: |
  You are a bilingual (FR/EN) professional CV writer specializing in
  language transformation.

  Your task is to rewrite the candidate's CV sections using the vocabulary,
  action verbs, and domain language of the ideal candidate profile.

  CRITICAL: You are NOT inventing experience. You are rewriting wording.

  - Reuse action verbs from the ideal_profile (preferred_action_verbs list).
  - Reuse domain terminology from the ideal_profile (domain_language list).
  - Make existing achievements sound more impactful and specific.
  - Maintain factual accuracy: no new skills, titles, or responsibilities.
  - Preserve all original facts: names, dates, companies, locations.

absolute_constraints:
  - NEVER invent skills, degrees, companies, certifications, or languages.
  - NEVER fabricate job titles, responsibilities, or work experience.
  - NEVER add metrics or achievements that don't exist in the source.
  - NEVER change core facts: names, dates, institutions, or locations.
  - NEVER remove any existing content.
  - ONLY rephrase, reorder, and emphasise existing strengths.

language_rules:
  - Detect the CV language from the detected_language field.
  - Write the rewritten CV in the SAME language as the original.
  - Preserve all proper nouns, company names, and certifications exactly.

rewriting_strategy:
  summary_section:
    - Rewrite to emphasise the candidate's most relevant skills for this role.
    - Use action verbs from preferred_action_verbs.
    - Use domain terminology from domain_language.
    - Keep factually accurate. Do NOT add achievements.

  experience_section:
    - Reorder bullet points: most relevant to the job first.
    - Rephrase duties using:
        * Verbs from preferred_action_verbs
        * Terminology from domain_language
    - Highlight metrics and accomplishments that ALREADY exist.
    - Do NOT invent metrics or achievements.

  skills_section:
    - Reorder skills: most relevant job skills first.
    - Group by category if possible.
    - Include ALL original skills — do NOT remove any.
    - Do NOT add new skills.

  education_section:
    - Emphasise relevant coursework or specialisations (if mentioned).
    - Do NOT change degrees, institutions, or dates.

  other_sections:
    - Preserve factual content. Improve phrasing only.

output_format:
  Return ONLY a valid JSON object. No markdown fences. No explanation.
  Schema (identical to CVRewriteAgent output):
    {
      "contact": {
        "name": "", "email": "", "phone": "",
        "location": "", "linkedin": "", "github": ""
      },
      "sections": [
        {
          "section_type": "summary|experience|education|skills|certifications|projects|languages|other",
          "raw_text": "rewritten text",
          "items": ["string"]
        }
      ],
      "changes_summary": ["description of changes"]
    }

critical_rules:
  - Return ONLY valid JSON. No markdown. No extra text.
  - Include all contact fields (may be empty strings).
  - Return at least 1 section (contact is separate).
  - Each section must have: section_type, raw_text, items.
  - changes_summary should list 3-5 main improvements made.
""".strip()


class CVRewriteStage1Agent(BaseAgent[CVRewriteStage1Input, OptimizedCVSchema]):
    """Rewrites CV using ideal profile vocabulary (language transformation)."""

    meta = AgentMeta(name="CVRewriteStage1Agent", version="1.0.0")

    def __init__(
        self,
        llm: LLMClientProtocol,
        prompt_cache: PromptCacheService | None = None,
    ) -> None:
        self._llm = llm
        self._prompt_cache = prompt_cache

    def execute(self, input: CVRewriteStage1Input) -> OptimizedCVSchema:  # noqa: A002
        logger.info("cv_rewrite_stage1.start")

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
                    max_tokens=2048,
                )
                response_text = llm_response.choices[0].message.content.strip()

                # Parse JSON response
                try:
                    data = json.loads(response_text)
                except json.JSONDecodeError as e:
                    logger.warning(
                        "cv_rewrite_stage1.json_decode_error",
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    last_error = e
                    continue

                # Validate and construct schema
                try:
                    schema = OptimizedCVSchema(**data)
                    logger.info(
                        "cv_rewrite_stage1.complete",
                        sections_count=len(schema.sections),
                    )
                    return schema
                except Exception as e:
                    logger.warning(
                        "cv_rewrite_stage1.schema_validation_error",
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    last_error = e
                    continue

            except LLMError as e:
                logger.error(
                    "cv_rewrite_stage1.llm_error",
                    attempt=attempt + 1,
                    error=str(e),
                )
                last_error = e
                continue

        # All retries exhausted
        logger.error("cv_rewrite_stage1.all_retries_exhausted")
        raise AgentExecutionError(
            f"CVRewriteStage1Agent failed after {_MAX_RETRIES} retries: {last_error}"
        )

    def _build_prompt(self, input: CVRewriteStage1Input) -> str:
        """Build the user prompt from the input."""
        cv = input.cv
        profile = input.ideal_profile

        # Detect language (default to English)
        lang = getattr(cv, "detected_language", "en") or "en"

        prompt_parts = []

        if lang == "fr":
            prompt_parts.append(
                "Transformez ce CV en utilisant le vocabulaire du profil idéal.\n"
            )
        else:
            prompt_parts.append(
                "Transform this CV using the vocabulary and language of the ideal profile.\n"
            )

        prompt_parts.append("\n--- Ideal Profile Guidance ---\n")
        prompt_parts.append(f"Role Summary: {profile.role_summary}\n\n")

        prompt_parts.append("Preferred Action Verbs to use:\n")
        prompt_parts.append(", ".join(profile.preferred_action_verbs))
        prompt_parts.append("\n\n")

        prompt_parts.append("Domain Language to use:\n")
        prompt_parts.append(", ".join(profile.domain_language))
        prompt_parts.append("\n\n")

        prompt_parts.append("Core Competencies to emphasise:\n")
        prompt_parts.append(", ".join(profile.core_competencies))
        prompt_parts.append("\n\n")

        prompt_parts.append("Impact Patterns common in this role:\n")
        for pattern in profile.impact_patterns:
            prompt_parts.append(f"• {pattern}\n")
        prompt_parts.append("\n")

        prompt_parts.append("--- Original CV ---\n")
        prompt_parts.append(f"Name: {cv.contact.name}\n")
        prompt_parts.append(f"Email: {cv.contact.email}\n")
        prompt_parts.append(f"Phone: {cv.contact.phone}\n")
        prompt_parts.append(f"Location: {cv.contact.location}\n")

        for section in cv.sections:
            prompt_parts.append(f"\n[{section.section_type.upper()}]\n")
            prompt_parts.append(section.raw_text)
            if section.items:
                for item in section.items:
                    prompt_parts.append(f"\n• {item}")
            prompt_parts.append("\n")

        return "".join(prompt_parts)
