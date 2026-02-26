"""Unit test template for CVValidatorAgent.

Validates pure business-rule logic with no external dependencies.
"""

from __future__ import annotations

import pytest

from app.agents.cv_validator import CVValidatorAgent, CVValidatorInput
from app.schemas.cv import ContactInfoSchema, CVSectionSchema, StructuredCVSchema
from app.schemas.report import OptimizedCVSchema


def _make_optimized_cv(
    email: str = "jane@example.com",
    sections: list | None = None,
) -> OptimizedCVSchema:
    if sections is None:
        sections = [
            CVSectionSchema(
                section_type="experience",
                raw_text="5 years Python development on distributed systems.",
                items=["Python"],
            ),
            CVSectionSchema(
                section_type="skills",
                raw_text="Python FastAPI PostgreSQL Docker",
                items=["Python", "FastAPI"],
            ),
        ]
    return OptimizedCVSchema(
        contact=ContactInfoSchema(name="Jane", email=email),
        sections=sections,
        changes_summary=["Rephrased experience section."],
    )


class TestCVValidatorAgent:
    """Unit tests for CVValidatorAgent.execute()."""

    def test_valid_cv_passes_all_rules(self, structured_cv):
        """A well-formed CV should pass validation with no violations."""
        optimized = _make_optimized_cv()
        agent = CVValidatorAgent()

        result = agent.execute(CVValidatorInput(original=structured_cv, optimized=optimized))

        assert result.is_valid is True
        assert result.violations == []

    def test_missing_email_fails_validation(self, structured_cv):
        """A CV with an empty contact email must fail validation."""
        optimized = _make_optimized_cv(email="")
        agent = CVValidatorAgent()

        result = agent.execute(CVValidatorInput(original=structured_cv, optimized=optimized))

        assert result.is_valid is False
        assert any("email" in v.lower() for v in result.violations)

    def test_no_experience_or_skills_fails_validation(self, structured_cv):
        """A CV without experience or skills sections must fail validation."""
        sections = [
            CVSectionSchema(
                section_type="summary",
                raw_text="A passionate developer.",
                items=[],
            )
        ]
        optimized = _make_optimized_cv(sections=sections)
        agent = CVValidatorAgent()

        result = agent.execute(CVValidatorInput(original=structured_cv, optimized=optimized))

        assert result.is_valid is False

    def test_empty_section_fails_validation(self, structured_cv):
        """A section with empty raw_text after rewriting must fail."""
        sections = [
            CVSectionSchema(section_type="experience", raw_text="", items=[]),
            CVSectionSchema(section_type="skills", raw_text="Python", items=["Python"]),
        ]
        optimized = _make_optimized_cv(sections=sections)
        agent = CVValidatorAgent()

        result = agent.execute(CVValidatorInput(original=structured_cv, optimized=optimized))

        assert result.is_valid is False

    def test_drastic_shrinkage_fails_validation(self):
        """A section shrunk by more than 50% must trigger a violation."""
        long_text = "A" * 200
        short_text = "A" * 50  # 25% of original → exceeds the 50% threshold
        original_cv = StructuredCVSchema(
            contact=ContactInfoSchema(name="Test", email="t@t.com"),
            sections=[
                CVSectionSchema(
                    section_type="experience",
                    raw_text=long_text,
                    items=[],
                ),
                CVSectionSchema(
                    section_type="skills",
                    raw_text="Python",
                    items=[],
                ),
            ],
        )
        optimized = _make_optimized_cv(
            sections=[
                CVSectionSchema(
                    section_type="experience",
                    raw_text=short_text,
                    items=[],
                ),
                CVSectionSchema(
                    section_type="skills",
                    raw_text="Python",
                    items=["Python"],
                ),
            ]
        )
        agent = CVValidatorAgent()

        result = agent.execute(CVValidatorInput(original=original_cv, optimized=optimized))

        assert result.is_valid is False
        assert any("shrank" in v for v in result.violations)
