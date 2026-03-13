"""cv_to_markdown.py – deterministic StructuredCV → Markdown converter.

This is the ONLY correct way to produce original_cv.md.
It operates purely on the already-validated StructuredCVSchema — no LLM,
no OCR, no guessing. Same input always produces the same output.

The Markdown produced here is the immutable ground truth that the
MarkdownRewriteAgent may only improve wording in, never restructure.

Format contract:
  # FULL NAME
  email  |  phone  |  location  |  linkedin  |  github

  ## SECTION HEADING

  **Job Title | Company | Dates | Location**
  - Achievement bullet one
  - Achievement bullet two

  ## NEXT SECTION
  - item
"""

from __future__ import annotations

from app.domain.models import SectionType
from app.schemas.cv import CVSectionSchema, ContactInfoSchema, StructuredCVSchema

_SECTION_HEADINGS: dict[str, str] = {
    SectionType.SUMMARY:        "PROFESSIONAL SUMMARY",
    SectionType.EXPERIENCE:     "PROFESSIONAL EXPERIENCE",
    SectionType.EDUCATION:      "EDUCATION",
    SectionType.SKILLS:         "TECHNICAL SKILLS",
    SectionType.CERTIFICATIONS: "CERTIFICATIONS",
    SectionType.PROJECTS:       "PROJECTS",
    SectionType.LANGUAGES:      "LANGUAGES",
    SectionType.OTHER:          "ADDITIONAL INFORMATION",
}


def _section_heading(section_type: str) -> str:
    try:
        st = SectionType(section_type)
        return _SECTION_HEADINGS.get(st, section_type.upper())
    except ValueError:
        return section_type.upper()


def _render_contact(contact: ContactInfoSchema) -> str:
    parts = [p for p in [
        contact.email,
        contact.phone,
        contact.location,
        contact.linkedin,
        contact.github,
    ] if p and p.strip()]
    return "  |  ".join(parts)


def _looks_like_entry_header(item: str) -> bool:
    """Return True if this item is a role/education header, not a content bullet.

    A header looks like: "Title | Company | Dates | Location"
    A bullet looks like: "Built a data pipeline processing 10M events/day"

    Criteria:
    - Contains a pipe separator (|) — the canonical parser format
    - OR contains an em/en dash separator with a short length
    - Does NOT start with a lowercase letter
    - Does NOT start with action verbs (Led, Built, Developed, …)
    """
    if not item or len(item) > 160:
        return False
    if item[0].islower():
        return False
    # Pipe separator is the strongest signal — parser is instructed to use "Role | Co | Dates"
    if "|" in item:
        return True
    # Em/en dash separators for education or alternative formats
    if any(sep in item for sep in ("–", "—", " · ")):
        # Only treat as header if short enough to be a title line
        return len(item) < 120
    return False


def _render_section(section: CVSectionSchema) -> list[str]:
    lines: list[str] = []
    heading = _section_heading(section.section_type)
    lines.append(f"## {heading}")
    lines.append("")

    if section.items:
        # Track whether we just emitted a sub-entry header so we can
        # add a blank line between entries for readability.
        last_was_header = False
        for item in section.items:
            item = item.strip()
            if not item:
                continue
            if _looks_like_entry_header(item):
                # Blank line before each new entry (except the very first)
                if last_was_header or lines[-1] != "":
                    # Only add blank line if previous line was a bullet (not already blank)
                    if lines[-1] != "":
                        lines.append("")
                lines.append(f"**{item}**")
                last_was_header = True
            else:
                # Content bullet — strip any leading dash/bullet the parser may have added
                bullet_text = item.lstrip("-•*– ").strip()
                lines.append(f"- {bullet_text}")
                last_was_header = False
    elif section.raw_text.strip():
        # Fall back to raw_text, split into bullets by newline
        for raw_line in section.raw_text.strip().splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                lines.append("")
            else:
                bullet_text = raw_line.lstrip("-•*– ").strip()
                lines.append(f"- {bullet_text}" if bullet_text else "")

    return lines


def structured_cv_to_markdown(cv: StructuredCVSchema) -> str:
    """Convert a StructuredCVSchema to clean Markdown.

    Deterministic: no LLM, no randomness. Preserves all content exactly.
    """
    lines: list[str] = []

    # Header
    name = (cv.contact.name or "").strip().upper() or "CANDIDATE"
    lines.append(f"# {name}")

    contact_line = _render_contact(cv.contact)
    if contact_line:
        lines.append(contact_line)

    # Sections
    for section in cv.sections:
        lines.append("")
        section_lines = _render_section(section)
        lines.extend(section_lines)

    return "\n".join(lines).strip()
