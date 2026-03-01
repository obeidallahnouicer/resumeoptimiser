"""Pydantic v2 schemas for job description normalisation."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.models import EmploymentType


class RequiredSkillSchema(BaseModel):
    skill: str = Field(min_length=1)
    required: bool = True


class StructuredJobSchema(BaseModel):
    """Output schema returned by JobNormalizerAgent."""

    title: str = Field(min_length=1)
    company: str = ""
    employment_type: EmploymentType = EmploymentType.UNKNOWN
    required_skills: list[RequiredSkillSchema] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    qualifications: list[str] = Field(default_factory=list)
    raw_text: str = ""

    # ── Enriched fields (populated by the improved normalizer) ──────
    detected_language: str = Field(default="en", description="ISO 639-1 code: en, fr, …")
    hard_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    languages_required: list[str] = Field(default_factory=list)
    min_years_experience: float = Field(default=0.0)
    education_level: str = Field(default="", description="e.g. bachelor, master, phd, diploma, …")
    certifications_preferred: list[str] = Field(default_factory=list)
    methodologies: list[str] = Field(default_factory=list)
    domain: str = Field(default="", description="Industry/domain: finance, IT, healthcare, …")


class JobNormalizerInput(BaseModel):
    """Input schema for JobNormalizerAgent."""

    raw_text: str = Field(min_length=10, description="Raw job description text.")
