"""FastAPI application factory."""

import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from src.core.config import API_PREFIX, API_VERSION, DEBUG, FRONTEND_URL, TEMP_UPLOAD_DIR
from src.core.logging_config import setup_logging
from src.api import base_skills, jd, matching, scoring, rewriting, pdf, generation, semantic_matching, cv_rewrite

# Setup logging
setup_logging()
logger = logging.getLogger("api")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Resume Optimiser API",
        description="Generate ATS-friendly LaTeX CVs tailored to job descriptions",
        version=API_VERSION,
        debug=DEBUG
    )

    # Ensure temp upload directory exists
    TEMP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],  # Vite default port
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom exception handler for RequestValidationError
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors without encoding issues."""
        # Create safe error details without trying to encode uploaded file objects
        errors = []
        for error in exc.errors():
            error_dict = {
                "loc": error.get("loc"),
                "msg": error.get("msg"),
                "type": error.get("type")
            }
            errors.append(error_dict)
        
        logger.warning(f"Validation error: {errors}")
        return JSONResponse(
            status_code=422,
            content={"detail": errors}
        )

    # Initialize base skills
    @app.on_event("startup")
    async def startup_event():
        """Initialize on startup."""
        logger.info("🚀 Application startup event triggered")
        base_skills.initialize_base_skills()
        logger.info("✓ Base skills loaded successfully")

    # Include routers
    app.include_router(base_skills.router, prefix=API_PREFIX)
    app.include_router(jd.router, prefix=API_PREFIX)
    app.include_router(matching.router, prefix=API_PREFIX)
    app.include_router(scoring.router, prefix=API_PREFIX)
    app.include_router(rewriting.router, prefix=API_PREFIX)
    app.include_router(pdf.router, prefix=API_PREFIX)
    app.include_router(generation.router, prefix=API_PREFIX)
    app.include_router(semantic_matching.router, prefix=API_PREFIX)
    app.include_router(cv_rewrite.router, prefix=API_PREFIX)

    # Health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "ok",
            "base_skills_loaded": base_skills.base_skills_data is not None
        }

    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API documentation."""
        return {
            "name": "Resume Optimiser API",
            "version": API_VERSION,
            "docs": "/docs",
            "openapi": "/openapi.json",
            "endpoints": {
                "base_skills": f"{API_PREFIX}/base-skills",
                "parse_jd": f"{API_PREFIX}/jd/parse",
                "match_skills": f"{API_PREFIX}/matching/skills",
                "score_cv": f"{API_PREFIX}/scoring/score",
                "rewrite_cv": f"{API_PREFIX}/rewriting/rewrite",
                "compile_pdf": f"{API_PREFIX}/pdf/compile",
                "generate_cv": f"{API_PREFIX}/generation/generate",
                "semantic_matching": f"{API_PREFIX}/semantic-matching/match",
                "optimize_cv": f"{API_PREFIX}/semantic-matching/optimize",
                "full_report": f"{API_PREFIX}/semantic-matching/full-report",
                "health": "/health"
            }
        }

    return app


app = create_app()