"""Scoring engine for CV evaluation."""

from src.models.schemas import SkillMatchResult, CVScore, ScoreBreakdown, ParsedJobDescription
from src.core.config import SCORE_GREEN_THRESHOLD, SCORE_YELLOW_THRESHOLD


def calculate_stack_alignment(skill_match: SkillMatchResult) -> float:
    """Calculate stack alignment score (0-40)."""
    if skill_match.total_jd_requirements == 0:
        return 0.0

    matched_direct = sum(
        1 for match in skill_match.matches.values()
        if match.status.value == "direct"
    )
    matched_transferable = sum(
        1 for match in skill_match.matches.values()
        if match.status.value == "transferable"
    )

    # Direct matches worth full points, transferable worth 50%
    matched_score = matched_direct + (matched_transferable * 0.5)
    return (matched_score / skill_match.total_jd_requirements) * 40


def calculate_capability_match(skill_match: SkillMatchResult) -> float:
    """Calculate capability match score (0-20)."""
    total_matched = skill_match.total_matched
    total_required = skill_match.total_jd_requirements

    if total_required == 0:
        return 20.0

    match_ratio = total_matched / total_required
    return min(match_ratio * 20, 20.0)


def calculate_seniority_fit() -> float:
    """Calculate seniority fit score (0-15)."""
    # Placeholder: would require years of experience data
    return 10.0


def calculate_domain_relevance(jd_parsed: ParsedJobDescription) -> float:
    """Calculate domain relevance score (0-10)."""
    if len(jd_parsed.domain) == 0:
        return 5.0
    return 7.0


def calculate_sponsorship_feasibility(skill_match: SkillMatchResult) -> float:
    """Calculate sponsorship feasibility score (0-15)."""
    if skill_match.total_jd_requirements == 0:
        return 15.0

    missing_ratio = len(skill_match.unmatched_jd_requirements) / skill_match.total_jd_requirements

    if missing_ratio < 0.2:
        return 15.0
    elif missing_ratio < 0.5:
        return 10.0
    else:
        return 5.0


def get_score_category_and_recommendation(total_score: float) -> tuple:
    """Get score category and recommendation message."""
    if total_score >= SCORE_GREEN_THRESHOLD:
        return "green", "Strong fit! Your skills align well with this position."
    elif total_score >= SCORE_YELLOW_THRESHOLD:
        return "yellow", "Moderate fit. Consider learning the missing skills."
    else:
        return "red", "Weak fit. Significant skill gaps exist."


def score_cv(
    skill_match: SkillMatchResult,
    jd_parsed: ParsedJobDescription
) -> CVScore:
    """
    Calculate ATS-friendly score and capability alignment.

    Args:
        skill_match: Skill matching result
        jd_parsed: Parsed job description

    Returns:
        CVScore with total score and breakdown
    """
    stack_alignment = calculate_stack_alignment(skill_match)
    capability_match = calculate_capability_match(skill_match)
    seniority_fit = calculate_seniority_fit()
    domain_relevance = calculate_domain_relevance(jd_parsed)
    sponsorship_feasibility = calculate_sponsorship_feasibility(skill_match)

    total_score = (
        stack_alignment +
        capability_match +
        seniority_fit +
        domain_relevance +
        sponsorship_feasibility
    )

    category, recommendation = get_score_category_and_recommendation(total_score)

    return CVScore(
        total_score=total_score,
        category=category,
        breakdown=ScoreBreakdown(
            stack_alignment=stack_alignment,
            capability_match=capability_match,
            seniority_fit=seniority_fit,
            domain_relevance=domain_relevance,
            sponsorship_feasibility=sponsorship_feasibility
        ),
        recommendation=recommendation
    )