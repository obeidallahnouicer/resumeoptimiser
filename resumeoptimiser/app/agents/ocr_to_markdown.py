"""OCRToMarkdownAgent – converts raw OCR/PDF text into clean structured Markdown.

Responsibility:
  Take the raw text extracted from a PDF and produce a clean Markdown document
  that faithfully mirrors the original CV — every word, every bullet, every date.

Design:
  - Fully DETERMINISTIC — no LLM, no AI, no guessing.
  - Uses heuristic line classification to assign Markdown roles.
  - Preserves ALL original wording, order, and structure.
  - OCR artefacts (hard-wrapped lines, extra whitespace) are cleaned.

Output format contract:
  # Full Name
  email  |  phone  |  location

  ## SECTION HEADING
  **Role | Company | Dates**
  - Bullet item

  ## NEXT SECTION
  - item
"""

from __future__ import annotations

import re

from app.agents.base import AgentMeta, BaseAgent
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.markdown import MarkdownInput, MarkdownOutput
from app.services.cv_cache_service import CVCacheService

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Section heading keywords (case-insensitive)
# ---------------------------------------------------------------------------
_SECTION_KEYWORDS = re.compile(
    r"^("
    r"(professional\s+)?summary|profile|objective|about\s+me|profil|résumé|"
    r"(professional\s+)?experience|work\s+(experience|history)|employment|expérience|"
    r"education|formation|études|academic|"
    r"skills?|compétences?|technical\s+skills?|"
    r"languages?|langues?|"
    r"certifications?|awards?|"
    r"projects?|projets?|"
    r"references?|publications?|"
    r"interests?|hobbies|loisirs|volunteer"
    r")\s*[:\-–—]?\s*$",
    re.IGNORECASE,
)

# Contact field patterns
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
_PHONE_RE = re.compile(r"[+\d][\d\s\-().]{6,}")
_URL_RE = re.compile(r"(https?://|www\.|linkedin\.com|github\.com)", re.IGNORECASE)

# Entry header pattern: "Something | Something | Something" or "Something – Something"
_ENTRY_HEADER_RE = re.compile(r".{3,}\s*[|–—]\s*.{2,}")

# Date/location lines that look like entry headers but aren't (start with month or year)
_DATE_START_RE = re.compile(
    r"^(January|February|March|April|May|June|July|August|September|"
    r"October|November|December|\d{4})\b",
    re.IGNORECASE,
)

# Inline bullet separator: "A  •  B  •  C" (bullet used as separator, not list marker)
_INLINE_BULLET_RE = re.compile(r"\s*•\s*")

# Bullet markers that should become "- " bullets
_BULLET_RE = re.compile(r"^\s*[•●▪▸◦‣*\-–]\s+")


def _is_blank(line: str) -> bool:
    return not line.strip()


def _is_section_heading(line: str) -> bool:
    """True if the line is a known CV section heading."""
    return bool(_SECTION_KEYWORDS.match(line.strip()))


def _is_contact_line(line: str) -> bool:
    """True if line looks like contact info (email, phone, URL, location clue)."""
    s = line.strip()
    return bool(_EMAIL_RE.search(s) or _PHONE_RE.search(s) or _URL_RE.search(s))


def _is_entry_header(line: str) -> bool:
    """True if line looks like a role/education header (contains | or –).

    Explicitly rejects date/location lines like
    "January 2026 - Present  |  Tunis, Tunisia" — those start with a month
    name or a four-digit year and are metadata, not entry headers.
    """
    s = line.strip()
    if len(s) > 160 or not s:
        return False
    if s[0].islower():
        return False
    # Date lines start with a month name or year — they are *not* entry headers
    if _DATE_START_RE.match(s):
        return False
    return bool(_ENTRY_HEADER_RE.match(s))


def _is_inline_bullet_list(stripped: str, line: str) -> bool:
    """True when • is used as an inline separator (not a leading bullet marker)."""
    return "•" in stripped and not _has_bullet_marker(line)


def _looks_like_sub_heading(stripped: str) -> bool:
    """True for short skill sub-category lines like 'AI & Machine Learning'.

    Criteria: 2–6 words, title-case or all-caps, no punctuation at end,
    no bullet chars, no pipe/dash separators, no digits.
    """
    if not stripped or len(stripped) > 60:
        return False
    words = stripped.split()
    if not (2 <= len(words) <= 6):
        return False
    # Must not contain digits (dates, percentages, etc.)
    if re.search(r"\d", stripped):
        return False
    # Must not contain separator chars that would make it an entry header
    if re.search(r"[|–—:]", stripped):
        return False
    # Must be title-cased or all-caps
    return stripped.istitle() or stripped.isupper() or stripped[0].isupper()


def _strip_bullet_marker(line: str) -> str:
    """Remove leading bullet markers, returning clean text."""
    return _BULLET_RE.sub("", line).strip()


def _has_bullet_marker(line: str) -> bool:
    return bool(_BULLET_RE.match(line))


def _looks_like_name(line: str) -> bool:
    """Heuristic: short, title-cased or all-caps line near the top → candidate name.

    A name line must NOT contain email/phone/URL (those are contact lines, not names).
    """
    s = line.strip()
    if not s or len(s) > 60 or len(s.split()) < 2:
        return False
    # Reject if it contains contact signals
    if _EMAIL_RE.search(s) or _URL_RE.search(s):
        return False
    # Reject phone-only style lines
    if re.match(r"^[+\d\s\-().]+$", s):
        return False
    # Allow only letters, spaces, hyphens, apostrophes (no pipes, colons, etc.)
    if re.search(r"[^A-Za-zÀ-ÖØ-öø-ÿ\s'\-]", s):
        return False
    return s.isupper() or s.istitle()


# ---------------------------------------------------------------------------
# Main converter
# ---------------------------------------------------------------------------

def _raw_to_markdown(raw_text: str) -> str:
    """Convert raw PDF/OCR text to Markdown deterministically."""
    # Step 1 – join hard-wrapped continuation lines
    text = _join_wrapped_lines(raw_text)
    lines = text.splitlines()

    out: list[str] = []
    found_name = False
    found_first_section = False
    in_contact_block = False

    for line in lines:
        stripped = line.strip()

        # Always preserve blank lines (collapse multiple blanks to one)
        if _is_blank(stripped):
            if out and out[-1] != "":
                out.append("")
            continue

        # ── Name: must check BEFORE entry-header (name has no special chars) ──
        if not found_name and _looks_like_name(stripped):
            out.append(f"# {stripped}")
            found_name = True
            in_contact_block = True
            continue

        # ── Contact block (lines immediately after name, before first section) ─
        if in_contact_block and not found_first_section:
            if not _is_section_heading(stripped):
                out.append(stripped)
                continue
            in_contact_block = False
            # Fall through to section handling

        # ── Section headings ──────────────────────────────────────────────────
        if _is_section_heading(stripped):
            if out and out[-1] != "":
                out.append("")
            out.append(f"## {stripped.rstrip(':').upper()}")
            out.append("")
            found_first_section = True
            in_contact_block = False
            continue

        # ── Entry headers (Role | Company | Dates) ────────────────────────────
        if _is_entry_header(stripped):
            if out and out[-1] != "":
                out.append("")
            out.append(f"**{stripped}**")
            continue

        # ── Inline bullet-separated list  "A  •  B  •  C" ───────────────────
        # When • appears as an inline separator (not a leading marker), split
        # each item into its own "- item" bullet.
        if "•" in stripped and not _has_bullet_marker(line):
            parts = [p.strip() for p in _INLINE_BULLET_RE.split(stripped) if p.strip()]
            if len(parts) > 1:
                for part in parts:
                    out.append(f"- {part}")
                continue

        # ── Bullet items ──────────────────────────────────────────────────────
        if _has_bullet_marker(line):
            out.append(f"- {_strip_bullet_marker(line)}")
            continue

        # ── Skills / category sub-heading  "AI & Machine Learning" ───────────
        # Short title-cased label after a section heading, no separators, no digits.
        if found_first_section and _looks_like_sub_heading(stripped):
            if out and out[-1] != "":
                out.append("")
            out.append(f"**{stripped}**")
            out.append("")
            continue

        # ── Plain content line ────────────────────────────────────────────────
        out.append(stripped)

    # Collapse any trailing blank lines
    while out and out[-1] == "":
        out.pop()

    return "\n".join(out)


def _join_wrapped_lines(text: str) -> str:
    """Join PDF hard-wrap continuation lines into single logical lines."""
    _SENTENCE_END = re.compile(r"[.!?:;,]\s*$")
    _BULLET_START = re.compile(r"^\s*[-•●▪*\d]")
    _BLANK = re.compile(r"^\s*$")
    _HEADING_LIKE = re.compile(
        r"^("
        r"(professional\s+)?summary|experience|education|skills?|languages?|"
        r"certifications?|projects?|references?|profil|expérience|formation|compétences?"
        r")\s*[:\-–—]?\s*$",
        re.IGNORECASE,
    )

    lines = text.splitlines()
    result: list[str] = []

    for line in lines:
        if not result or _BLANK.match(line) or _BLANK.match(result[-1]):
            result.append(line)
            continue
        # Never join onto a heading-like line
        if _HEADING_LIKE.match(line.strip()):
            result.append(line)
            continue
        # Never join a contact/email/URL line onto a name line
        if _EMAIL_RE.search(line) or _URL_RE.search(line):
            result.append(line)
            continue
        prev = result[-1]
        # A continuation line: previous ends mid-sentence AND current line
        # is either lowercase OR indented (space-prefixed, typical of wrapped bullets)
        prev_unfinished = not _SENTENCE_END.search(prev)
        current_is_continuation = (
            line and (
                line[0].islower()
                or (line[0] == " " and not _BULLET_START.match(line))
            )
            and not _BULLET_START.match(line)
        )
        if prev_unfinished and current_is_continuation:
            result[-1] = prev.rstrip() + " " + line.lstrip()
        else:
            result.append(line)

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Agent wrapper (keeps the same interface, no LLM dependency needed)
# ---------------------------------------------------------------------------

class OCRToMarkdownAgent(BaseAgent[MarkdownInput, MarkdownOutput]):
    """Converts raw OCR/PDF text to structured Markdown — deterministically, no LLM.
    
    Caching:
    - Computes a stable SHA256 hash of the input raw_text
    - Checks cache for 'parsed_cv:{cv_hash}'
    - If found: returns cached markdown (CACHE_HIT logged)
    - If not found: converts deterministically and stores in cache (CACHE_MISS logged)
    """

    meta = AgentMeta(name="OCRToMarkdownAgent", version="2.0.0")

    def __init__(
        self,
        llm: LLMClientProtocol,
        cv_cache: CVCacheService | None = None,
    ) -> None:
        # LLM is accepted to keep the constructor signature compatible with deps.py,
        # but it is NOT used. Conversion is fully deterministic.
        self._llm = llm
        self._cv_cache = cv_cache

    def execute(self, input: MarkdownInput) -> MarkdownOutput:  # noqa: A002
        logger.info("ocr_to_markdown.start", text_length=len(input.raw_text))

        # If caching is enabled, check cache first
        if self._cv_cache:
            markdown_output, cache_hit = self._cv_cache.get_or_compute(
                input.raw_text,
                compute_fn=lambda: MarkdownOutput(markdown=_raw_to_markdown(input.raw_text)),
            )
            if cache_hit:
                logger.info("ocr_to_markdown.cache_hit")
            else:
                logger.info("ocr_to_markdown.cache_miss")
            logger.info("ocr_to_markdown.success", lines=markdown_output.markdown.count("\n"))
            return markdown_output

        # Fallback: no caching, convert directly
        markdown = _raw_to_markdown(input.raw_text)
        logger.info("ocr_to_markdown.success", lines=markdown.count("\n"))
        return MarkdownOutput(markdown=markdown)

    # Keep static helpers accessible for tests
    @staticmethod
    def _join_wrapped_lines(text: str) -> str:
        return _join_wrapped_lines(text)

    @staticmethod
    def _clean_fences(text: str) -> str:
        """No-op kept for backwards-compatibility with any existing tests."""
        return text.strip()
