# Architecture Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RESUME OPTIMISER API                     │
└─────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                     HTTP CLIENT                            │
│  (Browser, curl, Postman, Mobile App, etc.)               │
└────────────┬─────────────────────────────────────┬────────┘
             │                                     │
      Request│                            Response│
             │                                     │
    ┌────────▼────────────────────────────────────▼────────┐
    │              FASTAPI (src/main.py)                   │
    │  - CORS enabled                                      │
    │  - Error handling                                    │
    │  - Request validation                               │
    └────────┬────────────────────────────────────┬────────┘
             │                                     │
    ┌────────▼──────────────────────────────────────────────┐
    │         API ROUTERS (src/api/*)                      │
    │                                                       │
    │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
    │  │ base_skills │  │      jd      │  │  matching  │  │
    │  │   Ticket 2  │  │  Ticket 3    │  │ Ticket 4   │  │
    │  └─────────────┘  └──────────────┘  └────────────┘  │
    │                                                       │
    │  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  │
    │  │  scoring    │  │  rewriting   │  │    pdf     │  │
    │  │  Ticket 5   │  │  Ticket 6    │  │ Ticket 7   │  │
    │  └─────────────┘  └──────────────┘  └────────────┘  │
    │                                                       │
    │  ┌──────────────────────────────────────────────┐   │
    │  │         generation (Ticket 8)                │   │
    │  │  Orchestrates all tickets into one flow      │   │
    │  └──────────────────────────────────────────────┘   │
    └──────┬──────────────────────────────┬────────────────┘
           │                              │
    ┌──────▼──────────────────────────────▼────────────────┐
    │      REQUEST VALIDATION (Pydantic)                  │
    │  - Type checking                                    │
    │  - Schema validation                               │
    │  - Error messages                                  │
    └──────┬──────────────────────────────┬────────────────┘
           │                              │
    ┌──────▼──────────────────────────────▼────────────────┐
    │    BUSINESS LOGIC SERVICES (src/services/*)        │
    │                                                       │
    │  ┌──────────────┐  Pure Python functions            │
    │  │  jd_parser   │  - No FastAPI dependency          │
    │  │  - Regex     │  - Easy to test                   │
    │  │  - LLM ready │  - Reusable elsewhere            │
    │  └──────────────┘                                    │
    │                                                       │
    │  ┌──────────────┐                                    │
    │  │skill_matcher │  TF-IDF Embeddings                │
    │  │- Direct      │  Cosine Similarity               │
    │  │- Semantic    │  Min Thresholds                  │
    │  └──────────────┘                                    │
    │                                                       │
    │  ┌──────────────┐                                    │
    │  │scoring_engine│  Weighted Scoring                 │
    │  │- Stack (40)  │  - 5 dimensions                   │
    │  │- Capability  │  - Green/Yellow/Red               │
    │  │- Seniority   │                                    │
    │  │- Domain (10) │                                    │
    │  │- Sponsor (15)│                                    │
    │  └──────────────┘                                    │
    │                                                       │
    │  ┌──────────────┐                                    │
    │  │ cv_rewriter  │  Jinja2 Template                  │
    │  │- LaTeX gen   │  - Dynamic sections               │
    │  │- Truth-safe  │  - No hallucination               │
    │  │- Validation  │                                    │
    │  └──────────────┘                                    │
    │                                                       │
    │  ┌──────────────┐                                    │
    │  │pdf_compiler  │  subprocess + pdflatex            │
    │  │- LaTeX → PDF │  - Error handling                 │
    │  │- Validation  │                                    │
    │  └──────────────┘                                    │
    └──────┬──────────────────────────────┬────────────────┘
           │                              │
    ┌──────▼──────────────────────────────▼────────────────┐
    │      DATA ACCESS LAYER                              │
    │                                                       │
    │  base_skills.json ──────┐                           │
    │  (Truth file)           │                           │
    │                         ├──→ Configuration          │
    │  src/core/config.py ────┤   & Constants             │
    │  (Settings)             │                           │
    │                         └──→ Immutable data         │
    │                                                       │
    │  External Systems:                                  │
    │  ├─ pdflatex (PDF compilation)                     │
    │  ├─ sklearn (ML/similarity)                        │
    │  ├─ jinja2 (template rendering)                    │
    │  └─ OpenRouter (LLM - future)                      │
    └────────────────────────────────────────────────────┘
```

## Request Flow: End-to-End CV Generation

```
CLIENT REQUEST
    │
    │ POST /api/v1/generation/generate
    │ {"jd_text": "Senior Python engineer..."}
    │
    ▼
FASTAPI (src/main.py)
    │ Validate input
    │
    ▼
api/generation.py (Ticket 8 orchestrator)
    │
    ├──→ Step 1: PARSE JD
    │    │
    │    ▼
    │    services/jd_parser.py
    │    ├─ Extract tech stack
    │    ├─ Extract seniority
    │    ├─ Extract domain
    │    └─ Return ParsedJobDescription
    │
    ├──→ Step 2: MATCH SKILLS
    │    │
    │    ▼
    │    services/skill_matcher.py
    │    ├─ Load base_skills.json
    │    ├─ Compute TF-IDF embeddings
    │    ├─ Find direct matches
    │    ├─ Find semantic matches
    │    └─ Return SkillMatchResult
    │
    ├──→ Step 3: SCORE CV
    │    │
    │    ▼
    │    services/scoring_engine.py
    │    ├─ Stack alignment (40 pts)
    │    ├─ Capability match (20 pts)
    │    ├─ Seniority fit (15 pts)
    │    ├─ Domain relevance (10 pts)
    │    ├─ Sponsorship feasibility (15 pts)
    │    └─ Return CVScore + category
    │
    ├──→ Step 4: REWRITE CV
    │    │
    │    ▼
    │    services/cv_rewriter.py
    │    ├─ Render Jinja2 template
    │    ├─ Emphasize matched skills
    │    ├─ Build experience section
    │    ├─ Validate LaTeX syntax
    │    └─ Return RewrittenCV
    │
    ├──→ Step 5: COMPILE PDF
    │    │
    │    ▼
    │    services/pdf_compiler.py
    │    ├─ Write LaTeX file
    │    ├─ Run pdflatex subprocess
    │    ├─ Check for errors
    │    └─ Return PDF path or error
    │
    └──→ Return EndToEndResponse
         ├─ parsed_jd
         ├─ skill_match
         ├─ cv_score
         ├─ rewritten_cv
         ├─ pdf_path
         └─ logs (step-by-step)
            │
            ▼
        CLIENT RECEIVES
        Complete CV package


## Truth Constraint Guarantee

```
┌─────────────────────────────────────────────┐
│      base_skills.json (Single Source)       │
│  (Your ACTUAL skills and experience)        │
└────────┬────────────────────────────────────┘
         │ (loaded once at startup)
         │
    ┌────▼────────────────────────────────────┐
    │   MATCHED AGAINST JD REQUIREMENTS       │
    │  (never added, only compared)            │
    └────┬────────────────────────────────────┘
         │
    ┌────▼────────────────────────────────────┐
    │   REWRITTEN TO LATEX (only emphasis)    │
    │  (same content, better layout)           │
    └────┬────────────────────────────────────┘
         │
    ┌────▼────────────────────────────────────┐
    │     COMPILED TO PDF                     │
    │   (no new content added)                 │
    └────────────────────────────────────────┘

GUARANTEE: No hallucination, no made-up skills,
           only your actual experience emphasized
           for the specific job.
```

## Configuration Management

```
src/core/config.py
    │
    ├─ API_VERSION = "v1"
    ├─ API_PREFIX = "/api/v1"
    │
    ├─ SERVER_HOST (from env: 0.0.0.0)
    ├─ SERVER_PORT (from env: 8000)
    ├─ DEBUG (from env: False)
    │
    ├─ BASE_SKILLS_FILE = "./base_skills.json"
    ├─ LATEX_TEMPLATE_FILE = "./template.tex"
    ├─ BUILD_DIR = "./build"
    │
    ├─ LATEX_TIMEOUT = 30 seconds
    ├─ LATEX_INTERACTION_MODE = "nonstopmode"
    │
    ├─ SCORE_GREEN_THRESHOLD = 80.0
    ├─ SCORE_YELLOW_THRESHOLD = 60.0
    │
    ├─ MIN_TRANSFERABLE_SIMILARITY = 0.5
    ├─ MIN_DIRECT_SIMILARITY = 0.95
    │
    ├─ CORE_TECH_STACK = {...}
    ├─ SECONDARY_TECH_STACK = {...}
    └─ DOMAIN_KEYWORDS = {...}

All settable via environment variables
or config file (future enhancement).
```

## Module Dependency Graph

```
                    src/main.py
                    (FastAPI factory)
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    src/api/*      src/models/    src/core/
    (Routes)       schemas.py      config.py
        │                │              │
        └────────┬───────┴──────┬───────┘
                 │              │
                 ▼              ▼
            src/services/*  CONSTANTS
            (Business Logic)
                 │
        ┌────────┼────────┬────────┬───────┐
        │        │        │        │       │
        ▼        ▼        ▼        ▼       ▼
      JD      Skill    Scoring   CV     PDF
     Parse    Matcher  Engine   Rewriter Compiler
        │        │        │        │       │
        └────────┴────────┴────────┴───────┘
                 │
                 ▼
        External Dependencies:
        ├─ sklearn (embeddings)
        ├─ jinja2 (templates)
        ├─ numpy (arrays)
        ├─ pandas (data)
        ├─ subprocess (latex)
        └─ requests (http)
```