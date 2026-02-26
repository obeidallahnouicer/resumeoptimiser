"""POST /v1/optimize – main API endpoint.

Receives raw CV + job text, runs the full pipeline, returns the report.
No business logic here – all delegated to OptimizationService.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_optimization_service
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.schemas.pipeline import OptimizeRequest, OptimizeResponse
from app.services.optimization_service import OptimizationService

router = APIRouter(prefix="/optimize", tags=["optimize"])
logger = get_logger(__name__)


@router.post(
    "",
    response_model=OptimizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Optimise a CV against a job description",
    description=(
        "Accepts raw CV text and raw job description text. "
        "Runs the full AI pipeline and returns a structured comparison report."
    ),
)
def optimize(
    body: OptimizeRequest,
    service: OptimizationService = Depends(get_optimization_service),
) -> OptimizeResponse:
    """Run the CV optimisation pipeline and return the full report."""
    logger.info("api.optimize.request", cv_len=len(body.cv_text), job_len=len(body.job_text))

    try:
        report = service.run(cv_text=body.cv_text, job_text=body.job_text)
    except AppError as exc:
        logger.error("api.optimize.failed", code=exc.code, message=exc.message)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": exc.code, "message": exc.message},
        ) from exc

    return OptimizeResponse(report=report)
