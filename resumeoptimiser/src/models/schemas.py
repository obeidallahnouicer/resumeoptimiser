"""Pydantic models for validation and API requests/responses."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from enum import Enum


class SkillLevel(str, Enum):
    """Skill proficiency levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class MatchStatus(str, Enum):
    """Skill matching status."""
    DIRECT = "direct"
    TRANSFERABLE = "transferable"
    MISSING = "missing"


# ============= BASE SKILLS SCHEMA =============

class Skill(BaseModel):
    """Individual skill with proficiency and projects."""
    name: str
    years: int
    level: SkillLevel
    projects: List[str]
    description: str


class Experience(BaseModel):
    """Work experience entry."""
    title: str
    company: str
    duration_months: int
    role: str
    bullet_points: List[str]
    measurable_impact: List[str]


class BaseSkillsData(BaseModel):
    """Complete base skills and experience data (truth file)."""
    name: str
    email: str
    phone: str
    summary: str
    skills: List[Skill]
    experience: List[Experience]
    domain_knowledge: Optional[List[str]] = []
    learning_mode: Optional[List[str]] = []


# ============= JOB DESCRIPTION SCHEMA =============

class ParsedJobDescription(BaseModel):
    """Parsed and structured job description."""
    core_stack: List[str]
    secondary_stack: List[str]
    domain: List[str]
    seniority: str
    keywords: List[str]
    raw_jd: Optional[str] = None


# ============= SKILL MATCHING SCHEMA =============

class SkillMatch(BaseModel):
    """Result of matching a single skill."""
    status: MatchStatus
    source: Optional[str] = None
    similarity: float = Field(ge=0, le=1)
    closest_match: Optional[str] = None


class SkillMatchResult(BaseModel):
    """Complete skill matching result."""
    matches: Dict[str, SkillMatch]
    unmatched_jd_requirements: List[str] = []
    total_matched: int
    total_jd_requirements: int


# ============= SCORING ENGINE SCHEMA =============

class ScoreBreakdown(BaseModel):
    """Breakdown of CV score components."""
    stack_alignment: float = Field(ge=0, le=40)
    capability_match: float = Field(ge=0, le=20)
    seniority_fit: float = Field(ge=0, le=15)
    domain_relevance: float = Field(ge=0, le=10)
    sponsorship_feasibility: float = Field(ge=0, le=15)


class CVScore(BaseModel):
    """Complete CV scoring result."""
    total_score: float = Field(ge=0, le=100)
    category: Literal["green", "yellow", "red"]
    breakdown: ScoreBreakdown
    recommendation: str


# ============= CV REWRITER SCHEMA =============

class RewrittenCV(BaseModel):
    """Generated LaTeX CV with content sections."""
    experience_section: str
    skills_section: str
    latex_content: str
    warnings: List[str] = []


# ============= API REQUEST/RESPONSE SCHEMA =============

class ParseJobDescriptionRequest(BaseModel):
    """Request to parse job description."""
    jd_text: str


class MatchSkillsRequest(BaseModel):
    """Request to match skills."""
    jd_json: ParsedJobDescription


class ScoreCVRequest(BaseModel):
    """Request to score CV."""
    skill_match_json: SkillMatchResult
    jd_json: ParsedJobDescription


class RewriteCVRequest(BaseModel):
    """Request to rewrite CV."""
    jd_json: ParsedJobDescription
    skill_match_json: SkillMatchResult
    cv_score: CVScore


class CompilePDFRequest(BaseModel):
    """Request to compile LaTeX to PDF."""
    latex_content: str


class EndToEndRequest(BaseModel):
    """Request for end-to-end CV generation."""
    jd_text: str


class EndToEndResponse(BaseModel):
    """Complete end-to-end response."""
    parsed_jd: ParsedJobDescription
    skill_match: SkillMatchResult
    cv_score: CVScore
    rewritten_cv: RewrittenCV
    pdf_path: Optional[str] = None
    logs: List[str] = []