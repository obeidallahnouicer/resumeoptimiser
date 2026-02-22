"""API routes for CV rewriting - DEPRECATED, use cv_rewrite.py instead."""

from fastapi import APIRouter

router = APIRouter(prefix="/rewriting", tags=["cv-rewriting"])

# Legacy endpoints disabled - use /api/v1/cv-rewrite instead
