"""API routes for skill matching."""

from fastapi import APIRouter, HTTPException

from src.models.schemas import MatchSkillsRequest, SkillMatchResult
from src.services.skill_matcher import match_skills, load_base_skills

router = APIRouter(prefix="/matching", tags=["skill-matching"])


@router.post("/skills", response_model=SkillMatchResult)
async def match_skills_endpoint(request: MatchSkillsRequest):
    """
    Match base skills to JD requirements with semantic similarity.
    Returns direct matches, transferable matches, and missing skills.
    """
    try:
        base_skills = load_base_skills()
        result = match_skills(base_skills, request.jd_json)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error matching skills: {str(e)}")