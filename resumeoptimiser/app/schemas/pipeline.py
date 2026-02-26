"""Pydantic v2 schemas for the final comparison report and API contracts."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.scoring import SimilarityScoreSchema
from app.schemas.report import ExplanationReportSchema, OptimizedCVSchema


class ImprovedScoreSchema(BaseModel):
    """Output schema returned by RescoreAgent."""

    before: SimilarityScoreSchema
    after: SimilarityScoreSchema
    delta: float = Field(description="Improvement in overall score (after - before).")


class ComparisonReportSchema(BaseModel):
    """Full pipeline output returned by ReportGeneratorAgent."""

    improved_score: ImprovedScoreSchema
    explanation: ExplanationReportSchema
    optimized_cv: OptimizedCVSchema
    narrative: str = Field(default="", description="Human-readable summary of improvements.")


# ---------------------------------------------------------------------------
# API-level request / response wrappers
# ---------------------------------------------------------------------------


class OptimizeRequest(BaseModel):
    """Top-level API request body."""

    cv_text: str = Field(min_length=10, description="Raw CV text.")
    job_text: str = Field(min_length=10, description="Raw job description text.")


class OptimizeResponse(BaseModel):
    """Top-level API response body."""

    report: ComparisonReportSchema
