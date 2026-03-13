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
 * - Times out after TIMEOUT_MS milliseconds (default 60 s for LLM stages)
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

/** Timeout for LLM-backed stages (parse, match, explain, rewrite, compare). 
 * Increased to 300s to support heavy CV parsing tasks on free-tier models.
 */
const LLM_TIMEOUT_MS = 300_000;
/** Timeout for fast/deterministic stages (extract, diff, render-pdf). */
const FAST_TIMEOUT_MS = 60_000;

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
// Internal fetch helpers
// ---------------------------------------------------------------------------

/**
 * Parse an error response body, falling back gracefully when the body
 * is not JSON (e.g. a 502 Bad Gateway HTML page from a proxy).
 */
async function _parseErrorBody(res: Response): Promise<{ code: string; message: string }> {
  try {
    const body = await res.json();
    // FastAPI wraps validation errors in { detail: { code, message } }
    // or { detail: "string" } for simple raises.
    if (body?.detail && typeof body.detail === 'object') {
      return { code: body.detail.code ?? 'API_ERROR', message: body.detail.message ?? res.statusText };
    }
    if (body?.detail && typeof body.detail === 'string') {
      return { code: 'API_ERROR', message: body.detail };
    }
    return { code: body?.code ?? 'API_ERROR', message: body?.message ?? res.statusText };
  } catch {
    return { code: 'API_ERROR', message: res.statusText || `HTTP ${res.status}` };
  }
}

/**
 * POST JSON with AbortController timeout.
 *
 * Throws:
 *   ApiError(408, 'TIMEOUT', …)  when the request exceeds timeoutMs
 *   ApiError(0,   'NETWORK', …)  on network failure (no connection, DNS, etc.)
 *   ApiError(status, code, …)    on any non-2xx HTTP response
 */
async function post<TBody, TResponse>(
  path: string,
  body: TBody,
  timeoutMs = LLM_TIMEOUT_MS,
): Promise<TResponse> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!res.ok) {
      const { code, message } = await _parseErrorBody(res);
      throw new ApiError(res.status, code, message);
    }

    return res.json() as Promise<TResponse>;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(408, 'TIMEOUT', `Request timed out after ${timeoutMs / 1000}s`);
    }
    // Network error (offline, refused, DNS failure, etc.)
    const msg = err instanceof Error ? err.message : String(err);
    throw new ApiError(0, 'NETWORK', `Network error: ${msg}`);
  } finally {
    clearTimeout(timer);
  }
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

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FAST_TIMEOUT_MS);

  try {
    const res = await fetch(`${BASE}/extract`, {
      method: 'POST',
      body: form,
      signal: controller.signal,
    });

    if (!res.ok) {
      const { code, message } = await _parseErrorBody(res);
      throw new ApiError(res.status, code, message);
    }

    return res.json() as Promise<ExtractResponse>;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(408, 'TIMEOUT', `Extract timed out after ${FAST_TIMEOUT_MS / 1000}s`);
    }
    const msg = err instanceof Error ? err.message : String(err);
    throw new ApiError(0, 'NETWORK', `Network error: ${msg}`);
  } finally {
    clearTimeout(timer);
  }
}

// ---------------------------------------------------------------------------
// Stage 2 – Parse CV  (LLM-backed — uses LLM_TIMEOUT_MS)
// ---------------------------------------------------------------------------

export async function parseCv(rawText: string): Promise<StructuredCV> {
  return post<{ raw_text: string }, StructuredCV>('/parse-cv', { raw_text: rawText });
}

// ---------------------------------------------------------------------------
// Stage 3 – Normalize Job  (LLM-backed)
// ---------------------------------------------------------------------------

export async function normalizeJob(rawText: string): Promise<StructuredJob> {
  return post<{ raw_text: string }, StructuredJob>('/normalize-job', { raw_text: rawText });
}

// ---------------------------------------------------------------------------
// Stage 4 – Match (embeddings, no LLM — faster)
// ---------------------------------------------------------------------------

export async function matchCvToJob(input: SemanticMatcherInput): Promise<SimilarityScore> {
  return post<SemanticMatcherInput, SimilarityScore>('/match', input, FAST_TIMEOUT_MS);
}

// ---------------------------------------------------------------------------
// Stage 5 – Explain mismatches  (LLM-backed)
// ---------------------------------------------------------------------------

export async function explainMismatches(input: ScoreExplainerInput): Promise<ExplanationReport> {
  return post<ScoreExplainerInput, ExplanationReport>('/explain', input);
}

// ---------------------------------------------------------------------------
// Stage 6 – Rewrite CV  (LLM-backed)
// ---------------------------------------------------------------------------

export async function rewriteCV(input: CVRewriteInput): Promise<OptimizedCV> {
  return post<CVRewriteInput, OptimizedCV>('/rewrite', input);
}

// ---------------------------------------------------------------------------
// Stage 7 – Compare (rescore + report)  (LLM-backed)
// ---------------------------------------------------------------------------

export async function compareResults(input: CompareRequest): Promise<ComparisonReport> {
  return post<CompareRequest, ComparisonReport>('/compare', input);
}

// ---------------------------------------------------------------------------
// Markdown pipeline – Stage A (preferred): StructuredCV → Markdown (deterministic)
// ---------------------------------------------------------------------------

export async function structuredToMarkdown(cv: StructuredCV): Promise<MarkdownOutput> {
  return post<StructuredCV, MarkdownOutput>('/structured-to-markdown', cv, FAST_TIMEOUT_MS);
}

// ---------------------------------------------------------------------------
// Markdown pipeline – Stage A (fallback): OCR text → structured Markdown
// Deterministic — no LLM. Kept for direct use if needed.
// ---------------------------------------------------------------------------

export async function ocrToMarkdown(rawText: string): Promise<MarkdownOutput> {
  return post<MarkdownInput, MarkdownOutput>('/to-markdown', { raw_text: rawText }, FAST_TIMEOUT_MS);
}

// ---------------------------------------------------------------------------
// Markdown pipeline – Stage B: Markdown + job → improved Markdown  (LLM-backed)
// ---------------------------------------------------------------------------

export async function rewriteMarkdown(input: MarkdownRewriteInput): Promise<MarkdownRewriteOutput> {
  return post<MarkdownRewriteInput, MarkdownRewriteOutput>('/rewrite-markdown', input);
}

// ---------------------------------------------------------------------------
// Markdown pipeline – Stage C: compute line-by-line diff  (deterministic)
// ---------------------------------------------------------------------------

export async function computeMarkdownDiff(input: MarkdownDiffInput): Promise<MarkdownDiffOutput> {
  return post<MarkdownDiffInput, MarkdownDiffOutput>('/diff', input, FAST_TIMEOUT_MS);
}

// ---------------------------------------------------------------------------
// Markdown pipeline – Stage D: render Markdown → PDF  (deterministic)
// ---------------------------------------------------------------------------

/**
 * Download the improved CV as a PDF rendered from a fixed HTML/CSS template.
 * Returns a Blob so the caller can trigger a browser download.
 */
export async function renderMarkdownPdf(input: MarkdownToPdfInput): Promise<Blob> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), FAST_TIMEOUT_MS);

  try {
    const res = await fetch(`${BASE}/render-pdf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input),
      signal: controller.signal,
    });

    if (!res.ok) {
      const { code, message } = await _parseErrorBody(res);
      throw new ApiError(res.status, code, message);
    }

    return res.blob();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiError(408, 'TIMEOUT', `PDF render timed out after ${FAST_TIMEOUT_MS / 1000}s`);
    }
    const msg = err instanceof Error ? err.message : String(err);
    throw new ApiError(0, 'NETWORK', `Network error: ${msg}`);
  } finally {
    clearTimeout(timer);
  }
}
