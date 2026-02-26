"""Schemas package – re-exports all public Pydantic schemas."""

from app.schemas.cv import CVParserInput, CVSectionSchema, ContactInfoSchema, StructuredCVSchema
from app.schemas.job import JobNormalizerInput, RequiredSkillSchema, StructuredJobSchema
from app.schemas.scoring import SemanticMatcherInput, SectionScoreSchema, SimilarityScoreSchema
from app.schemas.report import (
    CVRewriteInput,
    ExplanationReportSchema,
    MismatchItemSchema,
    OptimizedCVSchema,
    ScoreExplainerInput,
)
from app.schemas.pipeline import (
    ComparisonReportSchema,
    ImprovedScoreSchema,
    OptimizeRequest,
    OptimizeResponse,
)

__all__ = [
    "CVParserInput",
    "CVSectionSchema",
    "ContactInfoSchema",
    "StructuredCVSchema",
    "JobNormalizerInput",
    "RequiredSkillSchema",
    "StructuredJobSchema",
    "SemanticMatcherInput",
    "SectionScoreSchema",
    "SimilarityScoreSchema",
    "CVRewriteInput",
    "ExplanationReportSchema",
    "MismatchItemSchema",
    "OptimizedCVSchema",
    "ScoreExplainerInput",
    "ComparisonReportSchema",
    "ImprovedScoreSchema",
    "OptimizeRequest",
    "OptimizeResponse",
]
