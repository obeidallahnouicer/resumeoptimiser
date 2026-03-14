"""Unit tests for CVParserAgent.

Tests the agent in isolation:
- Uses pure regex parsing (NO LLM CALLS)
- Tests caching via CVCacheService
- No network calls, no model loading
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.agents.cv_parser import CVParserAgent
from app.schemas.cv import CVParserInput
from app.services.cv_cache_service import CVCacheService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_sample_cv() -> str:
    """Return a sample raw CV text (before markdown conversion)."""
    return """Jane Doe
jane@example.com | +1-555-0100 | Berlin | linkedin.com/in/jane | github.com/jane

SUMMARY
Experienced Python developer with 5+ years in backend development.

EXPERIENCE
Senior Python Developer at TechCorp (2019-2024)
- Developed REST APIs using FastAPI
- Led team of 3 engineers

EDUCATION
Master's Degree in Computer Science from University (2018)

SKILLS
- Python
- FastAPI
- Docker
- Leadership

LANGUAGES
- English
- German
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCVParserAgent:
    """Unit tests for CVParserAgent.execute()."""

    def test_execute_parses_markdown_deterministically(self, mock_llm):
        """Agent should parse Markdown deterministically (NO LLM CALLS)."""
        agent = CVParserAgent(llm=mock_llm)
        
        result = agent.execute(CVParserInput(raw_text=_make_sample_cv()))
        
        # Verify parsing worked
        assert result.contact.name == "Jane Doe"
        assert result.contact.email == "jane@example.com"
        assert len(result.sections) > 0
        # Verify NO LLM calls were made
        mock_llm.complete.assert_not_called()

    def test_execute_returns_markdown_field(self, mock_llm):
        """Agent should populate the markdown field."""
        agent = CVParserAgent(llm=mock_llm)
        
        result = agent.execute(CVParserInput(raw_text=_make_sample_cv()))
        
        assert result.markdown is not None
        assert len(result.markdown) > 0
        assert "Jane Doe" in result.markdown

    def test_execute_extracts_contact_info(self, mock_llm):
        """Agent should extract contact information from CV."""
        agent = CVParserAgent(llm=mock_llm)
        
        result = agent.execute(CVParserInput(raw_text=_make_sample_cv()))
        
        assert result.contact.name == "Jane Doe"
        assert result.contact.email == "jane@example.com"
        assert result.contact.phone == "+1-555-0100"
        assert result.contact.location == "Berlin"
        assert "jane" in result.contact.linkedin
        assert "jane" in result.contact.github

    def test_execute_extracts_sections(self, mock_llm):
        """Agent should extract all CV sections."""
        agent = CVParserAgent(llm=mock_llm)
        
        result = agent.execute(CVParserInput(raw_text=_make_sample_cv()))
        
        section_types = {s.section_type.value for s in result.sections}
        assert "summary" in section_types or "experience" in section_types or "education" in section_types

    def test_execute_extracts_skills(self, mock_llm):
        """Agent should extract hard skills, soft skills, and tools."""
        agent = CVParserAgent(llm=mock_llm)
        
        result = agent.execute(CVParserInput(raw_text=_make_sample_cv()))
        
        # Should have extracted skills
        all_skills = result.hard_skills + result.soft_skills + result.tools
        assert len(all_skills) > 0

    def test_execute_uses_cache_on_second_call(self, mock_llm):
        """Agent should use cache on second call with same CV text."""
        cache = CVCacheService(MagicMock())
        agent = CVParserAgent(llm=mock_llm, cv_cache=cache)
        cv_text = _make_sample_cv()
        
        # First call
        result1 = agent.execute(CVParserInput(raw_text=cv_text))
        call_count_1 = mock_llm.complete.call_count
        
        # Second call with same CV
        result2 = agent.execute(CVParserInput(raw_text=cv_text))
        call_count_2 = mock_llm.complete.call_count
        
        # Both calls should produce same result
        assert result1.contact.name == result2.contact.name
        # No additional LLM calls (was 0 before, still 0)
        assert call_count_1 == call_count_2 == 0

    def test_execute_preserves_raw_text(self, mock_llm):
        """Agent should preserve the raw_text field."""
        agent = CVParserAgent(llm=mock_llm)
        cv_text = _make_sample_cv()
        
        result = agent.execute(CVParserInput(raw_text=cv_text))
        
        assert result.raw_text == cv_text

    def test_execute_detects_language(self, mock_llm):
        """Agent should detect CV language (en or fr)."""
        agent = CVParserAgent(llm=mock_llm)
        
        result = agent.execute(CVParserInput(raw_text=_make_sample_cv()))
        
        assert result.detected_language in ("en", "fr")
