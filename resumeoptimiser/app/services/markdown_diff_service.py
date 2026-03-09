"""MarkdownDiffService – generates a human-readable line-by-line diff.

Uses Python's stdlib difflib only — no LLM involved.

The diff format uses:
  '- <line>'  removed / original line
  '+ <line>'  added   / improved line
  '  <line>'  unchanged context line

This is the canonical representation for the frontend diff viewer.
"""

from __future__ import annotations

import difflib
import unicodedata

from app.core.logging import get_logger
from app.schemas.markdown import MarkdownDiffInput, MarkdownDiffOutput

logger = get_logger(__name__)

# Number of context lines shown around each change block
_CONTEXT_LINES = 3

# Unicode characters that are visually identical to ASCII hyphen but differ in codepoint.
# The LLM sometimes "improves" hyphens to these — we treat them as the same character.
_HYPHEN_EQUIVALENTS = str.maketrans({
    "\u2010": "-",  # hyphen
    "\u2011": "-",  # non-breaking hyphen
    "\u2012": "-",  # figure dash
    "\u2013": "-",  # en dash (–)
    "\u2014": "-",  # em dash (—)
    "\u2212": "-",  # minus sign
})


def _normalize_line(line: str) -> str:
    """Normalize a line for comparison purposes only (not for display).

    - Replace visually-equivalent Unicode hyphens/dashes with ASCII hyphen.
    - Collapse multiple spaces to one.
    - Strip trailing whitespace.
    This ensures the diff only flags genuine wording changes.
    """
    line = line.translate(_HYPHEN_EQUIVALENTS)
    line = unicodedata.normalize("NFKC", line)
    return " ".join(line.split())


class MarkdownDiffService:
    """Pure-Python service: computes the diff between original and improved Markdown."""

    def compute(self, input: MarkdownDiffInput) -> MarkdownDiffOutput:  # noqa: A002
        original_lines = input.original_markdown.splitlines()
        improved_lines = input.improved_markdown.splitlines()

        # Compute the diff on normalized lines (for deciding what changed),
        # but display the actual improved lines so the user sees the real text.
        norm_original = [_normalize_line(l) for l in original_lines]
        norm_improved = [_normalize_line(l) for l in improved_lines]

        # Build a mapping from normalized improved index → original display line
        # We use SequenceMatcher on the normalized versions, then emit display lines.
        matcher = difflib.SequenceMatcher(None, norm_original, norm_improved, autojunk=False)

        diff_lines: list[str] = [
            "--- original_cv.md",
            "+++ improved_cv.md",
        ]
        change_count = 0

        for group in matcher.get_grouped_opcodes(_CONTEXT_LINES):
            # Emit hunk header
            first, last = group[0], group[-1]
            i1, i2, j1, j2 = first[1], last[2], first[3], last[4]
            diff_lines.append(f"@@ -{i1+1},{i2-i1} +{j1+1},{j2-j1} @@")

            for tag, i1, i2, j1, j2 in group:
                if tag == "equal":
                    for line in original_lines[i1:i2]:
                        diff_lines.append(f"  {line}")
                elif tag == "replace":
                    for line in original_lines[i1:i2]:
                        diff_lines.append(f"- {line}")
                        change_count += 1
                    for line in improved_lines[j1:j2]:
                        diff_lines.append(f"+ {line}")
                        change_count += 1
                elif tag == "delete":
                    for line in original_lines[i1:i2]:
                        diff_lines.append(f"- {line}")
                        change_count += 1
                elif tag == "insert":
                    for line in improved_lines[j1:j2]:
                        diff_lines.append(f"+ {line}")
                        change_count += 1

        logger.info("markdown_diff.computed", change_lines=change_count)
        return MarkdownDiffOutput(diff_lines=diff_lines, change_count=change_count)
