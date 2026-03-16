/**
 * PipelineContext – shared state for the entire CV optimisation pipeline.
 *
 * Holds every piece of data produced by the backend across all UI stages.
 * Exposed via usePipeline() hook. No API calls happen here – stages call
 * api.ts and store results via the setters provided by this context.
 */

import { createContext, useContext, useState, ReactNode, useMemo } from 'react';
import type {
  StructuredCV,
  StructuredJob,
  SimilarityScore,
  ExplanationReport,
  OptimizedCV,
  ComparisonReport,
  IdealProfile,
  MarkdownDiffOutput,
} from '../types/pipeline';

interface PipelineState {
  // Raw inputs
  cvText: string;
  jobText: string;
  cvFilename: string;

  // Stage outputs – structured pipeline
  structuredCV: StructuredCV | null;
  structuredJob: StructuredJob | null;
  similarityScore: SimilarityScore | null;
  explanationReport: ExplanationReport | null;
  idealProfile: IdealProfile | null;
  optimizedCV: OptimizedCV | null;
  comparisonReport: ComparisonReport | null;

  // Markdown pipeline (layout-safe)
  originalMarkdown: string | null;   // original_cv.md – immutable
  improvedMarkdown: string | null;   // improved_cv.md – wording only
  markdownDiff: MarkdownDiffOutput | null;

  // Skill editor state – tracks user edits to hard skills
  editedHardSkills: string[] | null;

  // Error tracking
  error: string | null;
}

interface PipelineActions {
  setRawInputs: (cvText: string, jobText: string, filename: string) => void;
  setStructuredCV: (cv: StructuredCV) => void;
  setStructuredJob: (job: StructuredJob) => void;
  setSimilarityScore: (score: SimilarityScore) => void;
  setExplanationReport: (report: ExplanationReport) => void;
  setIdealProfile: (profile: IdealProfile) => void;
  setOptimizedCV: (cv: OptimizedCV) => void;
  setComparisonReport: (report: ComparisonReport) => void;
  setOriginalMarkdown: (md: string) => void;
  setImprovedMarkdown: (md: string) => void;
  setMarkdownDiff: (diff: MarkdownDiffOutput) => void;
  setEditedHardSkills: (skills: string[]) => void;
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
  idealProfile: null,
  optimizedCV: null,
  comparisonReport: null,
  originalMarkdown: null,
  improvedMarkdown: null,
  markdownDiff: null,
  editedHardSkills: null,
  error: null,
};

const PipelineContext = createContext<(PipelineState & PipelineActions) | null>(null);

export function PipelineProvider({ children }: Readonly<{ children: ReactNode }>) {
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

    setIdealProfile: (profile) =>
      setState((s) => ({ ...s, idealProfile: profile })),

    setOptimizedCV: (cv) =>
      setState((s) => ({ ...s, optimizedCV: cv })),

    setComparisonReport: (report) =>
      setState((s) => ({ ...s, comparisonReport: report })),

    setOriginalMarkdown: (md) =>
      setState((s) => ({ ...s, originalMarkdown: md })),

    setImprovedMarkdown: (md) =>
      setState((s) => ({ ...s, improvedMarkdown: md })),

    setMarkdownDiff: (diff) =>
      setState((s) => ({ ...s, markdownDiff: diff })),

    setEditedHardSkills: (skills) =>
      setState((s) => ({ ...s, editedHardSkills: skills })),

    setError: (message) =>
      setState((s) => ({ ...s, error: message })),

    reset: () => setState(initialState),
  };

  const contextValue = useMemo(() => ({ ...state, ...actions }), [state]);

  return (
    <PipelineContext.Provider value={contextValue}>
      {children}
    </PipelineContext.Provider>
  );
}

export function usePipeline(): PipelineState & PipelineActions {
  const ctx = useContext(PipelineContext);
  if (!ctx) throw new Error('usePipeline must be used inside <PipelineProvider>');
  return ctx;
}
