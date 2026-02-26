"""Pydantic v2 schemas for explanation and rewriting."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.cv import StructuredCVSchema
from app.schemas.job import StructuredJobSchema
from app.schemas.scoring import SimilarityScoreSchema


class MismatchItemSchema(BaseModel):
    field: str
    cv_value: str
    job_expectation: str
    explanation: str


class ExplanationReportSchema(BaseModel):
    """Output schema returned by ScoreExplainerAgent."""

    mismatches: list[MismatchItemSchema] = Field(default_factory=list)
    summary: str = ""


class ScoreExplainerInput(BaseModel):
    cv: StructuredCVSchema
    job: StructuredJobSchema
    score: SimilarityScoreSchema


# ---------------------------------------------------------------------------
# CV Rewriting
# ---------------------------------------------------------------------------


class OptimizedCVSchema(BaseModel):
    """Output schema returned by CVRewriteAgent."""

    contact: "ContactInfoSchema"
    sections: list["CVSectionSchema"] = Field(default_factory=list)
    changes_summary: list[str] = Field(default_factory=list)


class CVRewriteInput(BaseModel):
    cv: StructuredCVSchema
    job: StructuredJobSchema
    explanation: ExplanationReportSchema


# Resolve forward refs
from app.schemas.cv import ContactInfoSchema, CVSectionSchema  # noqa: E402

OptimizedCVSchema.model_rebuild()
