/**
 * layout_tokens.ts
 *
 * Responsibility: single source of truth for ALL visual constants.
 *
 * Rules:
 *  - Every number used during rendering must come from this file.
 *  - No magic numbers anywhere else.
 *  - Tokens are grouped by concern (page, spacing, typography, colour).
 *  - All values are immutable (const / as const).
 */

// ---------------------------------------------------------------------------
// Page geometry  (mm, A4 portrait)
// ---------------------------------------------------------------------------

export const PAGE_W_MM   = 210 as const;
export const PAGE_H_MM   = 297 as const;
export const MARGIN_X_MM =  16 as const;
export const MARGIN_Y_MM =  16 as const;
export const FOOTER_H_MM =  10 as const;

/** Usable text width. */
export const CONTENT_W_MM = PAGE_W_MM - MARGIN_X_MM * 2;

/** Y coordinate below which a new page must be added. */
export const MAX_Y_MM = PAGE_H_MM - MARGIN_Y_MM - FOOTER_H_MM;

// ---------------------------------------------------------------------------
// Spacing tokens  (mm)
// ---------------------------------------------------------------------------

export const SPACING_XS  = 0.5  as const;  // micro nudge
export const SPACING_SM  = 1.5  as const;  // tight gap
export const SPACING_MD  = 3   as const;  // standard gap
export const SPACING_LG  = 5   as const;  // section gap
export const SPACING_XL  = 6   as const;  // post-header gap
export const SPACING_2XL = 8   as const;  // reserved for future use

// ---------------------------------------------------------------------------
// Typography  (pt)
// ---------------------------------------------------------------------------

export const FONT_SIZE_NAME    = 21   as const;
export const FONT_SIZE_CONTACT =  8.5 as const;
export const FONT_SIZE_SECTION = 10   as const;
export const FONT_SIZE_BODY    =  9   as const;
export const FONT_SIZE_BULLET  =  8.8 as const;
export const FONT_SIZE_ENTRY   =  9   as const;
export const FONT_SIZE_FOOTER  =  7   as const;

/** Leading multipliers (unitless, multiplied by font-size → mm line-height). */
export const LEADING_TIGHT    = 1.25 as const;
export const LEADING_NORMAL   = 1.4  as const;
export const LEADING_RELAXED  = 1.45 as const;
export const LEADING_LOOSE    = 1.5  as const;

/** Convert pt → mm. */
export const pt2mm = (pt: number): number => pt * 0.352_778;

/** Compute line height in mm from font-size (pt) and leading multiplier. */
export const lineHeight = (fontSizePt: number, leading: number): number =>
  pt2mm(fontSizePt) * leading;

// ---------------------------------------------------------------------------
// Indent tokens  (mm, relative to MARGIN_X_MM)
// ---------------------------------------------------------------------------

export const INDENT_BULLET = 2  as const;  // bullet text left-offset
export const INDENT_BODY   = 3  as const;  // sub-body left-offset

// ---------------------------------------------------------------------------
// Colour tokens  (RGB tuples)
// ---------------------------------------------------------------------------

export type RGBColor = [number, number, number];

export const COLOR_BLACK:  RGBColor = [18,  18,  20 ];
export const COLOR_ACCENT: RGBColor = [79,  70,  229];
export const COLOR_MUTED:  RGBColor = [100, 100, 115];
export const COLOR_RULE:   RGBColor = [210, 210, 220];

// ---------------------------------------------------------------------------
// Rule / divider tokens
// ---------------------------------------------------------------------------

export const RULE_WEIGHT_LIGHT  = 0.3 as const;
export const RULE_WEIGHT_HEAVY  = 0.7 as const;
export const RULE_GAP_AFTER_MM  = 4 as const;  // space below a light rule

// ---------------------------------------------------------------------------
// Section label map  (deterministic, no runtime computation)
// ---------------------------------------------------------------------------

export const SECTION_LABELS: Readonly<Record<string, string>> = {
  summary:        'Professional Summary',
  experience:     'Experience',
  education:      'Education',
  skills:         'Skills',
  certifications: 'Certifications',
  projects:       'Projects',
  languages:      'Languages',
  other:          'Additional Information',
} as const;

export function getSectionLabel(type: string): string {
  return SECTION_LABELS[type] ?? type.charAt(0).toUpperCase() + type.slice(1);
}
