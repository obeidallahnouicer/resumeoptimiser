# Resume Optimiser

## Project Description

This project generates **ATS-friendly, truth-constrained LaTeX CVs** tailored to specific job descriptions. It uses Python, FastAPI, and semantic analysis to match your actual skills with job requirements, ensuring no hallucination and maximum relevance.

## Features

- ✅ **ATS-Friendly CV Generation** - LaTeX format optimized for Applicant Tracking Systems
- ✅ **Truth-Constrained** - Only uses your actual skills and experience from `base_skills.json`
- ✅ **Job Description Parsing** - Intelligently extracts tech stack, domain, and requirements
- ✅ **Semantic Skill Matching** - Matches your skills to JD requirements with similarity scoring
- ✅ **CV Scoring** - Calculates alignment score (green/yellow/red) with detailed breakdown
- ✅ **Automatic LaTeX Rewriting** - Dynamically emphasizes relevant skills and experience
- ✅ **PDF Compilation** - Generates publication-ready PDF from LaTeX
- ✅ **FastAPI Backend** - Full REST API with comprehensive endpoints
- ✅ **End-to-End Workflow** - Complete pipeline from JD to PDF in one call

## Architecture

### 8-Ticket Implementation

1. **Project Setup** ✅ - Git repo, venv, dependencies, LaTeX template
2. **Base Skills JSON** ✅ - Immutable truth file with your skills/experience
3. **JD Parser** ✅ - Converts raw job descriptions to structured JSON
4. **Skill Matcher** ✅ - Semantic matching with cosine similarity
5. **Scoring Engine** ✅ - Weighted scoring across 5 dimensions
6. **CV Rewriter** ✅ - LLM-powered LaTeX generation (truth-constrained)
7. **PDF Compiler** ✅ - LaTeX → PDF with validation
8. **End-to-End Test** ✅ - Complete workflow integration

## Installation

### 1. Clone & Setup Environment

```bash
git clone <repo-url>
cd resumeoptimiser
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install LaTeX (Required for PDF compilation)

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-full
```

**macOS:**
```bash
brew install mactex
```

**Fedora/RHEL:**
```bash
sudo dnf install texlive-scheme-full
```

## Usage

### Starting the FastAPI Server

```bash
python main.py
# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
# OpenAPI schema at http://localhost:8000/openapi.json
```

### API Endpoints

#### 1. Get Base Skills
```bash
curl http://localhost:8000/api/v1/base-skills
```

#### 2. Parse Job Description
```bash
curl -X POST http://localhost:8000/api/v1/parse-jd \
  -H "Content-Type: application/json" \
  -d '{"jd_text": "Looking for a Python developer with React experience..."}'
```

#### 3. Match Skills
```bash
curl -X POST http://localhost:8000/api/v1/match-skills \
  -H "Content-Type: application/json" \
  -d '{"jd_json": {...}}'
```

#### 4. Score CV
```bash
curl -X POST http://localhost:8000/api/v1/score-cv \
  -H "Content-Type: application/json" \
  -d '{"skill_match_json": {...}, "jd_json": {...}}'
```

#### 5. Rewrite CV (LaTeX)
```bash
curl -X POST http://localhost:8000/api/v1/rewrite-cv \
  -H "Content-Type: application/json" \
  -d '{"jd_json": {...}, "skill_match_json": {...}, "cv_score": {...}}'
```

#### 6. Compile PDF
```bash
curl -X POST http://localhost:8000/api/v1/compile-pdf \
  -H "Content-Type: application/json" \
  -d '{"latex_content": "\\documentclass{article}..."}' \
  > cv.pdf
```

#### 7. End-to-End Generation (All steps)
```bash
curl -X POST http://localhost:8000/api/v1/generate-cv \
  -H "Content-Type: application/json" \
  -d '{"jd_text": "Job description here..."}' > response.json
```

## Configuration

### Base Skills (`base_skills.json`)

Edit this file to add/update your actual skills and experience:

```json
{
  "name": "Your Name",
  "email": "your@email.com",
  "phone": "+1-555-0000",
  "summary": "Your professional summary",
  "skills": [
    {
      "name": "Python",
      "years": 6,
      "level": "expert",
      "projects": ["ProjectA", "ProjectB"],
      "description": "Backend development, data processing"
    }
  ],
  "experience": [
    {
      "title": "Senior Engineer",
      "company": "Company Inc.",
      "duration_months": 24,
      "role": "Lead backend engineer",
      "bullet_points": ["Achievement 1", "Achievement 2"],
      "measurable_impact": ["60% faster", "100K users"]
    }
  ]
}
```

## Truth Constraint

The system is designed to be **truth-constrained** - it will NEVER:

- ❌ Add skills you don't have
- ❌ Invent experience or projects
- ❌ Exaggerate your qualifications
- ❌ Use data outside `base_skills.json`

**All CV content comes directly from your base skills.** Skill matching and rewriting only emphasizes relevant parts of your actual experience.

## Project Structure

```
resumeoptimiser/
├── main.py                 # FastAPI application
├── schemas.py             # Pydantic models for validation
├── jd_parser.py           # Job description parsing
├── skill_matcher.py       # Semantic skill matching
├── scoring_engine.py      # CV scoring (0-100)
├── cv_rewriter.py         # LaTeX generation
├── pdf_compiler.py        # LaTeX → PDF compilation
├── base_skills.json       # Your truth file
├── template.tex           # LaTeX template
├── requirements.txt       # Python dependencies
├── .git/                  # Git repository
├── .venv/                 # Virtual environment
└── build/                 # Compiled PDFs (auto-created)
```

## Example Workflow

1. **Update `base_skills.json`** with your real skills and experience
2. **Paste job description** to `/api/v1/generate-cv`
3. **Get back:**
   - Parsed JD structure
   - Skill match analysis
   - Alignment score (green/yellow/red)
   - Rewritten LaTeX CV
   - Compiled PDF (if TeX installed)

## Scoring Breakdown

Each CV is scored out of 100 points:

- **Stack Alignment** (40 pts) - How well your skills match the JD tech stack
- **Capability Match** (20 pts) - Percentage of JD requirements you have
- **Seniority Fit** (15 pts) - Your experience level vs. role requirements
- **Domain Relevance** (10 pts) - Industry/domain overlap
- **Sponsorship Feasibility** (15 pts) - How learnable the missing skills are

**Categories:**
- 🟢 **Green** (80+) - Strong fit, apply now!
- 🟡 **Yellow** (60-79) - Moderate fit, consider learning
- 🔴 **Red** (0-59) - Weak fit, alignment needed

## Development

### Run Tests
```bash
pytest tests/
```

### Git Workflow
```bash
# Main branch (production)
git checkout main

# Development branch
git checkout dev

# Feature branches
git checkout -b features/feature-name
```

## Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation
- **numpy** - Numerical computing
- **pandas** - Data analysis
- **scikit-learn** - ML / cosine similarity
- **jinja2** - Template rendering
- **pylatex** - LaTeX generation

## TODO - Future Enhancements

- [ ] OpenRouter API integration for LLM JD parsing
- [ ] Fine-tuned embeddings for skill similarity
- [ ] Database backend for tracking CV versions
- [ ] Job description URL ingestion
- [ ] Multi-language CV support
- [ ] ATS keyword density analyzer
- [ ] Resume screening simulation

## License

MIT

## Contact

For questions or improvements, open an issue or PR!