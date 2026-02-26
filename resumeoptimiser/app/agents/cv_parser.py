"""CVParserAgent – parses raw CV text into a StructuredCVSchema.

Responsibility: Use the LLM to extract structured data from unstructured text.
The LLM is given a strict JSON schema prompt; the response is validated by
Pydantic before returning.

Design:
- LLM injected via LLMClientProtocol (testable, swappable)
- No global state
- execute() is the only public method
- All I/O typed via Pydantic schemas
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError, CVParsingError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.cv import CVParserInput, StructuredCVSchema

logger = get_logger(__name__)

_SYSTEM_PROMPT = """
You are a CV parsing engine. Extract structured data from the provided CV text.

Return ONLY a valid JSON object that matches this schema:
{
  "contact": {
    "name": "string",
    "email": "string",
    "phone": "string",
    "location": "string",
    "linkedin": "string",
    "github": "string"
  },
  "sections": [
    {
      "section_type": "summary|experience|education|skills|certifications|projects|languages|other",
      "raw_text": "string",
      "items": ["string"]
    }
  ],
  "raw_text": "string"
}

Rules:
- Return ONLY the JSON object, no markdown, no extra text.
- If a field is not found, use an empty string.
- section_type must be one of the enum values listed above.
""".strip()


class CVParserAgent(BaseAgent[CVParserInput, StructuredCVSchema]):
    """Parses raw CV text into a validated StructuredCVSchema."""

    meta = AgentMeta(name="CVParserAgent", version="1.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def execute(self, input: CVParserInput) -> StructuredCVSchema:  # noqa: A002
        """Parse the raw CV text and return a structured schema.

        Args:
            input: CVParserInput containing raw CV text.

        Returns:
            StructuredCVSchema with contact info and sections.

        Raises:
            AgentExecutionError: If parsing or validation fails.
        """
        logger.info("cv_parser.start", text_length=len(input.raw_text))

        raw_json = self._call_llm(input.raw_text)
        parsed_dict = self._parse_json(raw_json)
        schema = self._validate_schema(parsed_dict)

        logger.info("cv_parser.success", sections=len(schema.sections))
        return schema

    def _call_llm(self, raw_text: str) -> str:
        """Invoke the LLM with the CV text and return raw JSON string."""
        try:
            return self._llm.complete(system=_SYSTEM_PROMPT, user=raw_text)
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, f"LLM call failed: {exc}") from exc

    def _parse_json(self, raw_json: str) -> dict:
        """Parse the LLM response string into a Python dict."""
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise CVParsingError(f"LLM returned invalid JSON: {exc}") from exc

    def _validate_schema(self, data: dict) -> StructuredCVSchema:
        """Validate the parsed dict against StructuredCVSchema."""
        try:
            return StructuredCVSchema.model_validate(data)
        except Exception as exc:
            raise CVParsingError(f"Schema validation failed: {exc}") from exc
