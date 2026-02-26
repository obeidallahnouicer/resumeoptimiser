/**
 * TypeScript mirror of the Python Pydantic schemas.
 *
 * These types are the single source of truth for what the frontend
 * sends to and receives from the FastAPI backend.
 *
 * Keep in sync with: app/schemas/*.py
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type SectionType =
  | 'summary'
  | 'experience'
  | 'education'
  | 'skills'
  | 'certifications'
  | 'projects'
  | 'languages'
  | 'other';

export type EmploymentType =
  | 'full_time'
  | 'part_time'
  | 'contract'
  | 'freelance'
  | 'internship'
  | 'unknown';

// ---------------------------------------------------------------------------
// CV schemas
// ---------------------------------------------------------------------------

export interface ContactInfo {
  name: string;
  email: string;
  phone: string;
  location: string;
  linkedin: string;
  github: string;
}

export interface CVSection {
  section_type: SectionType;
  raw_text: string;
  items: string[];
}

export interface StructuredCV {
  contact: ContactInfo;
  sections: CVSection[];
  raw_text: string;
}

// ---------------------------------------------------------------------------
// Job schemas
// ---------------------------------------------------------------------------

export interface RequiredSkill {
  skill: string;
  required: boolean;
}

export interface StructuredJob {
  title: string;
  company: string;
  employment_type: EmploymentType;
  required_skills: RequiredSkill[];
  responsibilities: string[];
  qualifications: string[];
  raw_text: string;
}

// ---------------------------------------------------------------------------
// Scoring schemas
// ---------------------------------------------------------------------------

export interface SectionScore {
  section_type: SectionType;
  score: number; // 0.0 – 1.0
}

export interface SimilarityScore {
  overall: number; // 0.0 – 1.0
  section_scores: SectionScore[];
}

// ---------------------------------------------------------------------------
// Report schemas
// ---------------------------------------------------------------------------

export interface MismatchItem {
  field: string;
  cv_value: string;
  job_expectation: string;
  explanation: string;
}

export interface ExplanationReport {
  mismatches: MismatchItem[];
  summary: string;
}

export interface OptimizedCV {
  contact: ContactInfo;
  sections: CVSection[];
  changes_summary: string[];
}

// ---------------------------------------------------------------------------
// Pipeline schemas
// ---------------------------------------------------------------------------

export interface ImprovedScore {
  before: SimilarityScore;
  after: SimilarityScore;
  delta: number;
}

export interface ComparisonReport {
  improved_score: ImprovedScore;
  explanation: ExplanationReport;
  optimized_cv: OptimizedCV;
  narrative: string;
}

// ---------------------------------------------------------------------------
// API request / response wrappers
// ---------------------------------------------------------------------------

export interface ExtractResponse {
  cv_text: string;
  filename: string;
  char_count: number;
}

export interface SemanticMatcherInput {
  cv: StructuredCV;
  job: StructuredJob;
}

export interface ScoreExplainerInput {
  cv: StructuredCV;
  job: StructuredJob;
  score: SimilarityScore;
}

export interface CVRewriteInput {
  cv: StructuredCV;
  job: StructuredJob;
  explanation: ExplanationReport;
}

export interface CompareRequest {
  original_cv: StructuredCV;
  optimized_cv: StructuredCV;
  job: StructuredJob;
  original_score: SimilarityScore;
  explanation: ExplanationReport;
  optimized_cv_schema: OptimizedCV;
}
