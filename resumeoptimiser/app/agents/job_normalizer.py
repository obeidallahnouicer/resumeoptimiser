"""JobNormalizerAgent – normalises raw job description text.

Same structural pattern as CVParserAgent:
LLM call → JSON parse → Pydantic validation.
"""

from __future__ import annotations

import json

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError, JobNormalizationError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.job import JobNormalizerInput, StructuredJobSchema

logger = get_logger(__name__)

_SYSTEM_PROMPT = """
You are a job description normalisation engine.

Return ONLY a valid JSON object matching this schema:
{
  "title": "string",
  "company": "string",
  "employment_type": "full_time|part_time|contract|freelance|internship|unknown",
  "required_skills": [{"skill": "string", "required": true}],
  "responsibilities": ["string"],
  "qualifications": ["string"],
  "raw_text": "string"
}

Rules:
- Return ONLY the JSON, no markdown.
- employment_type must be one of the listed enum values.
- required_skills should list technical and soft skills separately.
""".strip()


class JobNormalizerAgent(BaseAgent[JobNormalizerInput, StructuredJobSchema]):
    """Normalises a raw job description into a StructuredJobSchema."""

    meta = AgentMeta(name="JobNormalizerAgent", version="1.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def execute(self, input: JobNormalizerInput) -> StructuredJobSchema:  # noqa: A002
        """Normalise raw job description text.

        Raises:
            AgentExecutionError: On LLM failure or schema validation error.
        """
        logger.info("job_normalizer.start", text_length=len(input.raw_text))

        raw_json = self._call_llm(input.raw_text)
        parsed_dict = self._parse_json(raw_json)
        schema = self._validate_schema(parsed_dict)

        logger.info("job_normalizer.success", title=schema.title)
        return schema

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
