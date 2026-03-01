"""CVParserAgent – parses raw CV text into a StructuredCVSchema.

Responsibility: Use the LLM to extract structured data from unstructured text.
The LLM is given a strict YAML-formatted prompt for clarity; the response is
JSON validated by Pydantic before returning.

Design:
- LLM injected via LLMClientProtocol (testable, swappable)
- No global state
- execute() is the only public method
- All I/O typed via Pydantic schemas
- Retries up to 2 times on JSON parse / validation failure
- Bilingual: handles French AND English CVs natively
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError, CVParsingError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.cv import CVParserInput, StructuredCVSchema

logger = get_logger(__name__)

_MAX_RETRIES = 2

_SYSTEM_PROMPT = """\
role: cv_parsing_engine
version: "2.0"
description: |
  You are a multilingual CV/résumé parsing engine.
  You MUST handle CVs written in French, English, or a mix of both.
  Your job is to deeply understand the CV content and extract structured data.

language_handling:
  - Auto-detect the CV language (fr or en).
  - ALWAYS preserve original wording for names, titles, and skill labels.
  - Translate NOTHING — keep text in its original language.
  - Recognise French equivalents:
      "Expérience professionnelle" → experience
      "Formation" / "Éducation"    → education
      "Compétences"                → skills
      "Profil" / "Résumé"         → summary
      "Certifications"             → certifications
      "Projets"                    → projects
      "Langues"                    → languages

extraction_rules:
  contact:
    - Extract name, email, phone, location, linkedin, github.
    - If not found, use empty string "".

  sections:
    - Map every CV section to one of these section_type values:
        summary, experience, education, skills, certifications, projects, languages, other
    - raw_text: a concise summary of the section (max 500 chars).
    - items: list of individual line items (job titles, skills, degrees, etc.)

  hard_skills:
    - Programming languages, frameworks, databases, cloud platforms, etc.
    - Example: ["Python", "SQL", "Azure", "Power BI", "SAP"]

  soft_skills:
    - Communication, leadership, teamwork, problem-solving, etc.
    - Example: ["Analytical thinking", "Stakeholder management"]

  tools:
    - Specific software, platforms, IDEs, or systems.
    - Example: ["JIRA", "Confluence", "Excel", "Visio"]

  languages_spoken:
    - Format: "Language (level)" — e.g. ["Français (natif)", "English (fluent)"]

  total_years_experience:
    - Calculate from work history dates. Estimate if unclear. Use 0 if none.

  education_level:
    - Highest attained: "phd", "master", "bachelor", "diploma", "certificate", ""
    - Map French: "Maîtrise"→master, "Baccalauréat"→bachelor, "DEC"→diploma, "DEP"→certificate

  certifications:
    - List all certifications and professional designations.

output_format:
  Return ONLY a valid JSON object. No markdown fences. No explanation.
  Schema:
    {
      "detected_language": "fr|en",
      "contact": {
        "name": "", "email": "", "phone": "",
        "location": "", "linkedin": "", "github": ""
      },
      "sections": [
        {"section_type": "...", "raw_text": "...", "items": ["..."]}
      ],
      "hard_skills": ["..."],
      "soft_skills": ["..."],
      "tools": ["..."],
      "languages_spoken": ["..."],
      "total_years_experience": 0.0,
      "education_level": "",
      "certifications": ["..."],
      "raw_text": ""
    }

critical_rules:
  - Return ONLY the JSON. No extra text. No markdown.
  - Keep raw_text per section SHORT (max 500 chars) — summarise if needed.
  - Top-level raw_text must be "".
  - JSON must be complete and valid. Do NOT let it get cut off.
  - When in doubt about section_type, use "other".
""".strip()


class CVParserAgent(BaseAgent[CVParserInput, StructuredCVSchema]):
    """Parses raw CV text into a validated StructuredCVSchema."""

    meta = AgentMeta(name="CVParserAgent", version="2.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def execute(self, input: CVParserInput) -> StructuredCVSchema:  # noqa: A002
        """Parse the raw CV text and return a structured schema.

        Retries up to _MAX_RETRIES times if the LLM returns invalid JSON.
        """
        logger.info("cv_parser.start", text_length=len(input.raw_text))

        last_error: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            raw_json = self._call_llm(input.raw_text)
            try:
                parsed_dict = self._parse_json(raw_json)
                schema = self._validate_schema(parsed_dict)
                logger.info("cv_parser.success", sections=len(schema.sections),
                            skills=len(schema.hard_skills), lang=schema.detected_language,
                            attempt=attempt)
                return schema
            except (CVParsingError, AgentExecutionError) as exc:
                last_error = exc
                logger.warning("cv_parser.retry", attempt=attempt, error=str(exc))

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
            raise CVParsingError(f"LLM returned invalid JSON: {exc}") from exc

    def _validate_schema(self, data: dict) -> StructuredCVSchema:
        try:
            return StructuredCVSchema.model_validate(data)
        except Exception as exc:
            raise CVParsingError(f"Schema validation failed: {exc}") from exc
