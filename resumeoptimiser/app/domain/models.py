"""Pure domain models (no ORM, no Pydantic).

These are immutable dataclasses representing core business concepts.
They carry no validation logic – that lives in schemas/.
They carry no persistence logic – that lives in infrastructure/.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------


class SectionType(str, Enum):
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    CERTIFICATIONS = "certifications"
    PROJECTS = "projects"
    LANGUAGES = "languages"
    OTHER = "other"


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# CV domain model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CVSection:
    """A single section of a CV (e.g. Experience, Skills)."""

    section_type: SectionType
    raw_text: str
    items: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ContactInfo:
    name: str
    email: str
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    github: str = ""


@dataclass(frozen=True)
class StructuredCV:
    """Fully parsed and structured representation of a CV."""

    contact: ContactInfo
    sections: tuple[CVSection, ...] = field(default_factory=tuple)
    raw_text: str = ""


# ---------------------------------------------------------------------------
# Job domain model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RequiredSkill:
    skill: str
    required: bool = True


@dataclass(frozen=True)
class StructuredJob:
    """Normalised representation of a job description."""

    title: str
    company: str
    employment_type: EmploymentType
    required_skills: tuple[RequiredSkill, ...] = field(default_factory=tuple)
    responsibilities: tuple[str, ...] = field(default_factory=tuple)
    qualifications: tuple[str, ...] = field(default_factory=tuple)
    raw_text: str = ""


# ---------------------------------------------------------------------------
# Scoring domain model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SectionScore:
    """Cosine similarity score for one CV section against the job."""

    section_type: SectionType
    score: float  # 0.0 – 1.0


@dataclass(frozen=True)
class SimilarityScore:
    """Aggregate similarity result for one CV ↔ Job pair."""

    overall: float
    section_scores: tuple[SectionScore, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Report domain model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MismatchItem:
    """One specific gap between the CV and the job."""

    field: str
    cv_value: str
    job_expectation: str
    explanation: str


@dataclass(frozen=True)
class ExplanationReport:
    """LLM-generated explanation of mismatches."""

    mismatches: tuple[MismatchItem, ...] = field(default_factory=tuple)
    summary: str = ""
