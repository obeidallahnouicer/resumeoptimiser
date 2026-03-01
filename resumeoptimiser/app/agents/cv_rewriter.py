"""CVRewriteAgent – rewrites CV sections to better match the job.

Constraint: LLM may only rewrite language. It must not invent experience.
The agent passes the explanation report to give the LLM specific targets.
Retries up to 2 times on JSON/validation failure.
Bilingual: writes in the same language as the original CV.
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.report import CVRewriteInput, OptimizedCVSchema

logger = get_logger(__name__)

_MAX_RETRIES = 2

_SYSTEM_PROMPT = """\
role: professional_cv_rewriter
version: "2.0"
description: |
  You are a bilingual (FR/EN) professional CV writer.
  Rewrite the candidate's CV sections to maximise alignment with the target
  job description, WITHOUT inventing experience, skills, or qualifications.

language_rules:
  - Detect the CV language from the detected_language field.
  - Write the rewritten CV in the SAME language as the original.
  - If the job is in a different language, still keep the CV in its original language.
  - Preserve all proper nouns, company names, and certifications exactly.

rewriting_strategy:
  summary_section:
    - Rewrite to mirror the job title and key requirements.
    - Emphasise the candidate's most relevant skills for this specific role.
    - Use strong action verbs and quantified achievements if data exists.

  experience_section:
    - Reorder bullet points: most relevant to the job first.
    - Rephrase duties using keywords from the job description.
    - Highlight metrics and accomplishments (%, $, numbers).
    - Do NOT invent new job titles, companies, or responsibilities.

  skills_section:
    - Reorder skills: required job skills first, then additional ones.
    - Group by category if possible (hard skills, tools, soft skills).
    - Include ALL original skills — do not remove any.

  education_section:
    - Emphasise relevant coursework or specialisations.
    - Do NOT change degrees, institutions, or dates.

  other_sections:
    - Preserve factual content. Improve phrasing only.

  gap_targeting:
    - Use the provided gap analysis to know WHERE to focus rewrites.
    - If a gap is "missing keyword X", work X into existing content naturally.
    - If a gap is about experience years, emphasise longevity and depth of existing roles.

output_format:
  Return ONLY a valid JSON object. No markdown fences. No explanation.
  Schema:
    {
      "contact": {
        "name": "", "email": "", "phone": "",
        "location": "", "linkedin": "", "github": ""
      },
      "sections": [
        {
          "section_type": "summary|experience|education|skills|certifications|projects|languages|other",
          "raw_text": "rewritten text (max 500 chars per section)",
          "items": ["string"]
        }
      ],
      "changes_summary": ["brief description of each change made"]
    }

critical_rules:
  - NEVER invent skills, degrees, companies, or experience.
  - ONLY rephrase, reorder, and emphasise existing content.
  - Keep raw_text per section SHORT (max 500 chars) to avoid truncation.
  - Return ONLY the JSON. No markdown. No extra text.
  - JSON must be complete and valid. Do NOT let it get cut off.
  - Keep contact info EXACTLY as provided.
  - changes_summary should list 3-8 specific changes you made.
""".strip()


class CVRewriteAgent(BaseAgent[CVRewriteInput, OptimizedCVSchema]):
    """Rewrites CV text to better match the target job (LLM-powered)."""

    meta = AgentMeta(name="CVRewriteAgent", version="2.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def execute(self, input: CVRewriteInput) -> OptimizedCVSchema:  # noqa: A002
        logger.info("cv_rewrite.start", job=input.job.title)

        user_prompt = self._build_prompt(input)

        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            raw_json = self._call_llm(user_prompt)
            try:
                schema = self._parse_and_validate(raw_json)
                logger.info("cv_rewrite.success", changes=len(schema.changes_summary), attempt=attempt)
                return schema
            except AgentExecutionError as exc:
                last_error = exc
                logger.warning("cv_rewrite.retry", attempt=attempt, error=str(exc))

        raise last_error  # type: ignore[misc]

    def _build_prompt(self, input: CVRewriteInput) -> str:  # noqa: A002
        """Construct a rich user message with all available context."""
        cv = input.cv
        job = input.job

        gaps = "\n".join(
            f"- [{m.field}] {m.explanation}" for m in input.explanation.mismatches
        )
        sections = "\n".join(
            f"[{s.section_type.value}]\n{s.raw_text[:400]}" for s in cv.sections
        )
        contact = cv.contact

        lines = [
            "=== JOB ===",
            f"Title: {job.title}",
            f"Hard skills: {', '.join(job.hard_skills)}",
            f"Soft skills: {', '.join(job.soft_skills)}",
            f"Tools: {', '.join(job.tools)}",
            f"Required skills: {', '.join(s.skill for s in job.required_skills)}",
            f"Methodologies: {', '.join(job.methodologies)}",
            "",
            "=== GAP ANALYSIS ===",
            gaps,
            "",
            "=== CANDIDATE (keep contact as-is) ===",
            f"Name: {contact.name}, Email: {contact.email}",
            f"Phone: {contact.phone}, Location: {contact.location}",
            f"LinkedIn: {contact.linkedin}, GitHub: {contact.github}",
            f"Detected language: {cv.detected_language}",
            f"Hard skills: {', '.join(cv.hard_skills)}",
            f"Soft skills: {', '.join(cv.soft_skills)}",
            f"Tools: {', '.join(cv.tools)}",
            "",
            "=== CURRENT CV SECTIONS ===",
            sections,
        ]
        return "\n".join(lines)

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
