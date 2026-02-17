"""CV rewriting service."""

from typing import List
from jinja2 import Template

from src.models.schemas import RewrittenCV, BaseSkillsData, SkillMatchResult, CVScore
from src.core.config import LATEX_TEMPLATE_FILE


LATEX_TEMPLATE = r"""
\documentclass{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\geometry{margin=0.75in}

\begin{document}

\section*{Experience}
{{ experience_section }}

\section*{Skills}
{{ skills_section }}

\end{document}
"""


def validate_latex_syntax(latex_content: str) -> List[str]:
    """
    Basic LaTeX syntax validation.

    Args:
        latex_content: LaTeX content to validate

    Returns:
        List of warnings/errors
    """
    warnings = []

    # Check for unmatched braces
    open_braces = latex_content.count('{')
    close_braces = latex_content.count('}')
    if open_braces != close_braces:
        warnings.append(f"Unmatched braces: {open_braces} open, {close_braces} close")

    # Check for unmatched dollar signs (math mode)
    if latex_content.count('$') % 2 != 0:
        warnings.append("Unmatched $ signs in math mode")

    # Check for common issues
    if r'\section' in latex_content and r'\end{document}' not in latex_content:
        warnings.append("Missing \\end{document}")

    return warnings


def generate_experience_section(
    base_skills: BaseSkillsData,
    skill_match: SkillMatchResult
) -> str:
    """
    Generate LaTeX experience section using base CV and skill matches.

    Args:
        base_skills: User's base skills and experience
        skill_match: Skill matching result

    Returns:
        LaTeX formatted experience section
    """
    section_latex = ""

    for exp in base_skills.experience:
        # Build enhanced bullet points
        highlighted_bullets = list(exp.bullet_points)

        section_latex += f"""
\\subsection*{{{exp.title} @ {exp.company}}}
\\textit{{{exp.role}}} \\\\
"""
        for bullet in highlighted_bullets:
            section_latex += f"\\item {bullet}\n"

        if exp.measurable_impact:
            section_latex += "\\textbf{Impact:} "
            section_latex += ", ".join(exp.measurable_impact)
            section_latex += "\n\n"

    return section_latex


def generate_skills_section(
    base_skills: BaseSkillsData,
    skill_match: SkillMatchResult
) -> str:
    """
    Generate LaTeX skills section, emphasizing matched skills.

    Args:
        base_skills: User's base skills
        skill_match: Skill matching result

    Returns:
        LaTeX formatted skills section
    """
    section_latex = ""

    # Group skills by match status
    direct_matches = [
        (name, match) for name, match in skill_match.matches.items()
        if match.status.value == "direct"
    ]
    transferable_matches = [
        (name, match) for name, match in skill_match.matches.items()
        if match.status.value == "transferable"
    ]

    # Direct matches (emphasized)
    if direct_matches:
        section_latex += "\\textbf{Core Skills:} "
        core_skills = ", ".join([name for name, _ in direct_matches])
        section_latex += core_skills + "\n\n"

    # Transferable matches
    if transferable_matches:
        section_latex += "\\textbf{Related Skills:} "
        related_skills = ", ".join([
            f"{name} ({match.closest_match})"
            for name, match in transferable_matches
        ])
        section_latex += related_skills + "\n\n"

    # Add other base skills
    all_matched_names = {name for name, _ in direct_matches + transferable_matches}
    other_skills = [s.name for s in base_skills.skills if s.name not in all_matched_names]
    if other_skills:
        section_latex += "\\textbf{Additional Skills:} "
        section_latex += ", ".join(other_skills)

    return section_latex


def rewrite_cv(
    base_skills: BaseSkillsData,
    skill_match: SkillMatchResult,
    cv_score: CVScore
) -> RewrittenCV:
    """
    Rewrite base CV into LaTeX using match JSON.
    Truth-constrained: only uses base skills, no hallucination.

    Args:
        base_skills: User's base skills and experience
        skill_match: Skill matching result
        cv_score: CV scoring result

    Returns:
        RewrittenCV with LaTeX content
    """
    experience_section = generate_experience_section(base_skills, skill_match)
    skills_section = generate_skills_section(base_skills, skill_match)

    # Render LaTeX template
    template = Template(LATEX_TEMPLATE)
    latex_content = template.render(
        experience_section=experience_section,
        skills_section=skills_section
    )

    # Validate LaTeX
    warnings = validate_latex_syntax(latex_content)

    # Add truth constraint warning if score is low
    if cv_score.category == "red":
        warnings.append(
            "Low match score. Consider applying to roles better aligned with your skills."
        )

    return RewrittenCV(
        experience_section=experience_section,
        skills_section=skills_section,
        latex_content=latex_content,
        warnings=warnings
    )