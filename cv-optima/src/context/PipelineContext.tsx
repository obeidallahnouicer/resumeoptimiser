/**
 * PipelineContext – shared state for the entire CV optimisation pipeline.
 *
 * Holds every piece of data produced by the backend across the 6 UI stages.
 * Exposed via usePipeline() hook. No API calls happen here – stages call
 * api.ts and store results via the setters provided by this context.
 */

import { createContext, useContext, useState, ReactNode } from 'react';
import type {
  StructuredCV,
  StructuredJob,
  SimilarityScore,
  ExplanationReport,
  OptimizedCV,
  ComparisonReport,
} from '../types/pipeline';

interface PipelineState {
  // Raw inputs
  cvText: string;
  jobText: string;
  cvFilename: string;

  // Stage outputs
  structuredCV: StructuredCV | null;
  structuredJob: StructuredJob | null;
  similarityScore: SimilarityScore | null;
  explanationReport: ExplanationReport | null;
  optimizedCV: OptimizedCV | null;
  comparisonReport: ComparisonReport | null;

  // Error tracking
  error: string | null;
}

interface PipelineActions {
  setRawInputs: (cvText: string, jobText: string, filename: string) => void;
  setStructuredCV: (cv: StructuredCV) => void;
  setStructuredJob: (job: StructuredJob) => void;
  setSimilarityScore: (score: SimilarityScore) => void;
  setExplanationReport: (report: ExplanationReport) => void;
  setOptimizedCV: (cv: OptimizedCV) => void;
  setComparisonReport: (report: ComparisonReport) => void;
  setError: (message: string | null) => void;
  reset: () => void;
}

const initialState: PipelineState = {
  cvText: '',
  jobText: '',
  cvFilename: '',
  structuredCV: null,
  structuredJob: null,
  similarityScore: null,
  explanationReport: null,
  optimizedCV: null,
  comparisonReport: null,
  error: null,
};

const PipelineContext = createContext<(PipelineState & PipelineActions) | null>(null);

export function PipelineProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<PipelineState>(initialState);

  const actions: PipelineActions = {
    setRawInputs: (cvText, jobText, filename) =>
      setState((s) => ({ ...s, cvText, jobText, cvFilename: filename, error: null })),

    setStructuredCV: (cv) =>
      setState((s) => ({ ...s, structuredCV: cv })),

    setStructuredJob: (job) =>
      setState((s) => ({ ...s, structuredJob: job })),

    setSimilarityScore: (score) =>
      setState((s) => ({ ...s, similarityScore: score })),

    setExplanationReport: (report) =>
      setState((s) => ({ ...s, explanationReport: report })),

    setOptimizedCV: (cv) =>
      setState((s) => ({ ...s, optimizedCV: cv })),

    setComparisonReport: (report) =>
      setState((s) => ({ ...s, comparisonReport: report })),

    setError: (message) =>
      setState((s) => ({ ...s, error: message })),

    reset: () => setState(initialState),
  };

  return (
    <PipelineContext.Provider value={{ ...state, ...actions }}>
      {children}
    </PipelineContext.Provider>
  );
}

export function usePipeline(): PipelineState & PipelineActions {
  const ctx = useContext(PipelineContext);
  if (!ctx) throw new Error('usePipeline must be used inside <PipelineProvider>');
  return ctx;
}
