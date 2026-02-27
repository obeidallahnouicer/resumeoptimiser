"""Unit tests for CVParserAgent.

Tests the agent in isolation:
- LLM is mocked via the mock_llm fixture
- No network calls, no model loading
- All agent behaviour is driven by injected dependencies
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from app.agents.cv_parser import CVParserAgent
from app.core.exceptions import AgentExecutionError, CVParsingError
from app.schemas.cv import CVParserInput


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_valid_cv_json(name: str = "Jane Doe", email: str = "jane@example.com") -> str:
    """Return a valid JSON string matching StructuredCVSchema."""
    return json.dumps(
        {
            "contact": {
                "name": name,
                "email": email,
                "phone": "+1-555-0100",
                "location": "Berlin",
                "linkedin": "",
                "github": "",
            },
            "sections": [
                {
                    "section_type": "experience",
                    "raw_text": "5 years Python development.",
                    "items": ["Python"],
                }
            ],
            "raw_text": "Jane Doe – Senior Python Developer…",
        }
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCVParserAgent:
    """Unit tests for CVParserAgent.execute()."""

    def test_execute_returns_structured_cv_on_valid_response(self, mock_llm):
        """Agent should return StructuredCVSchema when LLM returns valid JSON."""
        mock_llm.complete.return_value = _make_valid_cv_json()
        agent = CVParserAgent(llm=mock_llm)

        result = agent.execute(CVParserInput(raw_text="Jane Doe\nSenior Python Developer"))

        assert result.contact.name == "Jane Doe"
        assert result.contact.email == "jane@example.com"
        assert len(result.sections) == 1
        assert result.sections[0].section_type.value == "experience"

    def test_execute_calls_llm_with_raw_text(self, mock_llm):
        """Agent must pass the raw text to the LLM as the user message."""
        mock_llm.complete.return_value = _make_valid_cv_json()
        agent = CVParserAgent(llm=mock_llm)
        raw_text = "Unique CV content for assertion."

        agent.execute(CVParserInput(raw_text=raw_text))

        call_args = mock_llm.complete.call_args
        assert call_args.kwargs["user"] == raw_text or call_args.args[1] == raw_text

    def test_execute_raises_cv_parsing_error_on_invalid_json(self, mock_llm):
        """Agent should raise CVParsingError when LLM returns malformed JSON."""
        mock_llm.complete.return_value = "This is not JSON at all."
        agent = CVParserAgent(llm=mock_llm)

        with pytest.raises(CVParsingError):
            agent.execute(CVParserInput(raw_text="Some CV text here."))

    def test_execute_raises_cv_parsing_error_on_schema_mismatch(self, mock_llm):
        """Agent should raise CVParsingError when JSON doesn't match schema."""
        mock_llm.complete.return_value = json.dumps({"unexpected_key": "value"})
        agent = CVParserAgent(llm=mock_llm)

        with pytest.raises(CVParsingError):
            agent.execute(CVParserInput(raw_text="Some CV text here."))

    def test_execute_raises_agent_execution_error_on_llm_failure(self, mock_llm):
        """Agent should wrap LLM exceptions in AgentExecutionError."""
        mock_llm.complete.side_effect = RuntimeError("Connection timeout")
        agent = CVParserAgent(llm=mock_llm)

        with pytest.raises(AgentExecutionError) as exc_info:
            agent.execute(CVParserInput(raw_text="Some CV text here."))

        assert "CVParserAgent" in exc_info.value.agent

    def test_execute_preserves_all_contact_fields(self, mock_llm):
        """All optional contact fields should be present in the output."""
        payload = json.dumps(
            {
                "contact": {
                    "name": "Bob",
                    "email": "bob@test.com",
                    "phone": "+44 7000 000000",
                    "location": "London",
                    "linkedin": "linkedin.com/in/bob",
                    "github": "github.com/bob",
                },
                "sections": [],
                "raw_text": "",
            }
        )
        mock_llm.complete.return_value = payload
        agent = CVParserAgent(llm=mock_llm)

        result = agent.execute(CVParserInput(raw_text="Bob Smith's full CV document"))

        assert result.contact.linkedin == "linkedin.com/in/bob"
        assert result.contact.github == "github.com/bob"

    def test_llm_is_called_exactly_once_per_execute(self, mock_llm):
        """LLM should be called exactly once per execute() invocation."""
        mock_llm.complete.return_value = _make_valid_cv_json()
        agent = CVParserAgent(llm=mock_llm)

        agent.execute(CVParserInput(raw_text="CV text content here"))

        assert mock_llm.complete.call_count == 1
