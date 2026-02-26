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


class JobNormalizerInput(BaseModel):
    """Input schema for JobNormalizerAgent."""

    raw_text: str = Field(min_length=10, description="Raw job description text.")
