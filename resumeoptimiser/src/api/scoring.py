"""API routes for CV scoring."""

from fastapi import APIRouter, HTTPException

from src.models.schemas import ScoreCVRequest, CVScore
from src.services.scoring_engine import score_cv

router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.post("/score", response_model=CVScore)
async def score_cv_endpoint(request: ScoreCVRequest):
    """
    Calculate ATS-friendly score and capability alignment.
    Returns numeric score, category, and breakdown.
    """
    try:
        cv_score = score_cv(request.skill_match_json, request.jd_json)
        return cv_score

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scoring CV: {str(e)}")