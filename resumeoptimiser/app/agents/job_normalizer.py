"""JobNormalizerAgent – normalises raw job description text.

Same structural pattern as CVParserAgent:
LLM call → JSON parse → Pydantic validation.
Retries up to 2 times on JSON/validation failure.
Bilingual: handles French AND English job postings natively.
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError, JobNormalizationError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.job import JobNormalizerInput, StructuredJobSchema

logger = get_logger(__name__)

_MAX_RETRIES = 2

_SYSTEM_PROMPT = """\
role: job_description_normalisation_engine
version: "2.0"
description: |
  You are a multilingual job description analysis engine.
  You MUST handle job postings in French, English, or both.
  Your goal is DEEP understanding: extract every detail the recruiter asks for.

language_handling:
  - Auto-detect the language of the posting (fr or en).
  - PRESERVE original wording for job titles, company names, skill labels.
  - Translate NOTHING — keep text in its original language.
  - Recognise French equivalents:
      "Poste" / "Titre"               → title
      "Entreprise" / "Société"         → company
      "Compétences requises"           → required_skills
      "Responsabilités" / "Missions"   → responsibilities
      "Qualifications" / "Profil recherché" → qualifications
      "CDI"→full_time, "CDD"→contract, "Stage"→internship, "Freelance"→freelance
      "Temps partiel"→part_time

extraction_rules:
  title:
    - The job title exactly as stated.

  company:
    - Company or organisation name. Empty string if not found.

  employment_type:
    - One of: full_time, part_time, contract, freelance, internship, unknown
    - Map French contract types as shown above.

  required_skills:
    - Each object: {"skill": "Python", "required": true/false}
    - "required" = true if the posting says mandatory / requis / indispensable
    - "required" = false if the posting says nice-to-have / atout / apprécié

  responsibilities:
    - List of key duties / missions described in the posting.

  qualifications:
    - Degrees, years of experience, certifications mentioned.

  hard_skills:
    - Programming languages, frameworks, databases, cloud, methodologies.
    - Example: ["Python", "AWS", "Docker", "CI/CD"]

  soft_skills:
    - Interpersonal and organisational skills requested.
    - Example: ["Communication", "Esprit d'équipe", "Autonomie"]

  tools:
    - Specific software, platforms, systems mentioned.
    - Example: ["JIRA", "SAP", "Salesforce"]

  languages_required:
    - Format: "Language (level)" — e.g. ["Français (courant)", "English (fluent)"]

  min_years_experience:
    - Minimum years of experience required. Use 0 if not specified.

  education_level:
    - Minimum education: "phd", "master", "bachelor", "diploma", "certificate", ""
    - Map French: "Bac+5"→master, "Bac+3"→bachelor, "Bac+2"→diploma

  certifications_preferred:
    - List of certifications mentioned (PMP, AWS Certified, etc.)

  methodologies:
    - Agile, Scrum, Kanban, Waterfall, SAFe, DevOps, etc.

  domain:
    - Business domain / industry: "finance", "healthcare", "tech", "consulting", etc.

output_format:
  Return ONLY a valid JSON object. No markdown fences. No explanation.
  Schema:
    {
      "detected_language": "fr|en",
      "title": "",
      "company": "",
      "employment_type": "full_time|part_time|contract|freelance|internship|unknown",
      "required_skills": [{"skill": "...", "required": true}],
      "responsibilities": ["..."],
      "qualifications": ["..."],
      "hard_skills": ["..."],
      "soft_skills": ["..."],
      "tools": ["..."],
      "languages_required": ["..."],
      "min_years_experience": 0.0,
      "education_level": "",
      "certifications_preferred": ["..."],
      "methodologies": ["..."],
      "domain": "",
      "raw_text": ""
    }

critical_rules:
  - Return ONLY the JSON. No extra text. No markdown.
  - raw_text must be "".
  - JSON must be complete and valid. Do NOT let it get cut off.
  - When unsure about employment_type, use "unknown".
  - Be thorough: extract ALL skills, tools, and requirements mentioned.
""".strip()


class JobNormalizerAgent(BaseAgent[JobNormalizerInput, StructuredJobSchema]):
    """Normalises a raw job description into a StructuredJobSchema."""

    meta = AgentMeta(name="JobNormalizerAgent", version="2.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def execute(self, input: JobNormalizerInput) -> StructuredJobSchema:  # noqa: A002
        """Normalise raw job description text.

        Retries up to _MAX_RETRIES times if the LLM returns invalid JSON.
        """
        logger.info("job_normalizer.start", text_length=len(input.raw_text))

        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            raw_json = self._call_llm(input.raw_text)
            try:
                parsed_dict = self._parse_json(raw_json)
                schema = self._validate_schema(parsed_dict)
                logger.info("job_normalizer.success", title=schema.title,
                            skills=len(schema.hard_skills), lang=schema.detected_language,
                            attempt=attempt)
                return schema
            except (JobNormalizationError, AgentExecutionError) as exc:
                last_error = exc
                logger.warning("job_normalizer.retry", attempt=attempt, error=str(exc))

        raise last_error  # type: ignore[misc]

    def _call_llm(self, raw_text: str) -> str:
        try:
            return self._llm.complete(system=_SYSTEM_PROMPT, user=raw_text)
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, f"LLM call failed: {exc}") from exc

    def _parse_json(self, raw_json: str) -> dict:
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise JobNormalizationError(f"LLM returned invalid JSON: {exc}") from exc

    def _validate_schema(self, data: dict) -> StructuredJobSchema:
        try:
            return StructuredJobSchema.model_validate(data)
        except Exception as exc:
            raise JobNormalizationError(f"Schema validation failed: {exc}") from exc
