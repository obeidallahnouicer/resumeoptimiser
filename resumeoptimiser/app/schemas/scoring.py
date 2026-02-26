"""Pydantic v2 schemas for similarity scoring."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.models import SectionType


class SectionScoreSchema(BaseModel):
    section_type: SectionType
    score: float = Field(ge=0.0, le=1.0)


class SimilarityScoreSchema(BaseModel):
    """Output schema returned by SemanticMatcherAgent."""

    overall: float = Field(ge=0.0, le=1.0)
    section_scores: list[SectionScoreSchema] = Field(default_factory=list)


class SemanticMatcherInput(BaseModel):
    """Input schema for SemanticMatcherAgent."""

    cv: "StructuredCVSchema"
    job: "StructuredJobSchema"


# Resolve forward refs at import time
from app.schemas.cv import StructuredCVSchema  # noqa: E402
from app.schemas.job import StructuredJobSchema  # noqa: E402

SemanticMatcherInput.model_rebuild()
