# Backend Logging & LLM Configuration

## Logging Setup

### Overview
Comprehensive logging has been implemented throughout the Resume Optimiser backend with multiple log files and handlers.

### Log Files Location
All logs are stored in `/resumeoptimiser/logs/` directory:

- **`app.log`** - General application logs
- **`api.log`** - API request/response logs
- **`llm.log`** - LLM service interactions (OpenRouter)
- **`generation.log`** - CV generation pipeline logs

Each log file has automatic rotation:
- **Max Size**: 10MB per file
- **Backup Count**: 5 previous files retained
- **Total**: Up to 50MB of historical logs

### Log Levels
- **DEBUG**: Detailed diagnostic information (file only)
- **INFO**: General informational messages (console + file)
- **WARNING**: Warning messages for recoverable errors
- **ERROR**: Error messages for issues

### Console Output Example
```
2026-02-17 14:30:45 - api - INFO - 🚀 Application startup event triggered
2026-02-17 14:30:45 - api - INFO - ✓ Base skills loaded successfully
2026-02-17 14:30:50 - generation - INFO - ============================================================
2026-02-17 14:30:50 - generation - INFO - 🚀 CV Generation Request Started
2026-02-17 14:30:50 - generation - INFO - ============================================================
2026-02-17 14:30:50 - generation - INFO - [1/6] Parsing job description with LLM...
2026-02-17 14:30:51 - llm - INFO - 🔧 Initializing LLMService with model: openai/gpt-4o-mini
2026-02-17 14:30:51 - llm - INFO - ✓ LLMService initialized successfully
2026-02-17 14:30:52 - llm - DEBUG - Parsing JD with LLM (model: openai/gpt-4o-mini)...
2026-02-17 14:30:53 - llm - INFO - ✓ JD parsed successfully with LLM: 5 core techs, seniority=mid
2026-02-17 14:30:53 - generation - INFO - ✓ JD Parsed: 5 core techs, 0 secondary, seniority=mid
2026-02-17 14:30:53 - generation - INFO - [2/6] Matching candidate skills with job requirements...
2026-02-17 14:30:53 - generation - INFO - ✓ Skills Matched: 3/5 (60%)
2026-02-17 14:30:53 - generation - INFO - [3/6] Running multi-factor scoring engine...
2026-02-17 14:30:54 - generation - INFO - ✓ CV Scored: 63.0/100 (YELLOW)
2026-02-17 14:30:54 - generation - INFO - [4/6] Generating optimized CV with LaTeX formatting...
2026-02-17 14:30:55 - generation - INFO - ✓ CV Rewritten: LaTeX content generated
2026-02-17 14:30:55 - generation - INFO - [5/6] Compiling LaTeX to PDF...
2026-02-17 14:30:55 - generation - INFO - ⚠ PDF compilation unavailable: pdflatex not found
2026-02-17 14:30:55 - generation - INFO - [6/6] CV optimization complete!
2026-02-17 14:30:55 - generation - INFO - ✅ CV Generation Request Completed Successfully
```

---

## LLM Configuration (OpenRouter)

### Current Setup
- **Provider**: OpenRouter (https://openrouter.ai)
- **Primary Model**: `openai/gpt-4o-mini` (configurable)
- **Fallback Strategy**: Regex-based parsing when LLM unavailable

### Environment Variables Required
```bash
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=openai/gpt-4o-mini  # Optional, defaults to this
OPENROUTER_SITE_URL=http://localhost:3000  # Your app URL
OPENROUTER_SITE_NAME=Resume Optimiser  # Your app name
```

### OpenRouter Integration Features
1. **Robust Error Handling**: If OpenAI client isn't installed or API fails, falls back to regex parsing
2. **Extra Headers**: Properly configured HTTP-Referer and X-Title headers for OpenRouter
3. **Temperature Control**: 
   - JD Parsing: `0.3` (lower = more consistent)
   - CV Rewriting: `0.7` (higher = more creative)
   - Recommendations: `0.8` (balanced)

### Fallback Mechanism
When LLM service is unavailable:
```
⚠ LLM parsing failed: No module named 'openai'. Falling back to regex.
```

The system gracefully falls back to regex-based extraction which:
- Extracts core/secondary technologies from predefined lists
- Detects seniority level from keywords
- Identifies domain/industry keywords
- Works 100% offline

---

## Semantic Similarity Model

### Current Implementation: TF-IDF

**Location**: `src/services/skill_matcher.py`

**What is TF-IDF?**
- **TF** (Term Frequency): How often a term appears in a document
- **IDF** (Inverse Document Frequency): How unique/important a term is across all documents
- **Result**: A sparse vector representing each skill

### How it Works
1. **Vectorization**: Skills are converted to TF-IDF vectors using character n-grams (2-3 chars)
2. **Similarity Scoring**: Cosine similarity between skill vectors (0 to 1 scale)
3. **Thresholds**:
   - Direct match: `>0.95` similarity (exact or near-exact)
   - Transferable match: `>0.5` similarity (related skills)

### Example
```python
# Skill embedding computation
skills = ["Python", "JavaScript", "React", "Vue"]
embeddings = TfidfVectorizer(analyzer='char', ngram_range=(2, 3))
# Each skill becomes a vector of character n-gram frequencies

# Comparison
similarity("Python", "PyTorch") ≈ 0.87  # Transferable match
similarity("Python", "Ruby") ≈ 0.45    # Not matched
similarity("Docker", "Docker") = 1.0    # Direct match
```

### Why TF-IDF?
✅ **Advantages**:
- No external ML models needed
- Fast and lightweight
- Works offline completely
- Interpretable results
- Great for skill/tech matching

❌ **Limitations**:
- Doesn't understand semantic meaning (e.g., "Docker" vs "Containerization")
- Requires good threshold tuning
- Character-level matching can miss synonyms

### Configuration
**File**: `src/core/config.py`
```python
MIN_TRANSFERABLE_SIMILARITY = 0.5   # Threshold for related skills
MIN_DIRECT_SIMILARITY = 0.95        # Threshold for exact matches
```

### Future Improvements
Potential upgrades to semantic matching:
1. **Word Embeddings** (Word2Vec, GloVe): Better semantic understanding
2. **Sentence Transformers**: Deep learning-based embeddings
3. **LLM-based Matching**: Use OpenRouter to score skill relevance
4. **Custom Knowledge Graphs**: Domain-specific skill relationships

---

## Skill Matching Flow

```
Job Description
    ↓
[LLM Parsing or Regex Fallback]
    ↓
Extracted Skills (core_stack, secondary_stack, domain)
    ↓
[TF-IDF Vectorization]
    ↓
Candidate Skills (from base_skills.json)
    ↓
[Cosine Similarity Scoring]
    ↓
Skill Match Results
├─ Direct Matches (similarity > 0.95)
├─ Transferable Matches (0.5 < similarity < 0.95)
└─ Missing Skills (similarity < 0.5)
```

---

## Troubleshooting

### Issue: "LLM parsing failed: No module named 'openai'"
**Solution**: Install OpenAI client
```bash
pip install openai
```

### Issue: No logs appearing
**Verify**:
1. Logs directory exists: `resumeoptimiser/logs/`
2. Logging is configured in `create_app()` startup
3. Check file permissions: `chmod 755 logs/`

### Issue: OpenRouter API errors
**Check**:
1. `OPENROUTER_API_KEY` is valid and has credits
2. Model `openai/gpt-4o-mini` is available on OpenRouter
3. Network connectivity to https://openrouter.ai

### Issue: Low skill matching scores
**Diagnose**:
1. Check `MIN_TRANSFERABLE_SIMILARITY` threshold (currently 0.5)
2. Review skill names for typos
3. Check base_skills.json is loaded correctly
4. Consider increasing threshold or using LLM-based matching

---

## Monitoring

### Check Application Status
```bash
curl http://localhost:8000/health
```

### View Real-time Logs
```bash
tail -f logs/generation.log          # CV generation pipeline
tail -f logs/llm.log                 # LLM interactions
tail -f logs/app.log                 # Full application logs
```

### Search Logs
```bash
# Find errors
grep "ERROR" logs/app.log

# Find LLM parsing attempts
grep "LLM parsing" logs/llm.log

# Find specific user request
grep "CV Generation Request" logs/generation.log
```
