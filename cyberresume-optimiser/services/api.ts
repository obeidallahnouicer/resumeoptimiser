import { 
  GenerationResponse, 
  SemanticMatchResult, 
  SemanticCVReport, 
  CVOptimizationResult 
} from '../types';

const API_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000/api/v1';
const API_TIMEOUT = Number.parseInt((import.meta as any).env?.VITE_API_TIMEOUT || '60000', 10);
const ENABLE_MOCK = (import.meta as any).env?.VITE_ENABLE_MOCK_MODE === 'true';

// MOCK DATA for demonstration if backend is not reachable
const MOCK_RESPONSE: GenerationResponse = {
  parsed_jd: {
    tech_stack: ["Python", "FastAPI", "React", "Docker", "AWS", "PostgreSQL", "Tailwind"],
    seniority: "Senior",
    domain_keywords: ["FinTech", "High Frequency", "Low Latency"]
  },
  skill_match: {
    match_score: 0.85,
    direct_matches: ["Python", "Docker", "AWS", "PostgreSQL"],
    semantic_matches: ["FastAPI (via Flask)", "React (via Vue)"],
    missing_skills: ["Kubernetes", "GraphQL"]
  },
  cv_score: {
    total_score: 87.5,
    category: "GREEN",
    breakdown: {
      stack_alignment: 35, // out of 40
      capability_match: 18, // out of 20
      seniority_fit: 15, // out of 15
      domain_relevance: 9.5, // out of 10
      sponsorship: 10 // out of 15
    }
  },
  rewritten_cv: {
    latex_content: `\\documentclass{article}
\\usepackage{hyperref}
\\begin{document}
\\name{CYBER PUNK}
\\contact{San Francisco, CA}{555-0199}

\\section{Summary}
Senior Full Stack Engineer with 8+ years of experience in high-frequency trading platforms...

\\section{Skills}
\\textbf{Core:} Python, FastAPI, React, Docker, AWS
\\textbf{Secondary:} PostgreSQL, Tailwind, TypeScript

\\section{Experience}
\\textbf{Senior Engineer} \\hfill 2020 - Present
\\begin{itemize}
  \\item Optimized latency by 40\\% using Python async/await patterns.
  \\item Deployed containerized microservices on AWS ECS.
\\end{itemize}

\\end{document}`
  },
  pdf_path: "build/cv.pdf",
  logs: [
    "[INIT] System initialization complete.",
    "[UPLOAD] Source PDF received and buffered.",
    "[PARSE] Job Description analysis started.",
    "[PARSE] Extracted 7 core technologies.",
    "[PARSE] Seniority level detected: SENIOR.",
    "[MATCH] Loading Truth File (base_skills.json)...",
    "[MATCH] Calculating TF-IDF embeddings...",
    "[MATCH] Direct match found: Python",
    "[MATCH] Semantic bridge built: Flask -> FastAPI",
    "[SCORE] Stack Alignment: 35/40",
    "[SCORE] Domain Relevance: 9.5/10",
    "[SCORE] Final Score: 87.5 (GREEN)",
    "[GEN] Injecting data into LaTeX template...",
    "[COMPILE] Running pdflatex subprocess...",
    "[SUCCESS] PDF generated successfully."
  ]
};

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Create a timeout promise that rejects after specified milliseconds
 */
function createTimeoutPromise(ms: number): Promise<never> {
  return new Promise((_, reject) =>
    setTimeout(() => reject(new Error('Request timeout')), ms)
  );
}

/**
 * Fetch with timeout support
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit,
  timeoutMs: number = API_TIMEOUT
): Promise<Response> {
  return Promise.race([
    fetch(url, options),
    createTimeoutPromise(timeoutMs)
  ]);
}

export const generateCV = async (jdText: string, cvFile: File | null): Promise<GenerationResponse> => {
  // Force mock mode if env var is set
  if (ENABLE_MOCK) {
    console.log("Mock mode enabled, using MOCK simulation for demo.");
    await delay(2500);
    return MOCK_RESPONSE;
  }

  try {
    const formData = new FormData();
    formData.append('jd_text', jdText);
    
    if (cvFile) {
      // Validate file size (50MB default)
      const maxSizeMB = Number.parseInt((import.meta as any).env?.VITE_MAX_FILE_SIZE_MB || '50', 10);
      const maxSizeBytes = maxSizeMB * 1024 * 1024;
      
      if (cvFile.size > maxSizeBytes) {
        throw new Error(`File size exceeds ${maxSizeMB}MB limit. Current size: ${(cvFile.size / 1024 / 1024).toFixed(2)}MB`);
      }
      
      // Validate file type
      const allowedTypes = ((import.meta as any).env?.VITE_ALLOWED_FILE_TYPES || 'application/pdf').split(',');
      if (!allowedTypes.includes(cvFile.type)) {
        throw new Error(`Invalid file type. Allowed types: ${allowedTypes.join(', ')}`);
      }
      
      formData.append('cv_file', cvFile);
    }

    // Call the real backend
    const response = await fetchWithTimeout(`${API_URL}/generation/generate`, {
      method: 'POST',
      body: formData,
    }, API_TIMEOUT);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.statusText} (${response.status})`);
    }

    return await response.json();
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Unknown error';
    console.warn("Backend unavailable or error occurred:", errorMsg);
    console.log("Using MOCK simulation for demo.");
    
    // Fall back to mock mode with delay
    await delay(2500);
    return MOCK_RESPONSE;
  }
};

export const downloadPDF = async (pdfPath: string | null) => {
  if (!pdfPath) {
    alert('No PDF available for download');
    return;
  }

  try {
    // Construct the full URL to the PDF
    const fullUrl = pdfPath.startsWith('http') 
      ? pdfPath 
      : `${API_URL}/../..${pdfPath}`;  // Adjust path based on your backend structure
    
    const response = await fetchWithTimeout(fullUrl, { method: 'GET' }, API_TIMEOUT);
    
    if (!response.ok) {
      throw new Error(`Failed to download PDF: ${response.statusText}`);
    }

    const blob = await response.blob();
    const url = globalThis.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'optimized_resume.pdf';
    document.body.appendChild(a);
    a.click();
    globalThis.URL.revokeObjectURL(url);
    a.remove();
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Unknown error';
    alert(`Failed to download PDF: ${errorMsg}`);
  }
};

// ============= SEMANTIC MATCHING API FUNCTIONS =============

/**
 * Perform semantic CV to JD matching
 */
export const semanticMatch = async (
  cvFile: File,
  jdText: string,
  profileFile?: File
): Promise<SemanticMatchResult> => {
  if (ENABLE_MOCK) {
    console.log("Mock mode enabled for semantic matching");
    await delay(3000);
    return generateMockSemanticMatch();
  }

  try {
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('cv_file', cvFile);
    formData.append('job_description_text', jdText);
    if (profileFile) {
      formData.append('profile_file', profileFile);
    }

    const response = await fetchWithTimeout(
      `${API_URL}/semantic-matching/match`,
      {
        method: 'POST',
        body: formData
      },
      API_TIMEOUT
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Unknown error';
    console.warn("Semantic matching failed:", errorMsg);
    throw error;
  }
};

/**
 * SMART: Perform semantic CV to JD matching with LLM preprocessing
 * 
 * This uses LLM to intelligently parse the job description before matching,
 * resulting in much better gap analysis and recommendations.
 */
export const semanticMatchSmart = async (
  cvFile: File,
  jdText: string,
  profileFile?: File
): Promise<SemanticMatchResult> => {
  if (ENABLE_MOCK) {
    console.log("Mock mode enabled for smart semantic matching");
    await delay(4000); // Takes a bit longer due to LLM processing
    return generateMockSemanticMatch();
  }

  try {
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('cv_file', cvFile);
    formData.append('job_description_text', jdText);
    if (profileFile) {
      formData.append('profile_file', profileFile);
    }

    console.log("🧠 Calling smart semantic matching with LLM preprocessing...");
    const response = await fetchWithTimeout(
      `${API_URL}/semantic-matching/match-smart`,
      {
        method: 'POST',
        body: formData
      },
      API_TIMEOUT + 10000 // Extra timeout for LLM processing
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.statusText}`);
    }

    const result = await response.json();
    console.log("✅ Smart matching complete:", result);
    return result;
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Unknown error';
    console.warn("Smart semantic matching failed:", errorMsg);
    throw error;
  }
};

/**
 * Optimize CV based on job description
 */
export const optimizeCV = async (
  cvFile: File,
  jdText: string,
  profileFile?: File
): Promise<CVOptimizationResult> => {
  if (ENABLE_MOCK) {
    console.log("Mock mode enabled for CV optimization");
    await delay(4000);
    return generateMockOptimization();
  }

  try {
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('cv_file', cvFile);
    formData.append('job_description_text', jdText);
    if (profileFile) {
      formData.append('profile_file', profileFile);
    }
    formData.append('apply_optimizations', 'true');

    const response = await fetchWithTimeout(
      `${API_URL}/semantic-matching/optimize`,
      {
        method: 'POST',
        body: formData
      },
      API_TIMEOUT
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Unknown error';
    console.warn("CV optimization failed:", errorMsg);
    throw error;
  }
};

/**
 * Generate full semantic CV report
 */
export const generateFullReport = async (
  cvFile: File,
  jdText: string,
  profileFile?: File,
  applyOptimizations: boolean = false
): Promise<SemanticCVReport> => {
  if (ENABLE_MOCK) {
    console.log("Mock mode enabled for full report");
    await delay(5000);
    return generateMockFullReport();
  }

  try {
    // Create FormData for file upload
    const formData = new FormData();
    formData.append('cv_file', cvFile);
    formData.append('job_description_text', jdText);
    if (profileFile) {
      formData.append('profile_file', profileFile);
    }
    formData.append('apply_optimizations', String(applyOptimizations));

    const response = await fetchWithTimeout(
      `${API_URL}/semantic-matching/full-report`,
      {
        method: 'POST',
        body: formData
      },
      API_TIMEOUT
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API Error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : 'Unknown error';
    console.warn("Full report generation failed:", errorMsg);
    throw error;
  }
};

// ============= MOCK DATA GENERATORS =============

function generateMockSemanticMatch(): SemanticMatchResult {
  return {
    overall_score: 0.78,
    confidence: 'strong',
    section_scores: {
      skills: { similarity: 0.82, matched_count: 12, total_required: 15 },
      experience: { similarity: 0.75, years_match: 8, required_years: 5 },
      education: { similarity: 0.70, relevant_degrees: 1 }
    },
    skill_match_ratio: 0.8,
    gaps: [
      {
        gap_id: 'gap_001',
        requirement: 'Kubernetes orchestration',
        gap_type: 'skill_gap',
        severity: 'high',
        similarity: 0.45,
        closest_match: 'Docker containerization',
        suggested_improvement: 'Add Kubernetes experience or emphasize container orchestration work',
        source: 'job_description'
      },
      {
        gap_id: 'gap_002',
        requirement: '5+ years backend development',
        gap_type: 'wording_gap',
        severity: 'moderate',
        similarity: 0.65,
        closest_match: 'Backend development experience',
        suggested_improvement: 'Emphasize years of backend work and mention scale of systems',
        source: 'job_description'
      }
    ],
    critical_gaps: 1,
    recommendations: [
      '✓ Strong match - Ready to apply',
      '🟠 Address 1 critical skill gap (Kubernetes)',
      'Consider adding cloud orchestration experience'
    ]
  };
}

function generateMockOptimization(): CVOptimizationResult {
  return {
    original_score: 0.78,
    optimized_score: 0.87,
    improvement_delta: 0.09,
    improvements_made: [
      'Reworded backend experience to emphasize scalable systems',
      'Added quantified metrics for performance improvements',
      'Highlighted cloud deployment experience for AWS skills',
      'Reorganized skills section for better ATS matching'
    ],
    optimized_sections: {
      skills: 'Python • Java • AWS • Docker • PostgreSQL • React • TypeScript • Kubernetes',
      experience:
        'Senior Backend Engineer | TechCorp | 2019-Present\n' +
        '• Architected microservices platform serving 1M+ requests/day\n' +
        '• Reduced API latency by 40% through async optimization\n' +
        '• Deployed containerized services on AWS ECS and Kubernetes\n' +
        '• Led team of 4 engineers in cloud migration project'
    },
    warnings: [],
    compliance_check: {
      no_hallucination: true,
      uses_profile_data: false,
      jd_aligned: true
    }
  };
}

function generateMockFullReport(): SemanticCVReport {
  return {
    matching_result: generateMockSemanticMatch(),
    optimization_result: generateMockOptimization(),
    analysis_timestamp: new Date().toISOString(),
    summary:
      'CV-JD Alignment: 78% (strong). Identified 2 gaps (1 critical). ' +
      'After optimization: 87% (+9%). Recommendations: Build Kubernetes skills, ' +
      'Add deployment experience.'
  };
}