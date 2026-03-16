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
# Ideal Profile Generation
# ---------------------------------------------------------------------------


class IdealProfileSchema(BaseModel):
    """Output schema returned by IdealProfileAgent.

    Describes the ideal candidate profile for the job based on structured
    job data. Guides the two-stage rewrite process.
    """

    role_summary: str = Field(
        description="High-level summary of the ideal candidate for this role."
    )
    core_competencies: list[str] = Field(
        default_factory=list,
        description="Key competencies (capabilities, not tools).",
    )
    technical_stack: list[str] = Field(
        default_factory=list,
        description="Technologies, tools, and frameworks mentioned in the job.",
    )
    preferred_action_verbs: list[str] = Field(
        default_factory=list,
        description="Strong action verbs commonly used in job descriptions for this role.",
    )
    impact_patterns: list[str] = Field(
        default_factory=list,
        description="Common impact/achievement patterns for this role.",
    )
    domain_language: list[str] = Field(
        default_factory=list,
        description="Domain-specific terminology and industry jargon.",
    )


class IdealProfileInput(BaseModel):
    """Input schema for IdealProfileAgent."""

    job: StructuredJobSchema


# ---------------------------------------------------------------------------
# Two-Stage CV Rewriting
# ---------------------------------------------------------------------------


class CVRewriteStage1Input(BaseModel):
    """Input schema for CVRewriteStage1Agent (language transformation)."""

    cv: StructuredCVSchema
    ideal_profile: IdealProfileSchema


class CVRewriteStage2Input(BaseModel):
    """Input schema for CVRewriteStage2Agent (gap closing)."""

    cv_rewrite_stage1: OptimizedCVSchema
    comparison_report: ExplanationReportSchema


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
