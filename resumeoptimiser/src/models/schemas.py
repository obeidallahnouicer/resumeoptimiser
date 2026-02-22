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


# ============= SEMANTIC CV MATCHING SCHEMA =============

class SemanticMatchingRequest(BaseModel):
    """Request for semantic CV to JD matching."""
    cv_pdf_path: str
    job_description_text: str
    profile_md_path: Optional[str] = None


class GapAnalysisItem(BaseModel):
    """Item in gap analysis."""
    gap_id: str
    requirement: str
    gap_type: Literal[
        "skill_gap",
        "wording_gap",
        "structural_gap",
        "experience_gap",
        "education_gap",
        "requirement_gap"
    ]
    severity: Literal["critical", "high", "moderate", "low"]
    similarity: float = Field(ge=0, le=1)
    closest_match: Optional[str] = None
    suggested_improvement: Optional[str] = None
    source: Optional[str] = None


class SemanticMatchResult(BaseModel):
    """Result of semantic CV matching."""
    overall_score: float = Field(ge=0, le=1)
    confidence: Literal["strong", "viable", "risky", "low"]
    section_scores: Dict[str, Dict[str, Any]]
    skill_match_ratio: float = Field(ge=0, le=1)
    gaps: List[GapAnalysisItem]
    critical_gaps: int
    recommendations: List[str]


class CVOptimizationRequest(BaseModel):
    """Request to optimize CV based on JD."""
    cv_pdf_path: str
    job_description_text: str
    profile_md_path: Optional[str] = None
    apply_optimizations: bool = False


class CVOptimizationResult(BaseModel):
    """Result of CV optimization."""
    original_score: float = Field(ge=0, le=1)
    optimized_score: float = Field(ge=0, le=1)
    improvement_delta: float
    improvements_made: List[str]
    optimized_sections: Dict[str, str]
    warnings: List[str] = []
    compliance_check: Dict[str, bool]  # e.g. {"no_hallucination": True}


class SemanticCVReport(BaseModel):
    """Complete semantic CV matching report."""
    matching_result: SemanticMatchResult
    optimization_result: Optional[CVOptimizationResult] = None
    analysis_timestamp: str
    summary: str
