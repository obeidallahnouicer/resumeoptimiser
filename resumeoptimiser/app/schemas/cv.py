"""Pydantic v2 schemas for CV parsing inputs and outputs."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.domain.models import SectionType


class CVSectionSchema(BaseModel):
    section_type: SectionType
    raw_text: str = Field(min_length=1)
    items: list[str] = Field(default_factory=list)


class ContactInfoSchema(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""


class StructuredCVSchema(BaseModel):
    """Output schema returned by CVParserAgent."""

    contact: ContactInfoSchema
    sections: list[CVSectionSchema] = Field(default_factory=list)
    raw_text: str = ""


class CVParserInput(BaseModel):
    """Input schema for CVParserAgent."""

    raw_text: str = Field(min_length=10, description="Raw CV text extracted from a file.")
