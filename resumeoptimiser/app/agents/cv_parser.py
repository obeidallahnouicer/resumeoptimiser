"""CVParserAgent – deterministic Markdown → StructuredCVSchema.

Responsibility:
  1. Convert raw PDF/OCR text → clean Markdown (via _raw_to_markdown).
  2. Parse that Markdown into StructuredCVSchema using pure regex — ZERO LLM.

Design:
  - Fully DETERMINISTIC — no AI, no network call, no timeout risk.
  - Single pass over the Markdown lines produced by _raw_to_markdown.
  - LLM parameter kept in __init__ for DI compatibility but is NEVER used.
  - Runs in < 5 ms on any CV.
"""

from __future__ import annotations

import re
from datetime import date

from app.agents.base import AgentMeta, BaseAgent
from app.agents.ocr_to_markdown import (
    _EMAIL_RE,
    _PHONE_RE,
    _URL_RE,
    _raw_to_markdown,
)
from app.core.logging import get_logger
from app.domain.models import SectionType
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.cv import (
    CVParserInput,
    CVSectionSchema,
    ContactInfoSchema,
    StructuredCVSchema,
)

logger = get_logger(__name__)

# ── Markdown structure regexes ────────────────────────────────────────────────
_H1_RE = re.compile(r"^#\s+(.+)$")       # # Name
_H2_RE = re.compile(r"^##\s+(.+)$")       # ## SECTION
_H3_RE = re.compile(r"^###\s+(.+)$")      # ### Role | Company
_BOLD_RE = re.compile(r"^\*\*(.+)\*\*$")  # **Sub-heading**
_BULLET_RE = re.compile(r"^-\s+(.+)$")    # - item

# Section heading → SectionType
_SECTION_MAP: dict[str, SectionType] = {
    "summary": SectionType.SUMMARY,
    "profile": SectionType.SUMMARY,
    "objective": SectionType.SUMMARY,
    "about me": SectionType.SUMMARY,
    "profil": SectionType.SUMMARY,
    "professional experience": SectionType.EXPERIENCE,
    "experience": SectionType.EXPERIENCE,
    "work experience": SectionType.EXPERIENCE,
    "work history": SectionType.EXPERIENCE,
    "employment": SectionType.EXPERIENCE,
    "expérience": SectionType.EXPERIENCE,
    "education": SectionType.EDUCATION,
    "formation": SectionType.EDUCATION,
    "études": SectionType.EDUCATION,
    "academic": SectionType.EDUCATION,
    "skills": SectionType.SKILLS,
    "skill": SectionType.SKILLS,
    "technical skills": SectionType.SKILLS,
    "compétences": SectionType.SKILLS,
    "languages": SectionType.LANGUAGES,
    "langues": SectionType.LANGUAGES,
    "language": SectionType.LANGUAGES,
    "certifications": SectionType.CERTIFICATIONS,
    "certification": SectionType.CERTIFICATIONS,
    "awards": SectionType.CERTIFICATIONS,
    "projects": SectionType.PROJECTS,
    "projets": SectionType.PROJECTS,
}

_KNOWN_SOFT_SKILLS = frozenset({
    "leadership", "communication", "teamwork", "problem solving", "problem-solving",
    "adaptability", "time management", "critical thinking", "creativity", "collaboration",
    "interpersonal", "initiative", "attention to detail", "work ethic", "empathy",
    "negotiation", "presentation", "mentoring", "coaching", "organisation", "organization",
})

_KNOWN_TOOL_RE = re.compile(
    r"\b(vscode|vs code|pycharm|intellij|jira|confluence|git|github|gitlab|bitbucket|"
    r"docker|kubernetes|k8s|jenkins|ansible|terraform|aws|azure|gcp|google cloud|"
    r"power bi|tableau|excel|word|outlook|notion|slack|teams|figma|postman|"
    r"bloomberg|reuters|sap|salesforce|hubspot)\b",
    re.IGNORECASE,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _map_section(heading: str) -> SectionType:
    return _SECTION_MAP.get(heading.lower().strip(), SectionType.OTHER)


def _extract_contact(lines: list[str], name: str) -> ContactInfoSchema:
    email = phone = location = linkedin = github = ""
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if not email and (m := _EMAIL_RE.search(s)):
            email = m.group(0)
        if not phone and (m := _PHONE_RE.search(s)):
            val = m.group(0).strip()
            if len(val) >= 8:
                phone = val
        if not linkedin and (m := re.search(r"linkedin\.com/in/[\w\-]+", s, re.IGNORECASE)):
            linkedin = m.group(0)
        if not github and (m := re.search(r"github\.com/[\w\-]+", s, re.IGNORECASE)):
            github = m.group(0)
        # Location: non-email, non-phone, non-URL segment in a pipe-separated contact line
        if "|" in s and not location:
            for part in s.split("|"):
                part = part.strip()
                if (
                    part
                    and not _EMAIL_RE.search(part)
                    and not _URL_RE.search(part)
                    and not re.match(r"^[+\d\s\-().]+$", part)
                    and len(part) > 3
                ):
                    location = part
                    break
    return ContactInfoSchema(
        name=name, email=email, phone=phone,
        location=location, linkedin=linkedin, github=github,
    )


def _classify_skill(skill: str) -> str:
    s = skill.lower().strip()
    if s in _KNOWN_SOFT_SKILLS:
        return "soft"
    if _KNOWN_TOOL_RE.search(s):
        return "tool"
    return "hard"


def _years_from_date_line(text: str) -> float:
    """Extract years of experience from a date-range string."""
    years = re.findall(r"\b(20\d{2}|19\d{2})\b", text)
    if len(years) >= 2:
        return float(int(years[-1]) - int(years[0]))
    if "present" in text.lower() and len(years) == 1:
        today = date.today()
        return round((today.year - int(years[0])) + today.month / 12, 1)
    return 0.0


def _infer_education_level(items: list[str]) -> str:
    combined = " ".join(items).lower()
    for level, keywords in [
        ("phd", ["phd", "doctorat", "doctorate"]),
        ("master", ["master", "msc", "m.sc", "mba"]),
        ("bachelor", ["bachelor", "bsc", "b.sc", "licence"]),
        ("diploma", ["diploma", "diplôme"]),
        ("certificate", ["certificate", "certificat"]),
    ]:
        if any(k in combined for k in keywords):
            return level
    return ""


def _dedup(lst: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for x in lst:
        key = x.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(x)
    return out


# ── Main Markdown parser ──────────────────────────────────────────────────────

def _parse_markdown(markdown: str) -> StructuredCVSchema:
    """Parse a structured Markdown CV into StructuredCVSchema deterministically."""
    lines = markdown.splitlines()

    name = ""
    contact_lines: list[str] = []
    sections: list[CVSectionSchema] = []

    hard_skills: list[str] = []
    soft_skills: list[str] = []
    tools: list[str] = []
    languages_spoken: list[str] = []
    certifications: list[str] = []
    edu_items: list[str] = []
    total_years: float = 0.0
    detected_language = "en"

    current_section: SectionType | None = None
    current_items: list[str] = []
    current_raw: list[str] = []
    in_header = True  # True until first ## is seen

    def flush() -> None:
        nonlocal current_section, current_items, current_raw
        if current_section is not None:
            sections.append(CVSectionSchema(
                section_type=current_section,
                raw_text="\n".join(current_raw),
                items=list(current_items),
            ))
        current_section = None
        current_items = []
        current_raw = []

    for line in lines:
        # H1 → name
        if m := _H1_RE.match(line):
            name = m.group(1).strip()
            continue

        # Header block (contact lines) — everything before first ##
        if in_header:
            if not _H2_RE.match(line):
                if line.strip():
                    contact_lines.append(line)
                continue
            # Hit a ## — fall through to H2 handling
            in_header = False

        # H2 → new section
        if m := _H2_RE.match(line):
            flush()
            heading = m.group(1).strip()
            current_section = _map_section(heading)
            if any(fr in heading.lower() for fr in ("expérience", "formation", "compétences", "langues")):
                detected_language = "fr"
            continue

        if current_section is None:
            continue

        raw = line.strip()
        if raw:
            current_raw.append(raw)

        # H3 → entry header "Role | Company" or "Degree | Institution"
        if m := _H3_RE.match(line):
            entry = m.group(1).strip()
            current_items.append(entry)
            if current_section == SectionType.EDUCATION:
                edu_items.append(entry)
            continue

        # Bold sub-heading (skill categories) — structural, skip
        if _BOLD_RE.match(line):
            continue

        # Bullet → item
        if m := _BULLET_RE.match(line):
            item = m.group(1).strip()
            # For experience/projects/summary: bullets are body content, not key items
            # For skills/languages/certs/education: bullets ARE the items
            if current_section == SectionType.SKILLS:
                current_items.append(item)
                kind = _classify_skill(item)
                if kind == "soft":
                    soft_skills.append(item)
                elif kind == "tool":
                    tools.append(item)
                else:
                    hard_skills.append(item)
            elif current_section == SectionType.LANGUAGES:
                languages_spoken.append(item)
                current_items.append(item)
            elif current_section == SectionType.CERTIFICATIONS:
                certifications.append(item)
                current_items.append(item)
            elif current_section == SectionType.EDUCATION:
                edu_items.append(item)
                current_items.append(item)
            # experience/projects/summary bullets → raw_text only, not items
            continue

        # Plain text — date lines under ### entries contribute to years
        if raw and current_section == SectionType.EXPERIENCE:
            yrs = _years_from_date_line(raw)
            if yrs > 0:
                total_years += yrs

    flush()

    contact = _extract_contact(contact_lines, name)

    return StructuredCVSchema(
        contact=contact,
        sections=sections,
        raw_text="",
        markdown="",  # caller fills this
        detected_language=detected_language,
        hard_skills=_dedup(hard_skills),
        soft_skills=_dedup(soft_skills),
        tools=_dedup(tools),
        languages_spoken=_dedup(languages_spoken),
        total_years_experience=round(total_years, 1),
        education_level=_infer_education_level(edu_items),
        certifications=_dedup(certifications),
    )


# ── Agent wrapper ─────────────────────────────────────────────────────────────

class CVParserAgent(BaseAgent[CVParserInput, StructuredCVSchema]):
    """Parses raw CV text into StructuredCVSchema — deterministically, zero LLM.

    Flow:
      1. raw text  →  Markdown   (_raw_to_markdown)
      2. Markdown  →  schema     (_parse_markdown)
      3. schema.markdown = the Markdown from step 1
    """

    meta = AgentMeta(name="CVParserAgent", version="4.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        _ = llm  # accepted for DI compatibility, never used

    def execute(self, input: CVParserInput) -> StructuredCVSchema:  # noqa: A002
        logger.info("cv_parser.start", text_length=len(input.raw_text))

        markdown = _raw_to_markdown(input.raw_text)
        logger.info("cv_parser.markdown_ready", chars=len(markdown))

        schema = _parse_markdown(markdown)
        schema.markdown = markdown

        logger.info(
            "cv_parser.done",
            name=schema.contact.name,
            sections=len(schema.sections),
            hard_skills=len(schema.hard_skills),
            years=schema.total_years_experience,
        )
        return schema
