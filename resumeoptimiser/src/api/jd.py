"""API routes for job description parsing."""

from fastapi import APIRouter, HTTPException

from src.models.schemas import ParseJobDescriptionRequest, ParsedJobDescription
from src.services.jd_parser import parse_jd_with_llm, validate_parsed_jd

router = APIRouter(prefix="/jd", tags=["job-description"])


@router.post("/parse", response_model=ParsedJobDescription)
async def parse_job_description(request: ParseJobDescriptionRequest):
    """
    Parse raw job description text into structured JSON.
    Uses LLM with regex fallback.
    """
    if not request.jd_text or len(request.jd_text.strip()) == 0:
        raise HTTPException(status_code=400, detail="Job description text is required")

    try:
        parsed_jd = parse_jd_with_llm(request.jd_text)

        if not validate_parsed_jd(parsed_jd):
            raise HTTPException(
                status_code=400,
                detail="Could not extract structured data from job description"
            )

        return parsed_jd

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing JD: {str(e)}")