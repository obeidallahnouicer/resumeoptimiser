"""Granular stage-by-stage API routes for the CV optimisation pipeline.

Each endpoint corresponds to one stage in the frontend UI:
  POST /v1/pipeline/extract      – extract text from uploaded file
  POST /v1/pipeline/parse-cv     – CVParserAgent
  POST /v1/pipeline/normalize-job – JobNormalizerAgent
  POST /v1/pipeline/match        – SemanticMatcherAgent
  POST /v1/pipeline/explain      – ScoreExplainerAgent
  POST /v1/pipeline/rewrite      – CVRewriteAgent
  POST /v1/pipeline/compare      – RescoreAgent + ReportGeneratorAgent

No business logic here – each handler delegates to one service method.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.deps import get_optimization_service
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.schemas.cv import CVParserInput, StructuredCVSchema
from app.schemas.job import JobNormalizerInput, StructuredJobSchema
from app.schemas.pipeline import ComparisonReportSchema, ImprovedScoreSchema
from app.schemas.report import (
    CVRewriteInput,
    ExplanationReportSchema,
    OptimizedCVSchema,
    ScoreExplainerInput,
)
from app.schemas.scoring import SemanticMatcherInput, SimilarityScoreSchema
from app.services.optimization_service import OptimizationService

router = APIRouter(prefix="/pipeline", tags=["pipeline"])
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _handle_app_error(exc: AppError) -> None:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"code": exc.code, "message": exc.message},
    )


# ---------------------------------------------------------------------------
# Stage 1 – File extraction
# ---------------------------------------------------------------------------


class ExtractResponse(BaseModel):
    cv_text: str
    filename: str
    char_count: int


@router.post("/extract", response_model=ExtractResponse)
async def extract_text(
    cv_file: UploadFile = File(..., description="CV file (PDF or DOCX)"),
    job_text: str = Form(..., description="Raw job description text"),
) -> ExtractResponse:
    """Extract raw text from an uploaded CV file."""
    filename = cv_file.filename or "unknown"
    content_type = cv_file.content_type or ""
    raw_bytes = await cv_file.read()

    try:
        cv_text = _extract_from_bytes(raw_bytes, content_type, filename)
    except Exception as exc:
        logger.error("extract.failed", filename=filename, error=str(exc))
        raise HTTPException(status_code=422, detail=f"Could not extract text: {exc}") from exc

    return ExtractResponse(
        cv_text=cv_text,
        filename=filename,
        char_count=len(cv_text),
    )


def _extract_from_bytes(raw: bytes, content_type: str, filename: str) -> str:
    """Dispatch to the correct parser based on file type."""
    if "pdf" in content_type or filename.lower().endswith(".pdf"):
        return _extract_pdf(raw)
    if "word" in content_type or filename.lower().endswith(".docx"):
        return _extract_docx(raw)
    # Fallback: treat as plain text
    return raw.decode("utf-8", errors="replace")


def _extract_pdf(raw: bytes) -> str:
    import io
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(raw))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx(raw: bytes) -> str:
    import io
    from docx import Document
    doc = Document(io.BytesIO(raw))
    return "\n".join(p.text for p in doc.paragraphs)


# ---------------------------------------------------------------------------
# Stage 2 – Parse CV
# ---------------------------------------------------------------------------


@router.post("/parse-cv", response_model=StructuredCVSchema)
def parse_cv(
    body: CVParserInput,
    service: OptimizationService = Depends(get_optimization_service),
) -> StructuredCVSchema:
    """Run CVParserAgent on raw CV text."""
    try:
        return service._parse_cv(body.raw_text)  # noqa: SLF001
    except AppError as exc:
        _handle_app_error(exc)


# ---------------------------------------------------------------------------
# Stage 3 – Normalize job
# ---------------------------------------------------------------------------


@router.post("/normalize-job", response_model=StructuredJobSchema)
def normalize_job(
    body: JobNormalizerInput,
    service: OptimizationService = Depends(get_optimization_service),
) -> StructuredJobSchema:
    """Run JobNormalizerAgent on raw job description text."""
    try:
        return service._parse_job(body.raw_text)  # noqa: SLF001
    except AppError as exc:
        _handle_app_error(exc)


# ---------------------------------------------------------------------------
# Stage 4 – Match (embeddings + LLM analysis)
# ---------------------------------------------------------------------------


@router.post("/match", response_model=SimilarityScoreSchema)
def match(
    body: SemanticMatcherInput,
    service: OptimizationService = Depends(get_optimization_service),
) -> SimilarityScoreSchema:
    """Run SemanticMatcherAgent + LLMMatchAnalyzerAgent. Returns blended score."""
    try:
        return service._score(body.cv, body.job)  # noqa: SLF001
    except AppError as exc:
        _handle_app_error(exc)


# ---------------------------------------------------------------------------
# Stage 5 – Explain mismatches
# ---------------------------------------------------------------------------


@router.post("/explain", response_model=ExplanationReportSchema)
def explain(
    body: ScoreExplainerInput,
    service: OptimizationService = Depends(get_optimization_service),
) -> ExplanationReportSchema:
    """Run ScoreExplainerAgent. LLM-powered gap analysis."""
    try:
        return service._explain(body.cv, body.job, body.score)  # noqa: SLF001
    except AppError as exc:
        _handle_app_error(exc)


# ---------------------------------------------------------------------------
# Stage 6 – Rewrite CV
# ---------------------------------------------------------------------------


@router.post("/rewrite", response_model=OptimizedCVSchema)
def rewrite(
    body: CVRewriteInput,
    service: OptimizationService = Depends(get_optimization_service),
) -> OptimizedCVSchema:
    """Run CVRewriteAgent. LLM rewrites sections guided by the explanation."""
    try:
        return service._rewrite(body.cv, body.job, body.explanation)  # noqa: SLF001
    except AppError as exc:
        _handle_app_error(exc)


# ---------------------------------------------------------------------------
# Stage 7 – Compare (rescore + report)
# ---------------------------------------------------------------------------


class CompareRequest(BaseModel):
    original_cv: StructuredCVSchema
    optimized_cv: StructuredCVSchema
    job: StructuredJobSchema
    original_score: SimilarityScoreSchema
    explanation: ExplanationReportSchema
    optimized_cv_schema: OptimizedCVSchema


@router.post("/compare", response_model=ComparisonReportSchema)
def compare(
    body: CompareRequest,
    service: OptimizationService = Depends(get_optimization_service),
) -> ComparisonReportSchema:
    """Run RescoreAgent + ReportGeneratorAgent. Returns full comparison."""
    try:
        improved_score = service._rescore(  # noqa: SLF001
            body.original_cv,
            body.optimized_cv,
            body.job,
            body.original_score,
        )
        return service._generate_report(  # noqa: SLF001
            improved_score, body.explanation, body.optimized_cv_schema
        )
    except AppError as exc:
        _handle_app_error(exc)
