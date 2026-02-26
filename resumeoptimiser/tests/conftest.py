"""Shared pytest fixtures for all test suites.

Provides:
- Minimal StructuredCVSchema / StructuredJobSchema instances
- Mock LLMClientProtocol
- Mock EmbeddingClientProtocol
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import numpy as np
import pytest

from app.schemas.cv import ContactInfoSchema, CVSectionSchema, StructuredCVSchema
from app.schemas.job import RequiredSkillSchema, StructuredJobSchema
from app.schemas.scoring import SectionScoreSchema, SimilarityScoreSchema


# ---------------------------------------------------------------------------
# Domain fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def contact_info() -> ContactInfoSchema:
    return ContactInfoSchema(
        name="Jane Doe",
        email="jane@example.com",
        phone="+1-555-0100",
        location="Berlin, Germany",
    )


@pytest.fixture()
def cv_sections() -> list[CVSectionSchema]:
    return [
        CVSectionSchema(
            section_type="experience",
            raw_text="5 years of Python development, worked on distributed systems.",
            items=["Python", "distributed systems"],
        ),
        CVSectionSchema(
            section_type="skills",
            raw_text="Python, FastAPI, PostgreSQL, Docker, Kubernetes",
            items=["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
        ),
    ]


@pytest.fixture()
def structured_cv(contact_info, cv_sections) -> StructuredCVSchema:
    return StructuredCVSchema(contact=contact_info, sections=cv_sections)


@pytest.fixture()
def structured_job() -> StructuredJobSchema:
    return StructuredJobSchema(
        title="Senior Python Developer",
        company="Acme Corp",
        employment_type="full_time",
        required_skills=[
            RequiredSkillSchema(skill="Python", required=True),
            RequiredSkillSchema(skill="FastAPI", required=True),
            RequiredSkillSchema(skill="PostgreSQL", required=False),
        ],
        responsibilities=["Build REST APIs", "Write unit tests", "Code review"],
        qualifications=["5+ years Python", "Experience with async frameworks"],
    )


@pytest.fixture()
def similarity_score() -> SimilarityScoreSchema:
    return SimilarityScoreSchema(
        overall=0.72,
        section_scores=[
            SectionScoreSchema(section_type="experience", score=0.75),
            SectionScoreSchema(section_type="skills", score=0.85),
        ],
    )


# ---------------------------------------------------------------------------
# Infrastructure mock fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_llm():
    """A mock LLMClientProtocol that returns configurable responses."""
    mock = MagicMock()
    mock.complete = MagicMock(return_value="{}")
    return mock


@pytest.fixture()
def mock_embedder():
    """A mock EmbeddingClientProtocol returning fixed unit vectors."""
    mock = MagicMock()
    fixed_vector = np.ones(384, dtype=np.float32) / np.sqrt(384)
    mock.embed = MagicMock(return_value=fixed_vector)
    mock.embed_batch = MagicMock(return_value=np.stack([fixed_vector]))
    return mock
