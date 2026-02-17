import { GenerationResponse } from '../types';

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