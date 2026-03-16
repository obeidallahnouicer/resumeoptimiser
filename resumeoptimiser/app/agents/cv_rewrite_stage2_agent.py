"""CVRewriteStage2Agent – gap closing using comparison report.

Purpose:
  Address mismatches found in the comparison report. Uses information
  already present in the CV to reframe, emphasise, or highlight transferable skills.

Allowed actions:
  - Reframe bullet points
  - Emphasise relevant experience
  - Highlight transferable skills
  - Reorganise sections for better relevance

Forbidden actions:
  - Inventing tools or technologies
  - Inventing responsibilities or job titles
  - Fabricating metrics or achievements

Input:
  - OptimizedCVSchema from Stage 1 (already partially rewritten)
  - ExplanationReportSchema (gaps found in comparison)

Output:
  - OptimizedCVSchema (final optimized version)

The comparison report contains:
  - mismatches: specific gaps between CV and job
  - summary: overall gap assessment

Example:
  If comparison report shows "missing Docker" but CV doesn't mention Docker,
  Stage 2 cannot invent Docker experience. But it can emphasise related
  infrastructure or DevOps experience if present.

Bilingual: writes in the detected language of the CV.
Retries up to 2 times on JSON/validation failure.
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError, LLMError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.report import CVRewriteStage2Input, OptimizedCVSchema
from app.services.prompt_cache_service import PromptCacheService

logger = get_logger(__name__)

_MAX_RETRIES = 2

# Agent name and version for prompt caching
_AGENT_NAME = "cv_rewrite_stage2"
_AGENT_VERSION = "1.0"

_SYSTEM_PROMPT = """\
role: cv_gap_closer
version: "1.0"
description: |
  You are a bilingual (FR/EN) professional CV writer specializing in
  addressing gaps identified in a comparison analysis.

  Your task is to refine a partially-rewritten CV (from Stage 1) to address
  specific gaps identified between the candidate and the job.

  CRITICAL: You can only use information ALREADY PRESENT in the CV.
  You cannot invent experience, skills, or metrics.

  Your allowed actions are:
    1. Reframe bullet points to highlight relevance to missing areas
    2. Reorganise sections for better job alignment
    3. Emphasise transferable skills that address gaps
    4. Use clearer language to expose hidden relevant experience

absolute_constraints:
  - NEVER invent skills, degrees, companies, certifications, or languages.
  - NEVER fabricate job titles, responsibilities, or work experience.
  - NEVER add metrics or achievements that don't exist.
  - NEVER change core facts: names, dates, institutions, or locations.
  - NEVER remove any existing content.
  - If a gap cannot be addressed with existing content, leave it as-is.

language_rules:
  - Detect the CV language from the detected_language field.
  - Write the rewritten CV in the SAME language as the original.
  - Preserve all proper nouns, company names, and certifications exactly.

gap_addressing_strategy:
  For each gap in the comparison report:
    1. Check if the CV has relevant content that addresses this gap
    2. If YES: reframe or emphasise that content to highlight the connection
    3. If NO: do not invent content; move to the next gap

  Examples of valid reframing:
    Gap: "Missing Docker"
    CV has: "Built containerized applications"
    Action: Rewrite as "Built containerized applications using Docker" IF
            the original explicitly mentions Docker. Otherwise, just emphasise
            "containerization" experience as transferable.

  Examples of invalid actions:
    Gap: "Missing 5 years AWS experience"
    CV has: "2 years with cloud platforms"
    INVALID: Do NOT write "5 years AWS" – that's fabrication.
    VALID: Emphasise the 2 years and highlight cloud platform breadth.

output_format:
  Return ONLY a valid JSON object. No markdown fences. No explanation.
  Schema (identical to Stage 1 output):
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
  - changes_summary should list 3-5 gap-closing improvements made.
  - Limit total changes_summary to 5 items max.
""".strip()


class CVRewriteStage2Agent(BaseAgent[CVRewriteStage2Input, OptimizedCVSchema]):
    """Refines rewritten CV by addressing gaps from comparison report."""

    meta = AgentMeta(name="CVRewriteStage2Agent", version="1.0.0")

    def __init__(
        self,
        llm: LLMClientProtocol,
        prompt_cache: PromptCacheService | None = None,
    ) -> None:
        self._llm = llm
        self._prompt_cache = prompt_cache

    def execute(self, input: CVRewriteStage2Input) -> OptimizedCVSchema:  # noqa: A002
        logger.info("cv_rewrite_stage2.start", mismatches_count=len(input.comparison_report.mismatches))

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
                        "cv_rewrite_stage2.json_decode_error",
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    last_error = e
                    continue

                # Validate and construct schema
                try:
                    schema = OptimizedCVSchema(**data)
                    logger.info(
                        "cv_rewrite_stage2.complete",
                        sections_count=len(schema.sections),
                    )
                    return schema
                except Exception as e:
                    logger.warning(
                        "cv_rewrite_stage2.schema_validation_error",
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    last_error = e
                    continue

            except LLMError as e:
                logger.error(
                    "cv_rewrite_stage2.llm_error",
                    attempt=attempt + 1,
                    error=str(e),
                )
                last_error = e
                continue

        # All retries exhausted
        logger.error("cv_rewrite_stage2.all_retries_exhausted")
        raise AgentExecutionError(
            f"CVRewriteStage2Agent failed after {_MAX_RETRIES} retries: {last_error}"
        )

    def _build_prompt(self, input: CVRewriteStage2Input) -> str:
        """Build the user prompt from the input."""
        cv_rewrite = input.cv_rewrite_stage1
        gaps = input.comparison_report

        # Detect language (default to English)
        lang = getattr(cv_rewrite, "detected_language", "en") or "en"

        prompt_parts = []

        if lang == "fr":
            prompt_parts.append(
                "Affinez ce CV en abordant les écarts identifiés.\n"
            )
        else:
            prompt_parts.append(
                "Refine this CV by addressing the identified gaps.\n"
            )

        prompt_parts.append("\n--- Identified Gaps ---\n")
        prompt_parts.append(f"Summary: {gaps.summary}\n\n")

        if gaps.mismatches:
            prompt_parts.append("Specific mismatches to address:\n")
            for i, mismatch in enumerate(gaps.mismatches, 1):
                prompt_parts.append(f"\n{i}. {mismatch.field}\n")
                prompt_parts.append(f"   CV has: {mismatch.cv_value}\n")
                prompt_parts.append(f"   Job expects: {mismatch.job_expectation}\n")
                prompt_parts.append(f"   Suggestion: {mismatch.explanation}\n")
            prompt_parts.append("\n")

        prompt_parts.append("--- Stage 1 (Language-Transformed) CV ---\n")
        prompt_parts.append(f"Name: {cv_rewrite.contact.name}\n")
        prompt_parts.append(f"Email: {cv_rewrite.contact.email}\n")
        prompt_parts.append(f"Phone: {cv_rewrite.contact.phone}\n")
        prompt_parts.append(f"Location: {cv_rewrite.contact.location}\n")

        for section in cv_rewrite.sections:
            prompt_parts.append(f"\n[{section.section_type.upper()}]\n")
            prompt_parts.append(section.raw_text)
            if section.items:
                for item in section.items:
                    prompt_parts.append(f"\n• {item}")
            prompt_parts.append("\n")

        if lang == "fr":
            prompt_parts.append(
                "\nConsignes: Adressez les écarts en réorganisant et en "
                "réencadrant le contenu EXISTANT uniquement. "
                "Ne pas inventer d'expérience, de compétences ou de métriques.\n"
            )
        else:
            prompt_parts.append(
                "\nInstructions: Address the gaps by reorganising and reframing "
                "EXISTING content only. Do not invent experience, skills, or metrics.\n"
            )

        return "".join(prompt_parts)
