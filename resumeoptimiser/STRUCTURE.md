# Project Structure

```
resumeoptimiser/
├── src/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory
│   │
│   ├── api/                       # API Routes (separated by feature)
│   │   ├── __init__.py
│   │   ├── base_skills.py        # Ticket 2: Base skills endpoints
│   │   ├── jd.py                 # Ticket 3: JD parsing endpoints
│   │   ├── matching.py           # Ticket 4: Skill matching endpoints
│   │   ├── scoring.py            # Ticket 5: Scoring endpoints
│   │   ├── rewriting.py          # Ticket 6: CV rewriting endpoints
│   │   ├── pdf.py                # Ticket 7: PDF compilation endpoints
│   │   └── generation.py         # Ticket 8: End-to-end generation
│   │
│   ├── models/                    # Pydantic schemas & validation
│   │   ├── __init__.py
│   │   └── schemas.py            # All request/response models
│   │
│   ├── services/                  # Business logic & core algorithms
│   │   ├── __init__.py
│   │   ├── jd_parser.py          # Job description parsing
│   │   ├── skill_matcher.py      # Semantic skill matching
│   │   ├── scoring_engine.py     # CV scoring algorithm
│   │   ├── cv_rewriter.py        # LaTeX CV generation
│   │   └── pdf_compiler.py       # LaTeX to PDF compilation
│   │
│   ├── core/                      # Configuration & constants
│   │   ├── __init__.py
│   │   └── config.py             # All settings & constants
│   │
│   └── utils/                     # Utility functions
│       └── __init__.py
│
├── run.py                          # Entry point
├── requirements.txt                # Dependencies
├── base_skills.json               # User truth file (your actual skills)
├── template.tex                   # LaTeX template
├── .gitignore
├── .git/                          # Git repository
├── .venv/                         # Virtual environment
├── build/                         # Compiled PDFs (auto-created)
└── test_output/                   # Test results (auto-created)
```

## Directory Organization

### `src/api/`
**Purpose:** HTTP endpoints grouped by feature (REST routes)
- Each file = one feature set
- Clean separation of concerns
- Easy to test and maintain

### `src/models/`
**Purpose:** Data validation layer (Pydantic)
- Single `schemas.py` with all models
- Clear request/response contracts
- Type safety for entire API

### `src/services/`
**Purpose:** Business logic & algorithms (no HTTP details)
- Pure Python functions
- Testable without FastAPI
- Reusable across projects
- No dependency on FastAPI

### `src/core/`
**Purpose:** Configuration & constants
- `config.py`: All settings in one place
- Environment variables
- Tech stack definitions
- Threshold values

## Key Design Principles

1. **Separation of Concerns**
   - Routes (HTTP) ≠ Business Logic
   - Services are pure functions
   - Models validate data

2. **Truth Constraint**
   - All CV content from `base_skills.json`
   - No hallucination possible
   - Immutable source of truth

3. **Modularity**
   - Each ticket = independent feature
   - Easy to add/remove features
   - Minimal coupling between modules

4. **Testability**
   - Services can be tested without FastAPI
   - No global state except base_skills
   - Clear inputs/outputs

5. **Production Ready**
   - Type hints throughout
   - Error handling
   - Logging ready
   - Configuration management