export interface ParsedJobDescription {
  core_stack: string[];
  secondary_stack: string[];
  domain: string[];
  seniority: string;
  keywords: string[];
  raw_jd: string;
}

export interface SkillMatchDetail {
  status: 'direct' | 'missing' | 'semantic';
  source: string | null;
  similarity: number;
  closest_match: string | null;
}

export interface SkillMatchResult {
  matches: Record<string, SkillMatchDetail>;
  unmatched_jd_requirements: string[];
  total_matched: number;
  total_jd_requirements: number;
}

export interface CVScore {
  total_score: number;
  category: 'green' | 'yellow' | 'red';
  breakdown: {
    stack_alignment: number;
    capability_match: number;
    seniority_fit: number;
    domain_relevance: number;
    sponsorship_feasibility: number;
  };
  recommendation: string;
}

export interface GenerationResponse {
  parsed_jd: ParsedJobDescription;
  skill_match: SkillMatchResult;
  cv_score: CVScore;
  rewritten_cv: {
    experience_section: string;
    skills_section: string;
    latex_content: string;
    warnings: string[];
  };
  pdf_path: string | null;
  logs: string[];
}

export interface ApiError {
  detail: string;
}
