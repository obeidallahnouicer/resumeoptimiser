/**
 * font_registry.ts
 *
 * Responsibility: font loading, registration, and validation.
 *
 * Rules:
 *  - Fonts are registered ONCE at initialisation via `initFonts`.
 *  - Every font variant used by the renderer must be declared here.
 *  - If a font fails to load → throw FontLoadError (never silently fallback).
 *  - No system fonts. All variants are explicit.
 */

import type jsPDF from 'jspdf';

// ---------------------------------------------------------------------------
// Font variant identifiers
// ---------------------------------------------------------------------------

export const FONT_HEADING = 'helvetica' as const;
export const FONT_BODY    = 'helvetica' as const;

export type FontStyle = 'normal' | 'bold' | 'italic' | 'bolditalic';

export interface FontSpec {
  family: string;
  style: FontStyle;
}

/** All font variants the renderer is allowed to use. */
export const FONT_VARIANTS: ReadonlyArray<FontSpec> = [
  { family: FONT_HEADING, style: 'bold' },
  { family: FONT_BODY,    style: 'normal' },
  { family: FONT_BODY,    style: 'italic' },
  { family: FONT_BODY,    style: 'bolditalic' },
] as const;

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class FontLoadError extends Error {
  constructor(family: string, style: FontStyle, reason: string) {
    super(`[FontRegistry] Failed to load font "${family}" (${style}): ${reason}`);
    this.name = 'FontLoadError';
  }
}

// ---------------------------------------------------------------------------
// Registry state
// ---------------------------------------------------------------------------

let _initialised = false;

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Validate that all required font variants are available in the jsPDF instance.
 * jsPDF ships helvetica as a core font so we probe by switching to each variant
 * and confirming the doc reports the correct font back.
 *
 * Call this ONCE after `new jsPDF(...)` before any rendering begins.
 * Subsequent calls are no-ops (idempotent).
 */
export function initFonts(doc: jsPDF): void {
  if (_initialised) return;

  for (const { family, style } of FONT_VARIANTS) {
    try {
      doc.setFont(family, style);
      const reported = doc.getFont();
      if (reported.fontName.toLowerCase() !== family.toLowerCase()) {
        throw new FontLoadError(family, style, `doc reports "${reported.fontName}" instead`);
      }
    } catch (err) {
      if (err instanceof FontLoadError) throw err;
      throw new FontLoadError(family, style, String(err));
    }
  }

  _initialised = true;
}

/**
 * Apply a font variant to the document.
 * Throws FontLoadError if the variant is not in the allowed set.
 */
export function applyFont(doc: jsPDF, family: string, style: FontStyle): void {
  const allowed = FONT_VARIANTS.some(
    v => v.family === family && v.style === style,
  );
  if (!allowed) {
    throw new FontLoadError(family, style, 'variant is not registered in FONT_VARIANTS');
  }
  doc.setFont(family, style);
}

/**
 * Reset the registry state (for testing only).
 * @internal
 */
export function _resetFontRegistry(): void {
  _initialised = false;
}
