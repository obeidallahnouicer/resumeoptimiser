"""MarkdownPDFRenderer – converts Markdown → HTML → PDF via a fixed template.

DESIGN PRINCIPLE:
  The layout (typography, spacing, colours, columns) is defined ENTIRELY
  in the Jinja2 HTML template and the embedded CSS. The Markdown provides
  ONLY content — it never controls layout.

  This ensures the PDF looks identical regardless of what the LLM wrote,
  because the LLM output flows into pre-defined slots in the template.

Dependencies (must be installed):
  pip install markdown weasyprint jinja2

Usage:
  renderer = MarkdownPDFRenderer()
  pdf_bytes = renderer.render(markdown_text, candidate_name="Jane Doe")
"""

from __future__ import annotations

import io

from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Fixed CSS template – layout is NEVER derived from LLM output
# ---------------------------------------------------------------------------

_CV_CSS = """\
@page {
  size: A4;
  margin: 18mm 20mm 18mm 20mm;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: "Helvetica Neue", Arial, sans-serif;
  font-size: 9.5pt;
  line-height: 1.5;
  color: #1a1a1a;
  background: #ffffff;
}

/* ── Candidate name (h1) ───────────────────────────────────────────────── */
h1 {
  font-size: 20pt;
  font-weight: 700;
  color: #0d1b2a;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
  border-bottom: 2.5px solid #1a73e8;
  padding-bottom: 6px;
}

/* Contact line – the paragraph immediately after h1 */
h1 + p {
  font-size: 8.5pt;
  color: #555555;
  margin-bottom: 14px;
}

/* ── Section headings (h2) ─────────────────────────────────────────────── */
h2 {
  font-size: 10pt;
  font-weight: 700;
  color: #1a73e8;
  text-transform: uppercase;
  letter-spacing: 1px;
  border-bottom: 1px solid #dce8fb;
  padding-bottom: 3px;
  margin-top: 14px;
  margin-bottom: 6px;
}

/* ── Sub-headings: company / role / institution (h3) ───────────────────── */
h3 {
  font-size: 9.5pt;
  font-weight: 600;
  color: #0d1b2a;
  margin-top: 8px;
  margin-bottom: 1px;
}

/* Italic dates / sub-info */
em {
  font-size: 8.5pt;
  color: #666666;
  font-style: italic;
}

/* ── Paragraphs ─────────────────────────────────────────────────────────── */
p {
  margin-bottom: 4px;
}

/* ── Bullet lists ───────────────────────────────────────────────────────── */
ul {
  margin: 2px 0 6px 18px;
  padding: 0;
}

li {
  margin-bottom: 2px;
  font-size: 9pt;
}

/* ── Strong / Bold ─────────────────────────────────────────────────────── */
strong {
  font-weight: 600;
  color: #0d1b2a;
}

/* ── Horizontal rule (section separator) ───────────────────────────────── */
hr {
  border: none;
  border-top: 1px solid #e0e0e0;
  margin: 10px 0;
}

/* ── Page break helpers ─────────────────────────────────────────────────── */
h2, h3 { page-break-after: avoid; }
ul     { page-break-inside: avoid; }
"""

# ---------------------------------------------------------------------------
# Jinja2 HTML template skeleton
# ---------------------------------------------------------------------------

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
  <meta charset="utf-8">
  <title>{{ title }}</title>
  <style>
{{ css }}
  </style>
</head>
<body>
{{ body }}
</body>
</html>
"""


class MarkdownPDFRenderer:
    """Renders Markdown → HTML (fixed template) → PDF bytes."""

    def render(self, markdown_text: str, candidate_name: str = "CV", lang: str = "en") -> bytes:
        """Convert Markdown to PDF bytes.

        Args:
            markdown_text: The improved_cv.md content.
            candidate_name: Used as the document <title>.
            lang: HTML lang attribute (e.g. "en", "fr").

        Returns:
            PDF file contents as bytes.
        """
        html_body = self._markdown_to_html(markdown_text)
        full_html = self._build_html(html_body, title=candidate_name, lang=lang)
        return self._html_to_pdf(full_html)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _markdown_to_html(markdown_text: str) -> str:
        """Convert Markdown to HTML fragment using the `markdown` library."""
        try:
            import markdown as md_lib  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "The 'markdown' package is required: pip install markdown"
            ) from exc

        html = md_lib.markdown(
            markdown_text,
            extensions=["extra", "nl2br"],  # tables, definition lists, line-breaks
        )
        return html

    @staticmethod
    def _build_html(body_html: str, title: str, lang: str) -> str:
        """Inject body HTML into the fixed template."""
        try:
            from jinja2 import Template  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "The 'jinja2' package is required: pip install jinja2"
            ) from exc

        tmpl = Template(_HTML_TEMPLATE)
        return tmpl.render(body=body_html, css=_CV_CSS, title=title, lang=lang)

    @staticmethod
    def _html_to_pdf(html: str) -> bytes:
        """Render full HTML to PDF bytes using WeasyPrint."""
        try:
            from weasyprint import HTML  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "The 'weasyprint' package is required: pip install weasyprint"
            ) from exc

        buffer = io.BytesIO()
        HTML(string=html).write_pdf(buffer)
        return buffer.getvalue()
