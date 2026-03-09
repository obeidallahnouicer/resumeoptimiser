/**
 * Typed API client for the FastAPI pipeline backend.
 *
 * All requests go to /api/* which Vite proxies to http://localhost:8000
 * in development (see vite.config.ts). In production, the frontend is
 * served from the same origin as the API so no prefix is needed.
 *
 * Each function:
 * - Has one responsibility (one endpoint)
 * - Returns a typed response or throws an ApiError
 * - Never handles UI state – that is the caller's concern
 */

import type {
  CVRewriteInput,
  CompareRequest,
  ComparisonReport,
  ExplanationReport,
  ExtractResponse,
  MarkdownDiffInput,
  MarkdownDiffOutput,
  MarkdownInput,
  MarkdownOutput,
  MarkdownRewriteInput,
  MarkdownRewriteOutput,
  MarkdownToPdfInput,
  OptimizedCV,
  ScoreExplainerInput,
  SemanticMatcherInput,
  SimilarityScore,
  StructuredCV,
  StructuredJob,
} from './types/pipeline';

const BASE = '/api/v1/pipeline';

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ---------------------------------------------------------------------------
// Internal fetch helper
// ---------------------------------------------------------------------------

async function post<TBody, TResponse>(path: string, body: TBody): Promise<TResponse> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ code: 'UNKNOWN', message: res.statusText }));
    throw new ApiError(res.status, err.code ?? 'UNKNOWN', err.message ?? res.statusText);
  }
  return res.json() as Promise<TResponse>;
}

// ---------------------------------------------------------------------------
// Stage 1 – Extract text from file
// ---------------------------------------------------------------------------

export async function extractCVText(
  file: File,
  jobText: string,
): Promise<ExtractResponse> {
  const form = new FormData();
  form.append('cv_file', file);
  form.append('job_text', jobText);

  const res = await fetch(`${BASE}/extract`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ code: 'UNKNOWN', message: res.statusText }));
    throw new ApiError(res.status, err.code ?? 'UNKNOWN', err.message ?? res.statusText);
  }
  return res.json() as Promise<ExtractResponse>;
}

// ---------------------------------------------------------------------------
// Stage 2 – Parse CV
// ---------------------------------------------------------------------------

export async function parseCv(rawText: string): Promise<StructuredCV> {
  return post<{ raw_text: string }, StructuredCV>('/parse-cv', { raw_text: rawText });
}

// ---------------------------------------------------------------------------
// Stage 3 – Normalize Job
// ---------------------------------------------------------------------------

export async function normalizeJob(rawText: string): Promise<StructuredJob> {
  return post<{ raw_text: string }, StructuredJob>('/normalize-job', { raw_text: rawText });
}

// ---------------------------------------------------------------------------
// Stage 4 – Match (embeddings, no LLM)
// ---------------------------------------------------------------------------

export async function matchCvToJob(input: SemanticMatcherInput): Promise<SimilarityScore> {
  return post<SemanticMatcherInput, SimilarityScore>('/match', input);
}

// ---------------------------------------------------------------------------
// Stage 5 – Explain mismatches
// ---------------------------------------------------------------------------

export async function explainMismatches(input: ScoreExplainerInput): Promise<ExplanationReport> {
  return post<ScoreExplainerInput, ExplanationReport>('/explain', input);
}

// ---------------------------------------------------------------------------
// Stage 6 – Rewrite CV
// ---------------------------------------------------------------------------

export async function rewriteCV(input: CVRewriteInput): Promise<OptimizedCV> {
  return post<CVRewriteInput, OptimizedCV>('/rewrite', input);
}

// ---------------------------------------------------------------------------
// Stage 7 – Compare (rescore + report)
// ---------------------------------------------------------------------------

export async function compareResults(input: CompareRequest): Promise<ComparisonReport> {
  return post<CompareRequest, ComparisonReport>('/compare', input);
}

// ---------------------------------------------------------------------------
// Markdown pipeline – Stage A (preferred): StructuredCV → Markdown (deterministic)
// ---------------------------------------------------------------------------

export async function structuredToMarkdown(cv: StructuredCV): Promise<MarkdownOutput> {
  return post<StructuredCV, MarkdownOutput>('/structured-to-markdown', cv);
}

// ---------------------------------------------------------------------------
// Markdown pipeline – Stage A (fallback): OCR text → structured Markdown via LLM
// ---------------------------------------------------------------------------

export async function ocrToMarkdown(rawText: string): Promise<MarkdownOutput> {
  return post<MarkdownInput, MarkdownOutput>('/to-markdown', { raw_text: rawText });
}

// ---------------------------------------------------------------------------
// Markdown pipeline – Stage B: Markdown + job → improved Markdown
// ---------------------------------------------------------------------------

export async function rewriteMarkdown(input: MarkdownRewriteInput): Promise<MarkdownRewriteOutput> {
  return post<MarkdownRewriteInput, MarkdownRewriteOutput>('/rewrite-markdown', input);
}

// ---------------------------------------------------------------------------
// Markdown pipeline – Stage C: compute line-by-line diff
// ---------------------------------------------------------------------------

export async function computeMarkdownDiff(input: MarkdownDiffInput): Promise<MarkdownDiffOutput> {
  return post<MarkdownDiffInput, MarkdownDiffOutput>('/diff', input);
}

// ---------------------------------------------------------------------------
// Markdown pipeline – Stage D: render Markdown → PDF
// ---------------------------------------------------------------------------

/**
 * Download the improved CV as a PDF rendered from a fixed HTML/CSS template.
 * Returns a Blob so the caller can trigger a browser download.
 */
export async function renderMarkdownPdf(input: MarkdownToPdfInput): Promise<Blob> {
  const res = await fetch(`${BASE}/render-pdf`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ code: 'UNKNOWN', message: res.statusText }));
    throw new ApiError(res.status, err.code ?? 'UNKNOWN', err.message ?? res.statusText);
  }
  return res.blob();
}
