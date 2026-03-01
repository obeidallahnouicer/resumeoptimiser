/**
 * exportPdf – generates a clean, well-formatted PDF of the optimised CV.
 *
 * Pure jsPDF (no html2canvas) → crisp vector text, no screenshot artefacts.
 * A4 portrait, proper page-break handling, structured experience entries.
 */

import jsPDF from 'jspdf';
import type { OptimizedCV, CVSection } from '../types/pipeline';

// ─── Page geometry (mm, A4) ───────────────────────────────────────────────
const PAGE_W = 210;
const PAGE_H = 297;
const MARGIN_X = 16;
const MARGIN_Y = 16;
const CONTENT_W = PAGE_W - MARGIN_X * 2;
const FOOTER_H = 10;
const MAX_Y = PAGE_H - MARGIN_Y - FOOTER_H;

// ─── Colours ─────────────────────────────────────────────────────────────
const BLACK: [number, number, number] = [18, 18, 20];
const ACCENT: [number, number, number] = [79, 70, 229];
const MUTED: [number, number, number] = [100, 100, 115];
const LIGHT: [number, number, number] = [210, 210, 220];

// ─── Font sizes (pt) ─────────────────────────────────────────────────────
const F_NAME = 21;
const F_CONTACT = 8.5;
const F_SECTION = 10;
const F_BODY = 9;
const F_BULLET = 8.8;
const F_ENTRY_TITLE = 9;

// pt → mm
const pt2mm = (pt: number) => pt * 0.352778;
const lineH = (fontSize: number, leading = 1.5) => pt2mm(fontSize) * leading;

function sectionLabel(type: string): string {
  const MAP: Record<string, string> = {
    summary: 'Professional Summary',
    experience: 'Experience',
    education: 'Education',
    skills: 'Skills',
    certifications: 'Certifications',
    projects: 'Projects',
    languages: 'Languages',
    other: 'Additional Information',
  };
  return MAP[type] ?? type.charAt(0).toUpperCase() + type.slice(1);
}

/** "Title, Company (dates): description" → split on first colon */
function parseExperienceItem(item: string): { header: string; body: string } | null {
  const colonIdx = item.indexOf(':');
  if (colonIdx < 5 || colonIdx > 120) return null;
  const header = item.slice(0, colonIdx).trim();
  const body = item.slice(colonIdx + 1).trim();
  return body ? { header, body } : null;
}

// ─── Doc context shared across rendering helpers ──────────────────────────
interface Ctx {
  doc: jsPDF;
  y: number;
}

function addPage(ctx: Ctx) {
  ctx.doc.addPage();
  ctx.y = MARGIN_Y;
}

function need(ctx: Ctx, mm: number) {
  if (ctx.y + mm > MAX_Y) addPage(ctx);
}

/**
 * Render wrapped text at ctx.y.
 * Font style must be set by caller; font size and color are set here.
 */
function putText(
  ctx: Ctx,
  text: string,
  x: number,
  maxW: number,
  fontSize: number,
  color: [number, number, number],
  leading = 1.5,
) {
  if (!text.trim()) return;
  ctx.doc.setFontSize(fontSize);
  ctx.doc.setTextColor(...color);
  const lh = lineH(fontSize, leading);
  const lines: string[] = ctx.doc.splitTextToSize(text.trim(), maxW);
  for (const line of lines) {
    need(ctx, lh);
    ctx.doc.text(line, x, ctx.y);
    ctx.y += lh;
  }
}

function drawRule(ctx: Ctx, color: [number, number, number], weight = 0.3, gap = 3.5) {
  ctx.doc.setDrawColor(...color);
  ctx.doc.setLineWidth(weight);
  ctx.doc.line(MARGIN_X, ctx.y, PAGE_W - MARGIN_X, ctx.y);
  ctx.y += gap;
}

// ─── Section renderers ────────────────────────────────────────────────────

function renderSectionHeading(ctx: Ctx, label: string) {
  need(ctx, lineH(F_SECTION, 1.3) + 6 + lineH(F_BODY, 1.5));
  ctx.doc.setFont('helvetica', 'bold');
  putText(ctx, label.toUpperCase(), MARGIN_X, CONTENT_W, F_SECTION, ACCENT, 1.25);
  drawRule(ctx, LIGHT, 0.3, 4);
}

function renderExperienceItem(ctx: Ctx, item: string) {
  const parsed = parseExperienceItem(item);
  if (parsed) {
    need(ctx, lineH(F_ENTRY_TITLE, 1.35) + 2);
    ctx.doc.setFont('helvetica', 'bold');
    putText(ctx, parsed.header, MARGIN_X, CONTENT_W, F_ENTRY_TITLE, BLACK, 1.35);
    ctx.doc.setFont('helvetica', 'normal');
    putText(ctx, parsed.body, MARGIN_X + 3, CONTENT_W - 3, F_BULLET, BLACK, 1.45);
    ctx.y += 3;
  } else {
    ctx.doc.setFont('helvetica', 'normal');
    putText(ctx, `• ${item}`, MARGIN_X + 2, CONTENT_W - 2, F_BULLET, BLACK, 1.45);
    ctx.y += 1.5;
  }
}

function renderExperienceSection(ctx: Ctx, section: CVSection) {
  if (section.items.length > 0) {
    for (const item of section.items) renderExperienceItem(ctx, item);
  } else if (section.raw_text.trim()) {
    ctx.doc.setFont('helvetica', 'normal');
    putText(ctx, section.raw_text.trim(), MARGIN_X, CONTENT_W, F_BODY, BLACK, 1.5);
  }
}

function renderGenericSection(ctx: Ctx, section: CVSection) {
  const rawClean = section.raw_text.trim();
  const isFiller =
    rawClean.length < 20 ||
    /^(relevant|experience highlight|see items|n\/a)/i.test(rawClean);

  if (rawClean && !isFiller) {
    ctx.doc.setFont('helvetica', 'normal');
    putText(ctx, rawClean, MARGIN_X, CONTENT_W, F_BODY, BLACK, 1.5);
    if (section.items.length > 0) ctx.y += 1;
  }

  if (section.items.length > 0) {
    ctx.doc.setFont('helvetica', 'normal');
    for (const item of section.items) {
      putText(ctx, `• ${item}`, MARGIN_X + 2, CONTENT_W - 2, F_BULLET, BLACK, 1.45);
      ctx.y += 0.5;
    }
  }
}

// ─── Header renderer ──────────────────────────────────────────────────────

function renderHeader(ctx: Ctx, cv: OptimizedCV) {
  const { contact } = cv;
  ctx.doc.setFont('helvetica', 'bold');
  putText(
    ctx,
    (contact.name || 'Candidate').toUpperCase(),
    MARGIN_X, CONTENT_W, F_NAME, BLACK, 1.2,
  );
  ctx.y += 1;

  const parts: string[] = [
    contact.email, contact.phone, contact.location, contact.linkedin, contact.github,
  ].filter(Boolean);

  if (parts.length > 0) {
    ctx.doc.setFont('helvetica', 'normal');
    putText(ctx, parts.join('   |   '), MARGIN_X, CONTENT_W, F_CONTACT, MUTED, 1.4);
  }

  ctx.y += 2;
  ctx.doc.setDrawColor(...ACCENT);
  ctx.doc.setLineWidth(0.7);
  ctx.doc.line(MARGIN_X, ctx.y, PAGE_W - MARGIN_X, ctx.y);
  ctx.y += 6;
}

// ─── Footer renderer ──────────────────────────────────────────────────────

function renderFooters(doc: jsPDF) {
  const total = doc.getNumberOfPages();
  for (let p = 1; p <= total; p++) {
    doc.setPage(p);
    doc.setFontSize(7);
    doc.setTextColor(...MUTED);
    doc.text(`CV Optima  ·  Page ${p} / ${total}`, PAGE_W / 2, PAGE_H - MARGIN_Y / 2, {
      align: 'center',
    });
  }
}

// ─── Public entry point ───────────────────────────────────────────────────

export function exportOptimizedCvToPdf(cv: OptimizedCV, filename = 'optimized-cv.pdf'): void {
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const ctx: Ctx = { doc, y: MARGIN_Y };

  renderHeader(ctx, cv);

  for (const section of cv.sections) {
    renderSectionHeading(ctx, sectionLabel(section.section_type));

    if (section.section_type === 'experience') {
      renderExperienceSection(ctx, section);
    } else {
      renderGenericSection(ctx, section);
    }

    ctx.y += 5;
  }

  renderFooters(doc);
  doc.save(filename);
}
