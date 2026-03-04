/**
 * exportPdf.ts
 *
 * Responsibility: public entry point for PDF export.
 *
 * Wires together:
 *   cv_document  → builds the CVDocument model
 *   pdf_renderer → renders CVDocument to a jsPDF instance
 *
 * This file contains ZERO rendering logic and ZERO spacing constants.
 * It only orchestrates the pipeline and triggers the browser download.
 */

import type { OptimizedCV } from '../types/pipeline';
import { buildCVDocument, type SectionUpdate } from './pdf/cv_document';
import { renderCVToPdf } from './pdf/pdf_renderer';

export type { SectionUpdate } from './pdf/cv_document';

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Export a fully-optimised CV to PDF and trigger a browser download.
 *
 * @param cv       The optimised CV from the pipeline.
 * @param filename Desired filename for the downloaded PDF.
 */
export function exportOptimizedCvToPdf(cv: OptimizedCV, filename = 'optimized-cv.pdf'): void {
  const document = buildCVDocument(cv);
  const doc = renderCVToPdf(document);
  doc.save(filename);
}

/**
 * Export a CV with selective section overrides applied before rendering.
 *
 * Use this when only some sections have been optimised and the rest must be
 * preserved verbatim.
 *
 * @param cv      Base CV (original or partially-optimised).
 * @param updates List of section replacements to apply in order.
 * @param filename Desired filename.
 */
export function exportCvWithUpdates(
  cv: OptimizedCV,
  updates: SectionUpdate[],
  filename = 'optimized-cv.pdf',
): void {
  const base = buildCVDocument(cv);
  const updated = base.applyUpdates(updates);
  const doc = renderCVToPdf(updated);
  doc.save(filename);
}

