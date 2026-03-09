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
You are a CV parsing engine. Extract structured metadata from the CV text.
Return ONLY valid JSON matching the schema below. No markdown fences. No explanation.

RULES:
- detected_language: "fr" or "en"
- contact: extract name, email, phone, location, linkedin, github (empty string if missing)
- sections: one entry per CV section
    section_type: summary | experience | education | skills | certifications | projects | languages | other
    raw_text: verbatim section content, max 800 chars (truncate if longer)
    items: key entries only — for experience: "Role | Company | Dates", for education: "Degree | Institution | Dates", for skills: individual skill names, for languages: "Language (level)"
- hard_skills: every technical skill, language, framework, tool mentioned anywhere in the CV
- soft_skills: interpersonal/behavioural skills
- tools: specific platforms, software, IDEs
- languages_spoken: ["Language (level)"]
- total_years_experience: float, calculated from dates (0 if none)
- education_level: phd | master | bachelor | diploma | certificate | "" (highest only)
- certifications: list of certifications
- raw_text: must be ""

JSON schema:
{"detected_language":"","contact":{"name":"","email":"","phone":"","location":"","linkedin":"","github":""},"sections":[{"section_type":"","raw_text":"","items":[]}],"hard_skills":[],"soft_skills":[],"tools":[],"languages_spoken":[],"total_years_experience":0.0,"education_level":"","certifications":[],"raw_text":""}
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
