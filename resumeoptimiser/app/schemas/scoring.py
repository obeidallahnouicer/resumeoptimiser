"""Pydantic v2 schemas for similarity scoring."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.models import SectionType


class SectionScoreSchema(BaseModel):
    section_type: SectionType
    score: float = Field(ge=0.0, le=1.0)


# ── LLM-powered match analysis (new pre-semantic layer) ──────────

class SkillMatchSchema(BaseModel):
    skill: str
    found_in_cv: bool = False
    cv_evidence: str = Field(default="", description="Where/how it was found in the CV")


class LLMMatchAnalysisSchema(BaseModel):
    """Output of the LLMMatchAnalyzer — field-by-field CV↔Job comparison."""

    skills_match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    experience_match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    education_match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    languages_match_score: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_llm_score: float = Field(default=0.0, ge=0.0, le=1.0)
    skill_details: list[SkillMatchSchema] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    reasoning: str = Field(default="")


class SimilarityScoreSchema(BaseModel):
    """Output schema returned by SemanticMatcherAgent."""

    overall: float = Field(ge=0.0, le=1.0)
    section_scores: list[SectionScoreSchema] = Field(default_factory=list)

    # ── Enriched with LLM analysis ──
    llm_analysis: LLMMatchAnalysisSchema | None = Field(default=None)
    embedding_score: float = Field(default=0.0, ge=0.0, le=1.0,
                                    description="Pure cosine-similarity score before LLM blending")


class SemanticMatcherInput(BaseModel):
    """Input schema for SemanticMatcherAgent."""

    cv: "StructuredCVSchema"
    job: "StructuredJobSchema"


# Resolve forward refs at import time
from app.schemas.cv import StructuredCVSchema  # noqa: E402
from app.schemas.job import StructuredJobSchema  # noqa: E402

SemanticMatcherInput.model_rebuild()
