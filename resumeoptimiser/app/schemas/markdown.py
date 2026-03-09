"""Pydantic schemas for Markdown-based pipeline stages."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MarkdownInput(BaseModel):
    """Input for OCRToMarkdownAgent: raw text from PDF/OCR."""

    raw_text: str = Field(min_length=10, description="Raw text extracted from the CV file.")


class MarkdownOutput(BaseModel):
    """Clean structured Markdown produced by OCRToMarkdownAgent.

    This is the canonical 'original_cv.md' – never mutated downstream.
    """

    markdown: str = Field(description="Clean structured Markdown preserving original content.")


class MarkdownRewriteInput(BaseModel):
    """Input for MarkdownRewriteAgent."""

    original_markdown: str = Field(description="original_cv.md – the immutable source.")
    job_title: str = Field(default="", description="Target job title.")
    job_description: str = Field(default="", description="Raw job description text.")
    gap_analysis: str = Field(default="", description="Gap analysis summary from the explainer.")


class MarkdownRewriteOutput(BaseModel):
    """Output of MarkdownRewriteAgent – improved_cv.md."""

    improved_markdown: str = Field(description="Wording-improved Markdown (structure preserved).")
    changes_summary: list[str] = Field(
        default_factory=list,
        description="Human-readable list of changes made (3–8 items).",
    )


class MarkdownDiffInput(BaseModel):
    """Input for the diff computation."""

    original_markdown: str
    improved_markdown: str


class MarkdownDiffOutput(BaseModel):
    """Unified diff result."""

    diff_lines: list[str] = Field(
        description="Line-by-line diff in unified format: '- removed', '+ added', '  context'."
    )
    change_count: int = Field(description="Number of changed lines (added + removed).")


class MarkdownToPdfInput(BaseModel):
    """Input for the Markdown → PDF renderer."""

    markdown: str = Field(description="Markdown to render into PDF.")
    candidate_name: str = Field(default="CV", description="Used for the PDF filename hint.")
