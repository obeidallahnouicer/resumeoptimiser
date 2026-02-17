# Development Guide

## Running the Server

### Development Mode
```bash
cd resumeoptimiser
source .venv/bin/activate
python run.py
```

Server will run on `http://localhost:8000`

### Production Mode (with Gunicorn)
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app --bind 0.0.0.0:8000
```

## API Documentation

Once server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Project Architecture

```
Request Flow:
  FastAPI Route (api/*)
    ↓
  Request Validation (Pydantic)
    ↓
  Service Function (services/*)
    ↓
  Business Logic (pure Python)
    ↓
  Response Model (Pydantic)
    ↓
  JSON Response
```

## Module Breakdown

### Ticket 1: Project Setup ✅
- Repository initialized with git
- Virtual environment configured
- All dependencies installed
- LaTeX template created

### Ticket 2: Base Skills Management
**Module:** `api/base_skills.py` + `services/skill_matcher.py`

**Endpoints:**
- `GET /api/v1/base-skills` - Retrieve base skills
- `POST /api/v1/base-skills` - Validate base skills

**Data:** `base_skills.json`

### Ticket 3: Job Description Parser
**Module:** `api/jd.py` + `services/jd_parser.py`

**Endpoints:**
- `POST /api/v1/jd/parse` - Parse job description

**Features:**
- Regex extraction (current)
- Fallback to OpenRouter LLM (future)

### Ticket 4: Skill Matching Engine
**Module:** `api/matching.py` + `services/skill_matcher.py`

**Endpoints:**
- `POST /api/v1/matching/skills` - Match skills

**Algorithm:**
- Direct matching (exact name match)
- Semantic matching (TF-IDF similarity)
- Configurable thresholds

### Ticket 5: Scoring Engine
**Module:** `api/scoring.py` + `services/scoring_engine.py`

**Endpoints:**
- `POST /api/v1/scoring/score` - Score CV

**Scoring Breakdown:**
- Stack Alignment (40 pts)
- Capability Match (20 pts)
- Seniority Fit (15 pts)
- Domain Relevance (10 pts)
- Sponsorship Feasibility (15 pts)

**Categories:**
- Green (80+): Strong fit
- Yellow (60-79): Moderate fit
- Red (0-59): Weak fit

### Ticket 6: CV Rewriter
**Module:** `api/rewriting.py` + `services/cv_rewriter.py`

**Endpoints:**
- `POST /api/v1/rewriting/rewrite` - Rewrite CV to LaTeX

**Features:**
- Truth-constrained (only uses base_skills.json)
- Dynamic emphasis of matched skills
- LaTeX syntax validation

### Ticket 7: PDF Compilation
**Module:** `api/pdf.py` + `services/pdf_compiler.py`

**Endpoints:**
- `POST /api/v1/pdf/compile` - Compile LaTeX to PDF

**Requirements:**
- pdflatex installed (part of TeX Live)

### Ticket 8: End-to-End Flow
**Module:** `api/generation.py`

**Endpoints:**
- `POST /api/v1/generation/generate` - Complete workflow

**Flow:**
1. Parse JD
2. Match skills
3. Score CV
4. Rewrite CV
5. Compile PDF
6. Return all results + logs

## Testing

### Run All Tests
```bash
pytest tests/
```

### Run With Coverage
```bash
pytest --cov=src tests/
```

### Manual Testing

#### Parse JD
```bash
curl -X POST http://localhost:8000/api/v1/jd/parse \
  -H "Content-Type: application/json" \
  -d '{"jd_text": "Looking for Python developer with React experience"}'
```

#### Match Skills
```bash
curl -X POST http://localhost:8000/api/v1/matching/skills \
  -H "Content-Type: application/json" \
  -d '{
    "jd_json": {
      "core_stack": ["Python", "React"],
      "secondary_stack": [],
      "domain": ["tech"],
      "seniority": "mid",
      "keywords": []
    }
  }'
```

#### End-to-End Generation
```bash
curl -X POST http://localhost:8000/api/v1/generation/generate \
  -H "Content-Type: application/json" \
  -d '{"jd_text": "Full job description here..."}'
```

## Configuration

All settings in `src/core/config.py`:

```python
# Server
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000

# LaTeX
LATEX_TIMEOUT = 30  # seconds
LATEX_INTERACTION_MODE = "nonstopmode"

# Scoring Thresholds
SCORE_GREEN_THRESHOLD = 80.0
SCORE_YELLOW_THRESHOLD = 60.0

# Skill Matching
MIN_TRANSFERABLE_SIMILARITY = 0.5
MIN_DIRECT_SIMILARITY = 0.95
```

Override with environment variables:
```bash
export SERVER_PORT=8080
export DEBUG=True
```

## Truth Constraint Implementation

The system ensures no hallucination:

1. **Single Source of Truth**: `base_skills.json`
2. **Immutable Data**: Skills loaded once at startup
3. **No External Data**: CV only uses what's in base_skills.json
4. **Matching Only**: LLM would only match, never generate
5. **Transparent**: All cv content directly traceable to source

## Extending the API

### Adding a New Endpoint

1. **Create service function** (`src/services/my_service.py`)
```python
def my_service(input_data) -> OutputModel:
    """Pure business logic, no FastAPI dependency."""
    return result
```

2. **Create API route** (`src/api/my_route.py`)
```python
from fastapi import APIRouter

router = APIRouter(prefix="/my-feature", tags=["my-feature"])

@router.post("/endpoint", response_model=OutputModel)
async def my_endpoint(request: InputRequest):
    return await my_service(request.data)
```

3. **Register router** (`src/main.py`)
```python
from src.api import my_route
app.include_router(my_route.router, prefix=API_PREFIX)
```

## Error Handling

All endpoints follow consistent error patterns:

```python
raise HTTPException(
    status_code=400,  # or 500
    detail="Specific error message"
)
```

Common statuses:
- 200: Success
- 400: Bad request (validation failed)
- 404: Not found
- 500: Server error

## Performance Optimization

### Current Optimizations
- Embeddings computed once per request
- Base skills loaded at startup
- Minimal memory overhead

### Future Optimizations
- Cache parsed JDs
- Pre-compute skill embeddings
- Background PDF compilation
- Database for CV history

## Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  resume-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SERVER_HOST=0.0.0.0
      - SERVER_PORT=8000
```

### Environment Variables
```bash
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=False
```

## Troubleshooting

### "pdflatex not found"
Install TeX Live:
```bash
# Ubuntu/Debian
sudo apt-get install texlive-full

# macOS
brew install mactex

# Fedora
sudo dnf install texlive-scheme-full
```

### "Base skills not loaded"
Check `base_skills.json` exists and is valid JSON:
```bash
python -m json.tool base_skills.json
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

## Code Quality

### Format Code
```bash
black src/
```

### Lint
```bash
flake8 src/
```

### Type Check
```bash
mypy src/
```

### All Together
```bash
black src/ && flake8 src/ && mypy src/ && pytest
```

## Contributing

1. Create feature branch: `git checkout -b features/my-feature`
2. Make changes
3. Run tests: `pytest tests/`
4. Format code: `black src/`
5. Push and create PR

## License

MIT