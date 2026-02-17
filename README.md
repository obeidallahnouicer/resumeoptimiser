# 📚 Resume Optimiser - Complete Documentation

> **⭐ Start here if new**: Read [SUMMARY.md](./SUMMARY.md) for complete overview, then run `./setup.sh`

## 📖 Documentation Guide

### 🎯 Quick Links
- **New to project?** → Read [SUMMARY.md](./SUMMARY.md)
- **Setting up?** → Run [setup.sh](./setup.sh) then read [INTEGRATION.md](./INTEGRATION.md)
- **Need API key?** → See [OPENROUTER_SETUP.md](./OPENROUTER_SETUP.md)
- **Having issues?** → Check [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Coding?** → Use [QUICK_REF.md](./QUICK_REF.md)
- **Verifying setup?** → Run [test-setup.sh](./test-setup.sh)

---

## 🚀 For First-Time Setup

### Configuration & Setup
- ✅ **Backend `.env`** with all required variables
- ✅ **Frontend `.env`** with Vite environment variables  
- ✅ **Backend config system** (`config.py`) that loads from `.env`
- ✅ **Frontend API client** that reads from `.env`
- ✅ **CORS configuration** for local development
- ✅ **Automated setup script** (`setup.sh`)
- ✅ **Development startup script** (`start-dev.sh`)

### Backend Integration
- ✅ **File upload endpoint** - Accepts PDF + JD text via FormData
- ✅ **File validation** - Size (50MB) and type (PDF) checks
- ✅ **Multi-step pipeline**:
  1. ✅ PDF upload handling with temp storage
  2. ✅ JD parsing with LLM
  3. ✅ Skill matching with semantic similarity
  4. ✅ Multi-factor scoring (5 dimensions, 100 points total)
  5. ✅ CV rewriting with LaTeX
  6. ✅ PDF compilation to file
  7. ✅ Comprehensive logging with all steps

- ✅ **Logging system** with [STAGE] prefixes:
  - `[INIT]` - Initialization
  - `[UPLOAD]` - File upload handling
  - `[PARSE]` - JD parsing
  - `[MATCH]` - Skill matching
  - `[SCORE]` - Scoring
  - `[GEN]` - CV generation
  - `[COMPILE]` - PDF compilation
  - `[SUCCESS]` or `[ERROR]` - Final status

### Frontend Integration
- ✅ **Updated API client** (`services/api.ts`):
  - Reads API URL from environment variables
  - Implements timeout handling (default 60s)
  - File size and type validation
  - Proper error messages
  - Graceful fallback to mock mode

- ✅ **Environment variables** in `cyberresume-optimiser/.env`:
  - `VITE_API_URL` - Backend API endpoint
  - `VITE_API_TIMEOUT` - Request timeout
  - `VITE_ENABLE_MOCK_MODE` - Test without backend
  - `VITE_MAX_FILE_SIZE_MB` - File upload limit
  - `VITE_ALLOWED_FILE_TYPES` - Accepted file types

- ✅ **Complete UI workflow**:
  1. ✅ PDF upload with drag-and-drop
  2. ✅ Job description text input
  3. ✅ Loading state with spinner
  4. ✅ Results dashboard with:
     - Overall score gauge
     - Status indicator (GREEN/YELLOW/RED)
     - Parsed JD information
     - Skill analysis (direct + semantic + gaps)
     - Scoring breakdown visualization
     - LaTeX source preview
     - Live processing logs
     - Download button

### Documentation
- ✅ **`INTEGRATION.md`** - Comprehensive integration guide (400+ lines)
- ✅ **`QUICKSTART.md`** - Quick reference for common tasks
- ✅ **`CHECKLIST.md`** - Implementation progress tracker
- ✅ **`.env.example` files** - Environment templates
- ✅ **This README** - Overview and summary

### Docker & Deployment
- ✅ **Backend Dockerfile** - Python 3.11 with LaTeX
- ✅ **Frontend Dockerfile** - Node.js with Vite
- ✅ **docker-compose.yml** - Full stack orchestration
- ✅ **Volume mounts** for development

---

## 📋 Workflow Process

```
User Interface (React)
         ↓
    [Upload PDF]
    [Paste JD]
    [Click Submit]
         ↓
API Request (FormData)
  - jd_text: string
  - cv_file: File (optional)
         ↓
Backend FastAPI
         ↓
1. [UPLOAD] Store PDF temporarily
2. [PARSE] Extract JD requirements (LLM)
   → Core tech stack
   → Secondary tech stack  
   → Domain keywords
   → Seniority level
         ↓
3. [MATCH] Match candidate skills
   → Direct matches (exact skills)
   → Semantic matches (transferable skills)
   → Skill gaps
         ↓
4. [SCORE] Calculate 5-factor score
   → Stack alignment (40 pts)
   → Capability match (20 pts)
   → Seniority fit (15 pts)
   → Domain relevance (10 pts)
   → Sponsorship feasibility (15 pts)
   → Total: 0-100
   → Category: GREEN/YELLOW/RED
         ↓
5. [GEN] Rewrite CV with LaTeX
   → Inject matched skills
   → Generate experience section
   → Generate skills section
   → Create LaTeX document
         ↓
6. [COMPILE] Compile LaTeX → PDF
   → Run pdflatex subprocess
   → Save to build/ directory
         ↓
API Response (JSON)
  - parsed_jd: { core_stack, seniority, domain, ... }
  - skill_match: { matches, total_matched, total_jd_requirements }
  - cv_score: { total_score, category, breakdown }
  - rewritten_cv: { latex_content, experience_section, skills_section }
  - pdf_path: string
  - logs: string[]
         ↓
Frontend Display
  - Score gauge
  - Status badge
  - Skill analysis cards
  - Radar and bar charts
  - LaTeX preview
  - Processing logs
         ↓
    [Download PDF]
```

---

## 🚀 Quick Start

### 1. First Time Setup
```bash
chmod +x setup.sh
./setup.sh

# Edit backend .env and add OpenAI API key
nano resumeoptimiser/.env
```

### 2. Start Development Servers
```bash
chmod +x start-dev.sh
./start-dev.sh
```

### 3. Open Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 📁 File Structure

```
resumeshit/
├── setup.sh                         # Automated setup
├── start-dev.sh                     # Start both servers
├── docker-compose.yml               # Docker orchestration
├── INTEGRATION.md                   # Full guide
├── QUICKSTART.md                    # Quick reference
├── CHECKLIST.md                     # Progress tracker
│
├── resumeoptimiser/                 # Backend (Python/FastAPI)
│   ├── .env                        # Backend config (created from .env.example)
│   ├── .env.example                # Template
│   ├── Dockerfile                  # Docker image
│   ├── requirements.txt            # Python dependencies
│   ├── run.py                      # Entry point (loads .env)
│   │
│   ├── src/
│   │   ├── main.py                 # FastAPI app with CORS + .env config
│   │   ├── core/
│   │   │   └── config.py           # Config reader (loads .env)
│   │   └── api/
│   │       └── generation.py       # Main endpoint (POST /generation/generate)
│   │
│   ├── build/                      # Generated PDFs
│   ├── temp_uploads/               # Temporary uploaded files
│   └── base_skills.json            # Candidate skills database
│
└── cyberresume-optimiser/          # Frontend (React/TypeScript)
    ├── .env                        # Frontend config (created from .env.example)
    ├── .env.example                # Template
    ├── Dockerfile                  # Docker image
    ├── package.json                # Node.js dependencies
    ├── vite.config.ts              # Vite config
    ├── tsconfig.json               # TypeScript config
    ├── App.tsx                     # Main React component
    ├── types.ts                    # TypeScript interfaces
    │
    └── services/
        └── api.ts                  # API client (reads .env)
```

---

## 🔧 Environment Variables

### Backend (`resumeoptimiser/.env`)
```env
SERVER_HOST=0.0.0.0                 # Server bind address
SERVER_PORT=8000                    # Server port
DEBUG=False                          # Debug mode (reload on code change)

OPENAI_API_KEY=sk-...              # 🔴 REQUIRED - Your OpenAI API key
OPENAI_MODEL=gpt-4o-mini           # Model to use

MAX_UPLOAD_SIZE_MB=50              # Max file upload size
UPLOAD_TEMP_DIR=./temp_uploads     # Temp file location
BUILD_OUTPUT_DIR=./build            # Generated PDFs location

FRONTEND_URL=http://localhost:3000 # For CORS
LOG_LEVEL=info                      # Log level
```

### Frontend (`cyberresume-optimiser/.env`)
```env
VITE_API_URL=http://localhost:8000/api/v1  # Backend API URL
VITE_API_TIMEOUT=60000                      # Request timeout (ms)
VITE_ENABLE_MOCK_MODE=false                 # Use mock data (no backend)
VITE_MAX_FILE_SIZE_MB=50                    # Max upload size
VITE_ALLOWED_FILE_TYPES=application/pdf     # Accepted file types
```

---

## 🎯 Scoring System

| Factor | Points | Measures |
|--------|--------|----------|
| **Stack Alignment** | 40 | How well your skills match required technologies |
| **Capability Match** | 20 | Depth of experience in required areas |
| **Seniority Fit** | 15 | Experience level matches job level |
| **Domain Relevance** | 10 | Industry/domain experience |
| **Sponsorship** | 15 | Visa sponsorship likelihood |
| **TOTAL** | **100** | Overall fit score |

### Score Categories
- 🟢 **GREEN** (80+) - Excellent fit, high likelihood of interview
- 🟡 **YELLOW** (60-79) - Good fit, competitive candidate  
- 🔴 **RED** (<60) - Needs work, major gaps

---

## 📦 Dependencies

### Backend
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `openai` - GPT integration
- `python-dotenv` - Environment variables
- `requests` - HTTP client
- `pylatex` - LaTeX generation
- And others (see `requirements.txt`)

### Frontend
- `react` - UI framework
- `typescript` - Type safety
- `vite` - Build tool
- `tailwindcss` - Styling
- `framer-motion` - Animations
- `recharts` - Charts
- And others (see `package.json`)

---

## ✨ Features

### Backend Features
- ✅ Multipart file upload with validation
- ✅ LLM-powered JD parsing
- ✅ Semantic skill matching
- ✅ Multi-factor scoring algorithm
- ✅ LaTeX CV generation
- ✅ PDF compilation
- ✅ Structured logging
- ✅ CORS enabled
- ✅ Environment variable configuration
- ✅ Error handling and validation

### Frontend Features
- ✅ Drag-and-drop file upload
- ✅ Rich text input for job description
- ✅ Real-time file validation
- ✅ Loading state with animations
- ✅ Responsive dashboard
- ✅ Multiple chart visualizations
- ✅ Skill analysis display
- ✅ LaTeX source preview
- ✅ Live processing logs
- ✅ PDF download
- ✅ Mock mode for testing
- ✅ Cyberpunk theme
- ✅ Fully accessible UI

---

## 🧪 Testing

### Manual Testing Checklist
```
[ ] Setup runs without errors
[ ] Both servers start successfully
[ ] Frontend loads at http://localhost:3000
[ ] Backend responds at http://localhost:8000/health
[ ] Can upload PDF file (or skip)
[ ] Can paste job description
[ ] Processing completes in 30-60 seconds
[ ] Results display all components
[ ] Score is between 0-100
[ ] Category is GREEN, YELLOW, or RED
[ ] Logs show all processing steps
[ ] Can download PDF
[ ] Downloaded file is valid PDF
```

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Full workflow (no file)
curl -X POST http://localhost:8000/api/v1/generation/generate \
  -F "jd_text=Senior Python Developer with FastAPI experience"

# With file
curl -X POST http://localhost:8000/api/v1/generation/generate \
  -F "jd_text=Senior Python Developer" \
  -F "cv_file=@resume.pdf"
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend won't start | Check port 8000 (try 8001), ensure `.env` exists |
| OpenAI API errors | Get key from https://platform.openai.com/api-keys |
| Frontend can't reach backend | Check `VITE_API_URL`, verify backend running |
| File upload fails | Check file is PDF, under 50MB, no special chars |
| PDF download 404 | Restart backend, check build/ directory exists |
| Port already in use | Change `SERVER_PORT` in backend `.env` |

---

## 📖 Documentation Files

1. **INTEGRATION.md** (400+ lines)
   - Complete integration details
   - All endpoints documentation
   - Features breakdown
   - Production deployment guide
   - Security considerations
   - Performance optimization tips

2. **QUICKSTART.md** (300+ lines)
   - Quick reference guide
   - Common commands
   - Keyboard shortcuts
   - Troubleshooting tips
   - Advanced configuration

3. **CHECKLIST.md** (400+ lines)
   - Progress tracker
   - TODOs for next phases
   - Testing checklist
   - Security hardening tasks
   - Production features

4. **This file**
   - High-level overview
   - Architecture summary
   - Quick start guide

---

## 🚀 Next Steps

### Immediate (Required)
1. Add OPENAI_API_KEY to `resumeoptimiser/.env`
2. Run `./setup.sh` if not done
3. Run `./start-dev.sh`
4. Test the workflow

### Short-term (1-2 weeks)
1. Implement PDF text extraction using pdfplumber
2. Add unit tests for backend services
3. Add E2E tests for full workflow
4. Add user authentication

### Medium-term (1-2 months)
1. Add database for user profiles
2. Implement CV versioning/history
3. Add email notifications
4. Deploy to staging environment
5. Implement monitoring and logging

### Long-term (3+ months)
1. Production deployment
2. Security audit and hardening
3. Performance optimization
4. Advanced features:
   - Multiple JD comparison
   - Interview prep mode
   - Skills gap analysis
   - Learning recommendations

---

## 💡 Key Technical Decisions

1. **Environment Variables**: Using `python-dotenv` (backend) and Vite's `import.meta.env` (frontend)
2. **File Upload**: FormData with chunked reading for reliability
3. **Logging**: Structured [STAGE] prefixes for clarity and debugging
4. **Error Handling**: Graceful fallback to mock data if backend unavailable
5. **CORS**: Properly configured for localhost development
6. **Validation**: Client-side AND server-side for security
7. **Docker**: Development-focused with volume mounts for hot reload

---

## 📞 Support

For issues or questions:

1. Check **QUICKSTART.md** for common troubleshooting
2. Review **INTEGRATION.md** for detailed information  
3. Check backend logs: Terminal running backend
4. Check frontend logs: Browser console (F12)
5. Check API docs: http://localhost:8000/docs (when backend running)

---

## 🎓 Learning Resources

- FastAPI: https://fastapi.tiangolo.com/
- React: https://react.dev/
- TypeScript: https://www.typescriptlang.org/
- Vite: https://vitejs.dev/
- Tailwind: https://tailwindcss.com/
- OpenAI API: https://platform.openai.com/docs/

---

## ✅ Status Summary

| Area | Status | Details |
|------|--------|---------|
| Backend Integration | ✅ Complete | All 7 steps implemented |
| Frontend Integration | ✅ Complete | Full UI and API client |
| Configuration | ✅ Complete | .env files and loaders |
| Documentation | ✅ Complete | 4 comprehensive guides |
| Docker | ✅ Complete | Ready for containerization |
| **Testing** | 🟡 TODO | Unit, integration, E2E tests |
| **PDF Extraction** | 🟡 TODO | Placeholder needs implementation |
| **Auth** | 🟡 TODO | Required for production |
| **Database** | 🟡 TODO | For user profiles/history |
| **Production Ready** | 🟡 50% | Core done, hardening needed |

---

**Ready to go!** 🚀

Proceed to **QUICKSTART.md** for immediate setup instructions.
# resumeoptimiser
