#!/bin/bash
# Quick logging reference for Resume Optimiser

echo "📋 Resume Optimiser Logging Guide"
echo "=================================="
echo ""

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. VIEW REAL-TIME GENERATION LOGS${NC}"
echo "   tail -f resumeoptimiser/logs/generation.log"
echo ""

echo -e "${BLUE}2. VIEW LLM INTERACTIONS${NC}"
echo "   tail -f resumeoptimiser/logs/llm.log"
echo ""

echo -e "${BLUE}3. VIEW API REQUESTS${NC}"
echo "   tail -f resumeoptimiser/logs/api.log"
echo ""

echo -e "${BLUE}4. VIEW ALL APPLICATION LOGS${NC}"
echo "   tail -f resumeoptimiser/logs/app.log"
echo ""

echo -e "${BLUE}5. SEARCH FOR ERRORS${NC}"
echo "   grep ERROR resumeoptimiser/logs/*.log"
echo ""

echo -e "${BLUE}6. CHECK LOG FILE SIZES${NC}"
echo "   ls -lh resumeoptimiser/logs/"
echo ""

echo -e "${BLUE}7. FOLLOW CV GENERATION SPECIFIC REQUEST${NC}"
echo "   grep 'CV Generation Request' resumeoptimiser/logs/generation.log"
echo ""

echo -e "${BLUE}8. CHECK LLM FALLBACK USAGE${NC}"
echo "   grep 'Falling back to regex' resumeoptimiser/logs/llm.log"
echo ""

echo "📊 Expected Log Output Pattern:"
echo "=================================="
cat << 'EOF'

2026-02-17 14:30:50 - generation - INFO - ============================================================
2026-02-17 14:30:50 - generation - INFO - 🚀 CV Generation Request Started
2026-02-17 14:30:50 - generation - INFO - ============================================================
2026-02-17 14:30:50 - generation - INFO - [1/6] Parsing job description with LLM...
2026-02-17 14:30:51 - llm - INFO - 🔧 Initializing LLMService with model: openai/gpt-4o-mini
2026-02-17 14:30:51 - llm - INFO - ✓ LLMService initialized successfully
2026-02-17 14:30:51 - llm - DEBUG - Parsing JD with LLM (model: openai/gpt-4o-mini)...
2026-02-17 14:30:52 - llm - DEBUG - Sending request to OpenRouter API (openai/gpt-4o-mini)...
2026-02-17 14:30:53 - llm - DEBUG - LLM response received: {"core_stack": ["Docker", "FastAPI...
2026-02-17 14:30:53 - llm - INFO - ✓ JD parsed successfully with LLM: 5 core techs, seniority=mid
2026-02-17 14:30:53 - generation - INFO - ✓ JD Parsed: 5 core techs, 0 secondary, seniority=mid
2026-02-17 14:30:53 - generation - INFO - [2/6] Matching candidate skills with job requirements...
2026-02-17 14:30:53 - generation - INFO - ✓ Skills Matched: 3/5 (60%)
2026-02-17 14:30:54 - generation - INFO - [3/6] Running multi-factor scoring engine...
2026-02-17 14:30:54 - generation - INFO - ✓ CV Scored: 63.0/100 (YELLOW) - Recommendation: Moderate fit.
2026-02-17 14:30:54 - generation - INFO - [4/6] Generating optimized CV with LaTeX formatting...
2026-02-17 14:30:54 - llm - DEBUG - Rewriting CV experience section with LLM...
2026-02-17 14:30:55 - llm - INFO - ✓ CV experience section rewritten successfully
2026-02-17 14:30:55 - generation - INFO - ✓ CV Rewritten: LaTeX content generated
2026-02-17 14:30:55 - generation - INFO - [5/6] Compiling LaTeX to PDF...
2026-02-17 14:30:55 - generation - WARNING - ⚠ PDF compilation unavailable: pdflatex not found. Install TeX Live to compile LaTeX.
2026-02-17 14:30:55 - generation - INFO - [6/6] CV optimization complete!
2026-02-17 14:30:55 - generation - INFO - ✅ CV Generation Request Completed Successfully
2026-02-17 14:30:55 - generation - INFO - ============================================================
2026-02-17 14:30:55 - generation - DEBUG - Cleaned up temp file: /path/to/temp/resume.pdf

EOF

echo ""
echo -e "${YELLOW}⚠️  FALLBACK LOG (When OpenAI library missing):${NC}"
cat << 'EOF'

2026-02-17 14:31:00 - llm - WARNING - ⚠ OpenAI client not available: No module named 'openai'. LLM parsing will not be available.
2026-02-17 14:31:05 - generation - INFO - [1/6] Parsing job description with LLM...
2026-02-17 14:31:05 - llm - ERROR - LLM client not available. Cannot parse JD with LLM.
2026-02-17 14:31:05 - generation - WARNING - ⚠ LLM parsing failed: RuntimeError: LLM service not available. Falling back to regex.
2026-02-17 14:31:05 - generation - INFO - ✓ JD Parsed (REGEX): 5 core techs, 0 secondary, seniority=mid

EOF

echo ""
echo -e "${GREEN}✅ SOLUTION: Install OpenAI${NC}"
echo "   pip install openai"
echo ""

echo "📌 Log Files Location:"
echo "   resumeoptimiser/logs/generation.log  (CV pipeline)"
echo "   resumeoptimiser/logs/llm.log         (OpenRouter interactions)"
echo "   resumeoptimiser/logs/api.log         (HTTP requests)"
echo "   resumeoptimiser/logs/app.log         (All logs)"
echo ""

echo "🔍 Semantic Matching Model: TF-IDF with character n-grams"
echo "   Location: src/services/skill_matcher.py"
echo "   Direct match threshold: > 0.95 similarity"
echo "   Transferable threshold: > 0.50 similarity"
