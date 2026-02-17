"""API routes for CV rewriting."""

from fastapi import APIRouter, HTTPException

from src.models.schemas import RewriteCVRequest, RewrittenCV
from src.services.cv_rewriter import rewrite_cv
from src.services.skill_matcher import load_base_skills

router = APIRouter(prefix="/rewriting", tags=["cv-rewriting"])


@router.post("/rewrite", response_model=RewrittenCV)
async def rewrite_cv_endpoint(request: RewriteCVRequest):
    """
    Rewrite base CV into LaTeX using JD + match JSON.
    Truth-constrained: only uses base skills, no hallucination.
    """
    try:
        base_skills = load_base_skills()
        rewritten = rewrite_cv(base_skills, request.skill_match_json, request.cv_score)
        return rewritten

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rewriting CV: {str(e)}")