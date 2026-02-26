"""FastAPI application factory and entry point.

Responsibilities:
- Create the FastAPI app instance
- Register routers
- Configure logging on startup
- Register exception handlers
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.routes import optimize as optimize_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging, get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Configure logging and perform startup/shutdown tasks."""
    settings = get_settings()
    configure_logging(level=settings.log_level, fmt=settings.log_format)
    logger.info("app.startup", env=settings.app_env)
    yield
    logger.info("app.shutdown")


def create_app() -> FastAPI:
    """Construct and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AI CV Optimisation System",
        version="0.1.0",
        description="Modular AI pipeline for CV optimisation against job descriptions.",
        debug=settings.app_debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_routers(app)
    _register_exception_handlers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """Mount all API routers."""
    from app.api.v1.routes import pipeline as pipeline_router
    app.include_router(optimize_router.router, prefix="/v1")
    app.include_router(pipeline_router.router, prefix="/v1")


def _register_exception_handlers(app: FastAPI) -> None:
    """Map domain exceptions to HTTP responses."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("unhandled_app_error", code=exc.code, message=exc.message)
        return JSONResponse(
            status_code=422,
            content={"code": exc.code, "message": exc.message},
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={"code": "INTERNAL_ERROR", "message": "An unexpected error occurred."},
        )


app = create_app()
