/**
 * layout_primitives.ts
 *
 * Responsibility: low-level rendering primitives.
 *
 * Rules:
 *  - Every function is a pure side-effect on `RenderCursor` + `jsPDF`.
 *  - No business logic.
 *  - No font choices — callers set the font via font_registry before calling.
 *  - No spacing magic — all gaps come from layout_tokens.
 *  - Page breaks are explicit and predictable.
 */

import type jsPDF from 'jspdf';
import {
  MARGIN_X_MM,
  MARGIN_Y_MM,
  PAGE_W_MM,
  PAGE_H_MM,
  MAX_Y_MM,
  FOOTER_H_MM,
  CONTENT_W_MM,
  lineHeight,
  type RGBColor,
} from './layout_tokens';

// ---------------------------------------------------------------------------
// Render cursor
// ---------------------------------------------------------------------------

/**
 * Mutable cursor that tracks the current Y position across pages.
 * All primitives advance `cursor.y` deterministically.
 */
export interface RenderCursor {
  doc: jsPDF;
  y: number;
}

export function createCursor(doc: jsPDF): RenderCursor {
  return { doc, y: MARGIN_Y_MM };
}

// ---------------------------------------------------------------------------
// Page management
// ---------------------------------------------------------------------------

/** Add a new page and reset the cursor to the top margin. */
export function addPage(cursor: RenderCursor): void {
  cursor.doc.addPage();
  cursor.y = MARGIN_Y_MM;
}

/**
 * Ensure `neededMm` of space is available below the current cursor position.
 * If not, adds a new page.
 */
export function ensureSpace(cursor: RenderCursor, neededMm: number): void {
  if (cursor.y + neededMm > MAX_Y_MM) {
    addPage(cursor);
  }
}

// ---------------------------------------------------------------------------
// Text block
// ---------------------------------------------------------------------------

/**
 * Render a block of wrapped text at the current cursor position.
 *
 * - Caller is responsible for setting the font (via applyFont) before calling.
 * - fontSize is set here; color is set here.
 * - Advances cursor.y by the total rendered height.
 */
export function putText(
  cursor: RenderCursor,
  text: string,
  x: number,
  maxW: number,
  fontSizePt: number,
  color: RGBColor,
  leading: number,
): void {
  const trimmed = text.trim();
  if (!trimmed) return;

  cursor.doc.setFontSize(fontSizePt);
  cursor.doc.setTextColor(...color);

  const lh = lineHeight(fontSizePt, leading);
  const lines: string[] = cursor.doc.splitTextToSize(trimmed, maxW);

  for (const line of lines) {
    ensureSpace(cursor, lh);
    cursor.doc.text(line, x, cursor.y);
    cursor.y += lh;
  }
}

// ---------------------------------------------------------------------------
// Rule (horizontal divider)
// ---------------------------------------------------------------------------

/**
 * Draw a full-width horizontal rule at the current cursor position,
 * then advance the cursor by `gapAfterMm`.
 */
export function drawRule(
  cursor: RenderCursor,
  color: RGBColor,
  weightMm: number,
  gapAfterMm: number,
): void {
  cursor.doc.setDrawColor(...color);
  cursor.doc.setLineWidth(weightMm);
  cursor.doc.line(MARGIN_X_MM, cursor.y, PAGE_W_MM - MARGIN_X_MM, cursor.y);
  cursor.y += gapAfterMm;
}

// ---------------------------------------------------------------------------
// Spacing block
// ---------------------------------------------------------------------------

/**
 * Advance cursor by a fixed number of mm without emitting any content.
 * Always use a named token from layout_tokens — never a raw literal here.
 */
export function addSpacing(cursor: RenderCursor, mm: number): void {
  cursor.y += mm;
}

// ---------------------------------------------------------------------------
// Footer batch renderer
// ---------------------------------------------------------------------------

/**
 * Render page-number footers on every page of the document.
 * Must be called AFTER all content pages have been written.
 */
export function renderFooters(
  doc: jsPDF,
  fontSizePt: number,
  color: RGBColor,
  label: string,
): void {
  const total = doc.getNumberOfPages();
  for (let p = 1; p <= total; p++) {
    doc.setPage(p);
    doc.setFontSize(fontSizePt);
    doc.setTextColor(...color);
    doc.text(
      `${label}  ·  Page ${p} / ${total}`,
      PAGE_W_MM / 2,
      PAGE_H_MM - FOOTER_H_MM / 2,
      { align: 'center' },
    );
  }
}

// ---------------------------------------------------------------------------
// Experience item parser
// ---------------------------------------------------------------------------

export interface ParsedExperienceItem {
  header: string;
  body: string;
}

/**
 * Split "Title, Company (dates): description" on the first colon.
 * Returns null if the colon is absent or in an implausible position.
 *
 * Upper bound is raised to 200 to accommodate long job titles with dates
 * such as "Corporate Banking Officer, STB BANK (Jan/2026 – Present)".
 * Pure function – no side effects.
 */
export function parseExperienceItem(item: string): ParsedExperienceItem | null {
  const colonIdx = item.indexOf(':');
  if (colonIdx < 5 || colonIdx > 200) return null;
  const header = item.slice(0, colonIdx).trim();
  const body   = item.slice(colonIdx + 1).trim();
  return body ? { header, body } : null;
}

// ---------------------------------------------------------------------------
// Filler-text guard
// ---------------------------------------------------------------------------

/**
 * Returns true when the raw text is effectively empty or a known filler phrase
 * that should not be rendered.
 */
export function isFiller(rawText: string): boolean {
  const t = rawText.trim();
  return (
    t.length < 20 ||
    /^(relevant|experience highlight|see items|n\/a)/i.test(t)
  );
}

// ---------------------------------------------------------------------------
// Content-width helpers
// ---------------------------------------------------------------------------

export function indentedX(offsetMm: number): number {
  return MARGIN_X_MM + offsetMm;
}

export function indentedW(offsetMm: number): number {
  return CONTENT_W_MM - offsetMm;
}
