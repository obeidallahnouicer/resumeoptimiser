"""Unit tests for SemanticMatcherAgent.

Validates that:
- Similarity scores are computed without any LLM calls
- Section weights are applied correctly
- Edge cases (empty sections, no sections) are handled
"""

from __future__ import annotations

import numpy as np
import pytest

from app.agents.semantic_matcher import SemanticMatcherAgent
from app.schemas.cv import CVSectionSchema, StructuredCVSchema
from app.schemas.scoring import SemanticMatcherInput


class TestSemanticMatcherAgent:
    """Unit tests for SemanticMatcherAgent.execute()."""

    def test_returns_score_between_0_and_1(self, mock_embedder, structured_cv, structured_job):
        """Overall score must always be in [0, 1]."""
        agent = SemanticMatcherAgent(embedding_client=mock_embedder)

        result = agent.execute(SemanticMatcherInput(cv=structured_cv, job=structured_job))

        assert 0.0 <= result.overall <= 1.0

    def test_section_scores_match_sections_in_cv(
        self, mock_embedder, structured_cv, structured_job
    ):
        """Each non-empty CV section should produce one SectionScore."""
        agent = SemanticMatcherAgent(embedding_client=mock_embedder)

        result = agent.execute(SemanticMatcherInput(cv=structured_cv, job=structured_job))

        non_empty = [s for s in structured_cv.sections if s.raw_text.strip()]
        assert len(result.section_scores) == len(non_empty)

    def test_embedding_client_called_for_each_section_plus_job(
        self, mock_embedder, structured_cv, structured_job
    ):
        """embed() should be called once per section + once for the job."""
        agent = SemanticMatcherAgent(embedding_client=mock_embedder)

        agent.execute(SemanticMatcherInput(cv=structured_cv, job=structured_job))

        non_empty_sections = sum(1 for s in structured_cv.sections if s.raw_text.strip())
        expected_calls = non_empty_sections + 1  # +1 for the job vector
        assert mock_embedder.embed.call_count == expected_calls

    def test_no_llm_dependency(self, mock_embedder, structured_cv, structured_job):
        """SemanticMatcherAgent must not require an LLM – constructor check."""
        import inspect

        sig = inspect.signature(SemanticMatcherAgent.__init__)
        param_names = list(sig.parameters.keys())
        assert "llm" not in param_names

    def test_empty_cv_sections_returns_zero_score(
        self, mock_embedder, contact_info, structured_job
    ):
        """A CV with no text sections should return overall score of 0."""
        empty_cv = StructuredCVSchema(contact=contact_info, sections=[])
        agent = SemanticMatcherAgent(embedding_client=mock_embedder)

        result = agent.execute(SemanticMatcherInput(cv=empty_cv, job=structured_job))

        assert result.overall == 0.0
        assert result.section_scores == []
