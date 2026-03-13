"""MarkdownRewriteAgent – rewrites CV Markdown for ATS compliance and recruiter impact.

This is Step 2 of the layout-safe pipeline:
  original_cv.md → [this agent] → improved_cv.md

Strategy: splits the document into sections at every ## heading boundary and
rewrites each section independently to stay within LLM token limits.
Sections are reassembled in original order.

v3 goals (ATS-first):
  1. Enforce ATS-safe Markdown formatting:
       - Contact block: pipe-separated inline, no sub-bullets
       - Experience entries: **Role | Company**  +  date line  +  bullets
       - Skills: bold category labels + inline comma-separated values (NOT one-per-bullet)
       - Strict ASCII-only hyphens, no nested lists, no HTML
  2. Improve content quality:
       - Strong action verbs, keyword alignment, punchy bullets
       - No invented facts, no structural changes
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.markdown import MarkdownRewriteInput, MarkdownRewriteOutput

logger = get_logger(__name__)

_MAX_RETRIES = 2

# ---------------------------------------------------------------------------
# System prompt – used for every per-section LLM call
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = """\
role: ats_cv_section_editor
version: "3.0"
description: |
  You are a senior ATS-optimisation specialist and technical CV editor.
  You receive ONE SECTION of a CV in Markdown and a target job description.
  Your dual mission:
    1. Rewrite wording for maximum ATS keyword density and recruiter impact.
    2. Enforce ATS-safe Markdown formatting rules so the document parses cleanly
       through Applicant Tracking Systems.

════════════════════════════════════════════════════
ATS FORMATTING RULES — MANDATORY, NEVER VIOLATE
════════════════════════════════════════════════════

HEADINGS:
  - Keep ALL section headings (# ##) exactly as they are. Do not rename or reorder.
  - Section headings must be on their own line with NO trailing punctuation.
  - Use exactly ONE blank line before and after every heading.

CONTACT / HEADER BLOCK (the # name section):
  - Name on its own line: # FIRSTNAME LASTNAME  (all caps, no extra formatting)
  - Contact details on the very next line as pipe-separated inline text:
      City, Country  |  email@example.com  |  +phonenumber
  - If LinkedIn or GitHub exist, append them with  |  separators on the same line.
  - Do NOT use sub-bullets or extra lines for contact info.

EXPERIENCE / EDUCATION ENTRIES (** sub-sections):
  - Format MUST be:  **Role Title | Company Name**
  - Immediately below (no blank line): date range and location as plain text:
      Month YYYY - Month YYYY  |  City, Country
  - Then ONE blank line, then bullet points.
  - Keep each bullet to ONE line. No wrapped multi-line bullets.

BULLET POINTS:
  - Every bullet starts with "- " (hyphen + space). No asterisks, no numbers.
  - Begin EVERY bullet with a strong past-tense action verb (for past roles)
    or present-tense verb (for current role).
  - Each bullet: action verb + what you did + result/tool/scale.
    Pattern: "Verb + [technology/method] + [outcome/scope/metric]"
    Example:  "- Architected multi-agent LLM pipeline reducing processing latency by 40%"
  - Max ~120 characters per bullet. Cut filler; be dense and specific.
  - NO sub-bullets, no nested lists.

SKILLS SECTION:
  - Group skills into bold category labels followed by inline comma-separated values:
      **Category Name:** Skill A, Skill B, Skill C
  - Do NOT use one-skill-per-bullet format (extremely bad for ATS parsing).
  - Each category on its own line. No blank lines between skill lines.
  - Categories to use (merge/rename as needed):
      AI & Machine Learning, Languages & Frameworks, Databases & Infrastructure,
      DevOps & Cloud, Finance & Risk Analytics

LANGUAGES SECTION:
  - One line per language:  - Language: Proficiency Level
  - Keep it concise.

GENERAL FORMATTING:
  - Use only standard ASCII hyphens (-). NEVER use: ‑ – — or • or ●.
  - No bold (**text**) inside bullet content except in skill category labels.
  - No italic text.
  - No HTML tags.
  - No horizontal rules (---).
  - Exactly one blank line between section entries (** blocks).
  - No trailing spaces on any line.

════════════════════════════════════════════════════
CONTENT IMPROVEMENT RULES — APPLY AGGRESSIVELY
════════════════════════════════════════════════════

  a. Replace weak/passive verbs with strong action verbs:
      "was responsible for" → "owned" / "led" / "drove"
      "helped with" → "contributed to" / "collaborated on"
      "worked on" → "engineered" / "built" / "delivered"
      "managed" → "directed" / "spearheaded" / "oversaw"
  b. Weave in job description keywords naturally into existing bullets.
  c. Make bullets punchier: remove filler, cut passive voice, compress fluff.
  d. Fix grammar errors.
  e. Do NOT add new bullet points, new sections, or invent facts/metrics.
  f. Do NOT delete any existing bullet point or section.
  g. Do NOT change job titles, company names, dates, or degrees.
  h. Do NOT introduce new skills/tools/technologies/languages/education items that were not present in the input section. Rephrase only.
  i. Do NOT add placeholder headers or contact blocks. Never add new sections or headings.

════════════════════════════════════════════════════
OUTPUT FORMAT
════════════════════════════════════════════════════

Return ONLY a valid JSON object — no explanation outside it:
  {
    "improved_markdown": "<full improved section as a single string>",
    "changes_summary": ["<change 1>", "<change 2>", ...]
  }
  - improved_markdown: complete section text with all formatting + content fixes applied.
  - changes_summary: 1 to 5 concrete descriptions of what changed.
  - No markdown fences inside JSON string values.
""".strip()


@dataclass
class _Section:
    """A single ## block (or the header block above the first ##)."""
    heading: str        # e.g. "## Experience" or "" for the header block
    content: str        # the raw markdown text of this section (heading included)


class MarkdownRewriteAgent(BaseAgent[MarkdownRewriteInput, MarkdownRewriteOutput]):
    """Rewrites CV Markdown section-by-section to avoid LLM token/timeout limits."""

    meta = AgentMeta(name="MarkdownRewriteAgent", version="3.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def execute(self, input: MarkdownRewriteInput) -> MarkdownRewriteOutput:  # noqa: A002
        logger.info("markdown_rewrite.start", job=input.job_title)

        sections = self._split_sections(input.original_markdown)
        logger.info("markdown_rewrite.sections_found", count=len(sections))

        # Build a set of canonical ## headings from the *original* document so
        # the normaliser can restore any heading level the LLM degrades.
        original_headings: set[str] = {
            s.heading.lstrip("#").strip()
            for s in sections
            if s.heading.startswith("## ")
        }

        improved_parts: list[str] = []
        all_changes: list[str] = []

        for idx, section in enumerate(sections):
            improved_text, changes = self._rewrite_section(section, input, idx)
            improved_parts.append(improved_text)
            all_changes.extend(changes)

        raw_markdown = "\n\n".join(p.strip() for p in improved_parts if p.strip())
        improved_markdown = self._normalise(raw_markdown, original_headings)

        logger.info(
            "markdown_rewrite.success",
            sections=len(sections),
            total_changes=len(all_changes),
        )
        return MarkdownRewriteOutput(
            improved_markdown=improved_markdown,
            changes_summary=all_changes,
        )

    # ------------------------------------------------------------------
    # Section splitting
    # ------------------------------------------------------------------

    @staticmethod
    def _split_sections(markdown: str) -> list[_Section]:
        """Split markdown into sections at every ## boundary.

        The block before the first ## (name + contact) is treated as its own
        section with an empty heading so it's still sent for light cleanup.
        """
        sections: list[_Section] = []
        current_lines: list[str] = []
        current_heading = ""

        for line in markdown.splitlines():
            if line.startswith("## "):
                # Save the previous section
                if current_lines:
                    sections.append(
                        _Section(
                            heading=current_heading,
                            content="\n".join(current_lines),
                        )
                    )
                current_heading = line
                current_lines = [line]
            else:
                current_lines.append(line)

        # Flush the last section
        if current_lines:
            sections.append(
                _Section(
                    heading=current_heading,
                    content="\n".join(current_lines),
                )
            )

        return sections

    # ------------------------------------------------------------------
    # Per-section rewrite
    # ------------------------------------------------------------------

    def _rewrite_section(
        self,
        section: _Section,
        inp: MarkdownRewriteInput,
        idx: int,
    ) -> tuple[str, list[str]]:
        """Rewrite a single section; returns (improved_text, changes_list)."""
        label = section.heading or "Header / Contact"
        logger.info("markdown_rewrite.section_start", idx=idx, section=label)

        user_prompt = self._build_section_prompt(section, inp)
        last_error: Exception | None = None

        for attempt in range(_MAX_RETRIES + 1):
            try:
                raw = self._call_llm(user_prompt)
                improved, changes = self._parse_section(raw)
                logger.info(
                    "markdown_rewrite.section_done",
                    idx=idx,
                    section=label,
                    changes=len(changes),
                    attempt=attempt,
                )
                return improved, changes
            except AgentExecutionError as exc:
                last_error = exc
                logger.warning(
                    "markdown_rewrite.section_retry",
                    idx=idx,
                    section=label,
                    attempt=attempt,
                    error=str(exc),
                )

        # If all retries fail for this section, fall back to the original text
        logger.error(
            "markdown_rewrite.section_fallback",
            idx=idx,
            section=label,
            error=str(last_error),
        )
        return section.content, []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_section_prompt(self, section: _Section, inp: MarkdownRewriteInput) -> str:
        parts = [
            "=== TARGET JOB ===",
            f"Title: {inp.job_title}" if inp.job_title else "(no job title provided)",
        ]

        if inp.job_description:
            jd = inp.job_description[:1500]
            parts += ["", "Job Description (excerpt):", jd]

        if inp.gap_analysis:
            parts += ["", "=== GAP ANALYSIS (reference only) ===", inp.gap_analysis[:800]]

        parts += [
            "",
            "=== CV SECTION TO IMPROVE ===",
            section.content,
        ]
        return "\n".join(parts)

    def _call_llm(self, user_prompt: str) -> str:
        try:
            return self._llm.complete(system=_SYSTEM_PROMPT, user=user_prompt)
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, f"LLM call failed: {exc}") from exc

    def _parse_section(self, raw: str) -> tuple[str, list[str]]:
        """Parse LLM JSON output for a single section."""
        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)
        try:
            data = json.loads(text)
            return data["improved_markdown"], data.get("changes_summary", [])
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, f"Parse failed: {exc}") from exc

    # ------------------------------------------------------------------
    # Post-processing normaliser — deterministic, no LLM involved
    # ------------------------------------------------------------------

    # Date line pattern: "Month YYYY - Month YYYY  |  City" or "Month YYYY - Present  |  City"
    _DATE_LINE_RE = re.compile(
        r"^[A-Z]+\s+\d{4}\s*\W\s*(?:[A-Z]+\s+\d{4}|Present)\s*\|.*$",
        re.IGNORECASE,
    )

    @classmethod
    def _normalise(cls, markdown: str, original_section_headings: set[str]) -> str:
        """Deterministically fix every known LLM formatting mistake.

        Fixes applied (in order):
          1. Restore ## level for section headings the LLM promoted to #.
             2. Force entry heading lines to be bold (i.e. **Role | Company**) if the LLM promoted them to ## or #.
             3. Drop any extra H1 heading or ## section that was not present in the original document.
             4. Strip floating bold degree lines (e.g. **Bachelor's Degree in Finance**)
                 that should be part of the following entry heading — merge them.
             5. Remove duplicate date lines that appear directly after an entry heading.
             6. Collapse 3+ consecutive blank lines down to a single blank line.
             7. Strip trailing whitespace from every line.
        """
        lines = markdown.splitlines()
        lines = cls._fix_heading_levels(lines, original_section_headings)
        lines = cls._drop_unrecognized_sections(lines, original_section_headings)
        lines = cls._merge_floating_degree_lines(lines)
        lines = cls._remove_duplicate_date_lines(lines)
        lines = cls._collapse_blank_lines(lines)
        lines = [ln.rstrip() for ln in lines]
        return "\n".join(lines)

    # -- 1 & 2: heading level restoration ------------------------------------

    @classmethod
    def _fix_heading_levels(
        cls,
        lines: list[str],
        original_section_headings: set[str],
    ) -> list[str]:
        """Restore ## heading levels that the LLM incorrectly promoted.

        Rules:
          - Any heading whose text matches a known ## section (PROFESSIONAL
            EXPERIENCE, EDUCATION, TECHNICAL SKILLS, LANGUAGES, etc.) must be ##.
          - Any heading that contains " | " and is NOT a known ## section is an
            entry sub-heading (Role | Company) and must be bolded (e.g., **Role | Company**).
          - The very first # heading (candidate name) is left as-is.
        """
        result: list[str] = []
        name_heading_seen = False

        for line in lines:
            stripped = line.lstrip("#").strip()

            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))

                # Always protect the name heading (first # line)
                if level == 1 and not name_heading_seen and "|" not in line:
                    name_heading_seen = True
                    result.append(line)
                    continue

                # Known ## section heading — force to ##
                if stripped.upper() in {h.upper() for h in original_section_headings}:
                    result.append(f"## {stripped}")
                    continue

                # Entry heading (contains " | ") — force to **...**
                if "|" in stripped:
                    result.append(f"**{stripped}**")
                    continue

                # Anything else that was ## stays ##; anything deeper stays as-is
                result.append(line)
            else:
                result.append(line)

        return result

    # -- 3: drop hallucinated sections/headings ------------------------------

    @classmethod
    def _drop_unrecognized_sections(
        cls, lines: list[str], original_section_headings: set[str]
    ) -> list[str]:
        """Remove any extra H1/## sections that were not in the original document.

        - Keep only the first H1; drop any additional H1 headings and their blocks.
        - Keep only ## headings whose text matches original_section_headings (case-insensitive).
        - Preserve all non-heading content under kept sections.
        """
        keep: list[str] = []
        seen_h1 = False
        allowed_h2 = {h.upper() for h in original_section_headings}
        i = 0

        while i < len(lines):
            line = lines[i]

            if line.startswith("# "):
                if seen_h1:
                    # Skip duplicate H1 block until next heading
                    i += 1
                    while i < len(lines) and not lines[i].startswith("#"):
                        i += 1
                    continue
                seen_h1 = True
                keep.append(line)
                i += 1
                continue

            if line.startswith("## "):
                heading = line[3:].strip()
                if heading.upper() not in allowed_h2:
                    # Skip unknown section block until next heading
                    i += 1
                    while i < len(lines) and not lines[i].startswith("## ") and not lines[i].startswith("# "):
                        i += 1
                    continue

            keep.append(line)
            i += 1

        return keep

    # -- 3: floating bold degree lines ---------------------------------------

    @classmethod
    def _merge_floating_degree_lines(cls, lines: list[str]) -> list[str]:
        """Remove standalone **Degree Name** lines that float before an entry heading.

        The LLM sometimes emits:
            **Bachelor's Degree in Finance**
            (blank line)
            **IHEC Carthage  |  ...**

        We drop the bold line because the degree title already lives inside the
        entry heading or is redundant — it confuses ATS parsers.
        """
        result: list[str] = []
        i = 0
        # Matches lines that are ONLY a bold phrase, no other content.
        bold_only = re.compile(r"^\*\*[^*]+\*\*\s*$")

        while i < len(lines):
            line = lines[i]
            if bold_only.match(line):
                # Look ahead (skip blanks) to see if next real line is an entry heading
                j = i + 1
                while j < len(lines) and lines[j].strip() == "":
                    j += 1
                if j < len(lines) and " | " in lines[j] and bold_only.match(lines[j]):
                    # Drop the bold line (and any blank lines between it and entry heading)
                    i = j
                    continue
            result.append(line)
            i += 1

        return result

    # -- 4: duplicate date lines ---------------------------------------------

    @classmethod
    def _remove_duplicate_date_lines(cls, lines: list[str]) -> list[str]:
        """Remove a duplicate date/location line that appears right after an entry heading.

        The LLM sometimes outputs:
            **ESPRIT School of Business  |  September 2024 - Present  |  Tunis, Tunisia**
            September 2024 - Present  |  Tunis, Tunisia      ← duplicate

        We drop the second occurrence when it immediately follows (within 1 blank
        line) an entry heading that already contains the same date information.
        """
        result: list[str] = []
        i = 0
        
        bold_only = re.compile(r"^\*\*[^*]+\*\*\s*$")

        while i < len(lines):
            line = lines[i]
            result.append(line)

            # After an entry heading, skip any immediately following duplicate date line
            if " | " in line and bold_only.match(line):
                heading_text = line.strip("* ")
                j = i + 1
                # Allow at most one blank line between heading and date line
                if j < len(lines) and lines[j].strip() == "":
                    j += 1
                if j < len(lines) and cls._DATE_LINE_RE.match(lines[j].strip()):
                    date_candidate = lines[j].strip()
                    # Check if this date info is already embedded in the entry heading
                    if any(part.strip() in heading_text for part in date_candidate.split("|")):
                        i = j + 1  # skip the duplicate
                        continue

            i += 1

        return result

    # -- 5: collapse blank lines ---------------------------------------------

    @staticmethod
    def _collapse_blank_lines(lines: list[str]) -> list[str]:
        """Collapse runs of 2+ consecutive blank lines into a single blank line."""
        result: list[str] = []
        prev_blank = False
        for line in lines:
            is_blank = line.strip() == ""
            if is_blank and prev_blank:
                continue
            result.append(line)
            prev_blank = is_blank
        return result
