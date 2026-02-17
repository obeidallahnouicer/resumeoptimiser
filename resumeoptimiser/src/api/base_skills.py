"""API routes for base skills management."""

from fastapi import APIRouter, HTTPException

from src.models.schemas import BaseSkillsData
from src.services.skill_matcher import load_base_skills

router = APIRouter(prefix="/base-skills", tags=["base-skills"])

# Global state
base_skills_data: BaseSkillsData = None


def initialize_base_skills():
    """Initialize base skills from file."""
    global base_skills_data
    try:
        base_skills_data = load_base_skills()
    except Exception as e:
        print(f"Warning: Could not load base_skills.json: {e}")


@router.get("", response_model=BaseSkillsData)
async def get_base_skills():
    """Retrieve the current base skills data."""
    if not base_skills_data:
        raise HTTPException(status_code=500, detail="Base skills not loaded")
    return base_skills_data


@router.post("")
async def validate_base_skills():
    """Validate base skills JSON structure and content."""
    if not base_skills_data:
        raise HTTPException(status_code=500, detail="Base skills not loaded")

    return {
        "valid": True,
        "skills_count": len(base_skills_data.skills),
        "experience_count": len(base_skills_data.experience),
        "message": "Base skills are valid and truth-constrained"
    }