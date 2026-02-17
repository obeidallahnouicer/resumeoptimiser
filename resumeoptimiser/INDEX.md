# 📚 Documentation Index

## Quick Start

1. **New to the project?** → Start with [README.md](README.md)
2. **Want to understand the design?** → Read [ARCHITECTURE.md](ARCHITECTURE.md)
3. **Ready to develop?** → Follow [DEVELOPMENT.md](DEVELOPMENT.md)
4. **Want to know what changed?** → Check [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)
5. **Migrating from old code?** → See [MIGRATION.md](MIGRATION.md)
6. **Curious about structure?** → Explore [STRUCTURE.md](STRUCTURE.md)

---

## 📖 Documentation Files

### [README.md](README.md)
**Purpose:** User guide and project overview

**Contains:**
- Project description and features
- Installation instructions
- API endpoint examples
- Configuration guide
- Scoring breakdown
- Troubleshooting

**Read this if:** You're new to the project or need usage instructions

---

### [ARCHITECTURE.md](ARCHITECTURE.md)
**Purpose:** System design and architecture diagrams

**Contains:**
- System architecture overview
- Request flow diagrams
- Truth constraint guarantee
- Configuration management
- Module dependency graph
- Visual ASCII diagrams

**Read this if:** You want to understand how everything fits together

---

### [DEVELOPMENT.md](DEVELOPMENT.md)
**Purpose:** Developer guide for local development

**Contains:**
- Running the server (dev & production)
- API documentation links
- Module breakdown (Tickets 1-8)
- Manual testing examples
- Configuration options
- Performance optimization
- Docker deployment
- Troubleshooting
- Code quality tools

**Read this if:** You're contributing code or deploying

---

### [STRUCTURE.md](STRUCTURE.md)
**Purpose:** Project file organization explanation

**Contains:**
- Directory tree structure
- Directory purposes
- Key design principles
- Separation of concerns
- Modularity explanation
- Testability notes
- Production readiness checklist

**Read this if:** You need to understand file organization

---

### [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md)
**Purpose:** Summary of production refactoring

**Contains:**
- Before/after structure comparison
- Directory breakdown
- Architecture principles
- Code statistics
- Request flow example
- Key improvements
- Next steps

**Read this if:** You want to know what changed and why

---

### [MIGRATION.md](MIGRATION.md)
**Purpose:** Migration guide from old to new structure

**Contains:**
- What was changed
- Breaking changes (none!)
- Development workflow updates
- Import updates
- Git integration
- Deployment changes
- Rollback instructions

**Read this if:** You have existing code that needs updating

---

## 🗂️ Project File Locations

### Documentation Files (Root Level)
```
├── README.md              # User guide
├── ARCHITECTURE.md        # System design
├── DEVELOPMENT.md         # Developer guide
├── STRUCTURE.md           # File organization
├── REFACTOR_SUMMARY.md    # What changed
├── MIGRATION.md           # Migration guide
└── INDEX.md              # This file
```

### Configuration Files (Root Level)
```
├── run.py                 # Entry point
├── requirements.txt       # Dependencies
├── base_skills.json       # User skills (truth file)
├── template.tex           # LaTeX template
├── .gitignore             # Git exclusions
└── client.py              # API client utility
```

### Source Code (src/)
```
src/
├── main.py                # FastAPI factory
├── api/                   # HTTP routes
│   ├── base_skills.py     # Ticket 2
│   ├── jd.py              # Ticket 3
│   ├── matching.py        # Ticket 4
│   ├── scoring.py         # Ticket 5
│   ├── rewriting.py       # Ticket 6
│   ├── pdf.py             # Ticket 7
│   └── generation.py      # Ticket 8
├── services/              # Business logic
│   ├── jd_parser.py
│   ├── skill_matcher.py
│   ├── scoring_engine.py
│   ├── cv_rewriter.py
│   └── pdf_compiler.py
├── models/
│   └── schemas.py         # Pydantic models
├── core/
│   └── config.py          # Configuration
└── utils/                 # Utilities
```

---

## 🎯 By Use Case

### "I want to use the API"
1. [README.md](README.md) - Features and usage
2. [DEVELOPMENT.md](DEVELOPMENT.md#running-the-server) - How to run
3. http://localhost:8000/docs - Interactive API docs

### "I want to understand the design"
1. [ARCHITECTURE.md](ARCHITECTURE.md) - System overview
2. [STRUCTURE.md](STRUCTURE.md) - File organization
3. [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md) - Improvements

### "I want to contribute code"
1. [DEVELOPMENT.md](DEVELOPMENT.md) - Dev setup
2. [STRUCTURE.md](STRUCTURE.md) - Code organization
3. [ARCHITECTURE.md](ARCHITECTURE.md#adding-a-new-endpoint) - Adding features

### "I want to deploy"
1. [DEVELOPMENT.md](DEVELOPMENT.md#deployment) - Deployment options
2. [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md) - Production setup
3. [MIGRATION.md](MIGRATION.md#deployment) - Deployment changes

### "I'm migrating from old code"
1. [MIGRATION.md](MIGRATION.md) - Migration guide
2. [REFACTOR_SUMMARY.md](REFACTOR_SUMMARY.md) - What changed
3. [DEVELOPMENT.md](DEVELOPMENT.md#error-handling) - New patterns

---

## 🔍 Finding Information

### API Endpoints
- **All endpoints:** [README.md](README.md#api-endpoints)
- **Endpoint details:** [DEVELOPMENT.md](DEVELOPMENT.md#module-breakdown)
- **Request examples:** [DEVELOPMENT.md](DEVELOPMENT.md#testing)

### Configuration
- **All settings:** [DEVELOPMENT.md](DEVELOPMENT.md#configuration)
- **Environment variables:** [DEVELOPMENT.md](DEVELOPMENT.md#environment-variables)
- **Tech stack:** [STRUCTURE.md](STRUCTURE.md)

### Code Organization
- **Where is X?** [STRUCTURE.md](STRUCTURE.md#project-structure)
- **How do routers work?** [ARCHITECTURE.md](ARCHITECTURE.md#api-routers)
- **How do services work?** [ARCHITECTURE.md](ARCHITECTURE.md#services)

### Troubleshooting
- **Server issues:** [DEVELOPMENT.md](DEVELOPMENT.md#troubleshooting)
- **Not working?** [MIGRATION.md](MIGRATION.md)
- **API errors:** [DEVELOPMENT.md](DEVELOPMENT.md#error-handling)

---

## 📊 Quick Reference

### Running the Server
```bash
python run.py                              # Development
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app  # Production
```

### Testing an Endpoint
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/base-skills
curl -X POST http://localhost:8000/api/v1/jd/parse \
  -H "Content-Type: application/json" \
  -d '{"jd_text": "..."}'
```

### API Documentation
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### Project Statistics
- **Total Python files:** 21 (organized in src/)
- **API endpoints:** 7 main endpoints
- **Documentation files:** 6 guides
- **Tickets implemented:** 8/8 ✅

---

## 🚀 Next Steps

1. **Read [README.md](README.md)** for project overview
2. **Run [DEVELOPMENT.md](DEVELOPMENT.md#running-the-server) setup** to start developing
3. **Explore [ARCHITECTURE.md](ARCHITECTURE.md)** to understand the design
4. **Visit http://localhost:8000/docs** to explore the API
5. **Read [DEVELOPMENT.md](DEVELOPMENT.md#extending-the-api)** to add features

---

## 📞 Support

- **Issues?** See [DEVELOPMENT.md](DEVELOPMENT.md#troubleshooting)
- **Confused about structure?** See [STRUCTURE.md](STRUCTURE.md)
- **Something not working after refactor?** See [MIGRATION.md](MIGRATION.md)
- **Want to understand the system?** See [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 📅 Document Versions

- **README.md** - Latest
- **ARCHITECTURE.md** - Latest
- **DEVELOPMENT.md** - Latest
- **STRUCTURE.md** - Latest
- **REFACTOR_SUMMARY.md** - Latest
- **MIGRATION.md** - Latest
- **INDEX.md** - Latest (this file)

All documentation was updated during the production refactor. 🎉