/**
 * pdf_renderer.ts
 *
 * Responsibility: pure rendering of a CVDocument to a jsPDF instance.
 *
 * Rules:
 *  - Does NOT mutate CV data.
 *  - Does NOT recalculate business logic.
 *  - Does NOT inject optimization decisions.
 *  - Every font switch goes through font_registry.applyFont.
 *  - Every spacing value comes from layout_tokens.
 *  - Rendering is deterministic: same input → same output.
 */

import jsPDF from 'jspdf';
import type { CVSection } from '../../types/pipeline';
import { initFonts, applyFont, FONT_BODY, FONT_HEADING } from './font_registry';
import {
  MARGIN_X_MM,
  CONTENT_W_MM,
  FONT_SIZE_NAME,
  FONT_SIZE_CONTACT,
  FONT_SIZE_SECTION,
  FONT_SIZE_BODY,
  FONT_SIZE_BULLET,
  FONT_SIZE_ENTRY,
  FONT_SIZE_FOOTER,
  LEADING_TIGHT,
  LEADING_NORMAL,
  LEADING_RELAXED,
  LEADING_LOOSE,
  INDENT_BULLET,
  INDENT_BODY,
  COLOR_BLACK,
  COLOR_ACCENT,
  COLOR_MUTED,
  COLOR_RULE,
  RULE_WEIGHT_LIGHT,
  RULE_WEIGHT_HEAVY,
  RULE_GAP_AFTER_MM,
  SPACING_XS,
  SPACING_SM,
  SPACING_MD,
  SPACING_LG,
  SPACING_XL,
  getSectionLabel,
  lineHeight,
} from './layout_tokens';
import {
  createCursor,
  ensureSpace,
  putText,
  drawRule,
  addSpacing,
  renderFooters,
  parseExperienceItem,
  isFiller,
  indentedX,
  indentedW,
  type RenderCursor,
} from './layout_primitives';
import type { CVDocument } from './cv_document';

// ---------------------------------------------------------------------------
// Header
// ---------------------------------------------------------------------------

function renderHeader(cursor: RenderCursor, doc: CVDocument): void {
  const { contact } = doc;

  applyFont(cursor.doc, FONT_HEADING, 'bold');
  putText(
    cursor,
    (contact.name || 'Candidate').toUpperCase(),
    MARGIN_X_MM,
    CONTENT_W_MM,
    FONT_SIZE_NAME,
    COLOR_BLACK,
    LEADING_TIGHT,
  );

  addSpacing(cursor, SPACING_XS);

  const parts = [
    contact.email,
    contact.phone,
    contact.location,
    contact.linkedin,
    contact.github,
  ].filter(Boolean);

  if (parts.length > 0) {
    applyFont(cursor.doc, FONT_BODY, 'normal');
    putText(
      cursor,
      parts.join('   |   '),
      MARGIN_X_MM,
      CONTENT_W_MM,
      FONT_SIZE_CONTACT,
      COLOR_MUTED,
      LEADING_NORMAL,
    );
  }

  addSpacing(cursor, SPACING_SM);
  drawRule(cursor, COLOR_ACCENT, RULE_WEIGHT_HEAVY, SPACING_XL);
}

// ---------------------------------------------------------------------------
// Section heading
// ---------------------------------------------------------------------------

function renderSectionHeading(cursor: RenderCursor, sectionType: string): void {
  const label = getSectionLabel(sectionType);
  const headingH = lineHeight(FONT_SIZE_SECTION, LEADING_TIGHT)
    + RULE_GAP_AFTER_MM
    + lineHeight(FONT_SIZE_BODY, LEADING_LOOSE);

  ensureSpace(cursor, headingH);

  applyFont(cursor.doc, FONT_HEADING, 'bold');
  putText(
    cursor,
    label.toUpperCase(),
    MARGIN_X_MM,
    CONTENT_W_MM,
    FONT_SIZE_SECTION,
    COLOR_ACCENT,
    LEADING_TIGHT,
  );

  drawRule(cursor, COLOR_RULE, RULE_WEIGHT_LIGHT, RULE_GAP_AFTER_MM);
}

// ---------------------------------------------------------------------------
// Experience section
// ---------------------------------------------------------------------------

function renderExperienceItem(
  cursor: RenderCursor,
  item: string,
  sectionType: string,
): void {
  const parsed = parseExperienceItem(item);

  if (parsed) {
    ensureSpace(cursor, lineHeight(FONT_SIZE_ENTRY, LEADING_RELAXED) + SPACING_SM);
    applyFont(cursor.doc, FONT_BODY, 'bold');
    putText(
      cursor,
      parsed.header,
      MARGIN_X_MM,
      CONTENT_W_MM,
      FONT_SIZE_ENTRY,
      COLOR_BLACK,
      LEADING_RELAXED,
    );
    applyFont(cursor.doc, FONT_BODY, 'normal');
    putText(
      cursor,
      parsed.body,
      indentedX(INDENT_BODY),
      indentedW(INDENT_BODY),
      FONT_SIZE_BULLET,
      COLOR_BLACK,
      LEADING_RELAXED,
    );
    addSpacing(cursor, SPACING_MD);
  } else if (sectionType === 'education') {
    // Education items without a colon are degree / institution lines — bold, no bullet.
    ensureSpace(cursor, lineHeight(FONT_SIZE_ENTRY, LEADING_RELAXED));
    applyFont(cursor.doc, FONT_BODY, 'bold');
    putText(
      cursor,
      item,
      MARGIN_X_MM,
      CONTENT_W_MM,
      FONT_SIZE_ENTRY,
      COLOR_BLACK,
      LEADING_RELAXED,
    );
    addSpacing(cursor, SPACING_SM);
  } else {
    applyFont(cursor.doc, FONT_BODY, 'normal');
    putText(
      cursor,
      `• ${item}`,
      indentedX(INDENT_BULLET),
      indentedW(INDENT_BULLET),
      FONT_SIZE_BULLET,
      COLOR_BLACK,
      LEADING_RELAXED,
    );
    addSpacing(cursor, SPACING_SM);
  }
}

function renderExperienceSection(cursor: RenderCursor, section: CVSection): void {
  // Items are the canonical structured form — render them exclusively when present.
  if (section.items.length > 0) {
    for (const item of section.items) {
      renderExperienceItem(cursor, item, section.section_type);
    }
    return;
  }

  // No items — render raw_text as a prose block.
  if (section.raw_text.trim()) {
    applyFont(cursor.doc, FONT_BODY, 'normal');
    putText(
      cursor,
      section.raw_text.trim(),
      MARGIN_X_MM,
      CONTENT_W_MM,
      FONT_SIZE_BODY,
      COLOR_BLACK,
      LEADING_LOOSE,
    );
  }
}

// ---------------------------------------------------------------------------
// Generic section
// ---------------------------------------------------------------------------

function renderGenericSection(cursor: RenderCursor, section: CVSection): void {
  // If structured items exist they ARE the canonical content — never render raw_text
  // alongside items; that causes the prose paragraph + bullet list duplication seen
  // in the PDF output.
  if (section.items.length > 0) {
    applyFont(cursor.doc, FONT_BODY, 'normal');
    for (const item of section.items) {
      putText(
        cursor,
        `• ${item}`,
        indentedX(INDENT_BULLET),
        indentedW(INDENT_BULLET),
        FONT_SIZE_BULLET,
        COLOR_BLACK,
        LEADING_RELAXED,
      );
      addSpacing(cursor, SPACING_XS);
    }
    return;
  }

  // No items — fall back to raw_text, but skip filler.
  const rawClean = section.raw_text.trim();
  if (rawClean && !isFiller(rawClean)) {
    applyFont(cursor.doc, FONT_BODY, 'normal');
    putText(
      cursor,
      rawClean,
      MARGIN_X_MM,
      CONTENT_W_MM,
      FONT_SIZE_BODY,
      COLOR_BLACK,
      LEADING_LOOSE,
    );
  }
}

// ---------------------------------------------------------------------------
// Public render entry point
// ---------------------------------------------------------------------------

/**
 * Render `document` to a new jsPDF instance and return it.
 *
 * - Deterministic: identical inputs produce identical output.
 * - Does NOT call doc.save() — caller decides what to do with the PDF blob.
 */
export function renderCVToPdf(document: CVDocument): jsPDF {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

  initFonts(doc);

  const cursor = createCursor(doc);

  renderHeader(cursor, document);

  for (const section of document.sections) {
    renderSectionHeading(cursor, section.section_type);

    const usesEntryFormat =
      section.section_type === 'experience' || section.section_type === 'education';

    if (usesEntryFormat) {
      renderExperienceSection(cursor, section);
    } else {
      renderGenericSection(cursor, section);
    }

    addSpacing(cursor, SPACING_LG);
  }

  renderFooters(doc, FONT_SIZE_FOOTER, COLOR_MUTED, 'CV Optima');

  return doc;
}
