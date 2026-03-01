"""Pydantic v2 schemas for CV parsing inputs and outputs."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.models import SectionType


class CVSectionSchema(BaseModel):
    section_type: SectionType
    raw_text: str = Field(default="")
    items: list[str] = Field(default_factory=list)


class ContactInfoSchema(BaseModel):
    name: str = Field(default="")
    email: str = Field(default="")
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""


class StructuredCVSchema(BaseModel):
    """Output schema returned by CVParserAgent."""

    contact: ContactInfoSchema = Field(default_factory=ContactInfoSchema)
    sections: list[CVSectionSchema] = Field(default_factory=list)
    raw_text: str = ""

    # ── Enriched fields (populated by the improved parser) ──────────
    detected_language: str = Field(default="en", description="ISO 639-1 code: en, fr, …")
    hard_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    languages_spoken: list[str] = Field(default_factory=list)
    total_years_experience: float = Field(default=0.0)
    education_level: str = Field(default="", description="e.g. bachelor, master, phd, diploma, …")
    certifications: list[str] = Field(default_factory=list)


class CVParserInput(BaseModel):
    """Input schema for CVParserAgent."""

    raw_text: str = Field(min_length=10, description="Raw CV text extracted from a file.")
