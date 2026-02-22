"""API endpoint for CV rewriting."""

import logging
import tempfile
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.services.cv_parser import CVParser
from src.services.cv_rewriter import get_cv_rewriter
from src.services.pdf_compiler import compile_latex_to_pdf

logger = logging.getLogger("cv_rewrite_api")

router = APIRouter(prefix="/cv-rewrite", tags=["CV Rewriting"])


class CVRewriteRequest(BaseModel):
    """Request to rewrite CV."""
    pass


class CVRewriteResponse(BaseModel):
    """Response with rewritten CV."""
    latex_content: str
    message: str


@router.post("/rewrite", response_model=CVRewriteResponse)
async def rewrite_cv(
    cv_file: UploadFile = File(..., description="Original CV PDF"),
    profile_file: UploadFile = File(..., description="Profile markdown file"),
    jd_text: str = Form("", description="Optional job description to tailor CV"),
):
    """
    Rewrite CV using LLM + profile.md for professional polish.
    
    Returns LaTeX content that can be converted to PDF.
    """
    logger.info("🧠 Processing CV rewrite request...")
    
    temp_pdf = None
    try:
        # Save CV to temporary file
        logger.info(f"Parsing CV: {cv_file.filename}")
        cv_content = await cv_file.read()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(cv_content)
            temp_pdf = tmp.name
        
        # Parse CV using CVParser (for validation, though not used in new flow)
        parser = CVParser(temp_pdf)
        parser.extract_text()  # Validate PDF can be parsed
        
        # Read profile
        logger.info(f"Reading profile: {profile_file.filename}")
        profile_content = await profile_file.read()
        profile_md = profile_content.decode('utf-8')
        logger.info(f"✓ Profile read: {len(profile_md)} characters")
        
        # Rewrite with LLM
        logger.info("🧠 Rewriting CV with LLM...")
        rewriter = get_cv_rewriter()
        latex_content = rewriter.rewrite_cv(
            profile_md=profile_md,
            job_description=jd_text if jd_text else None
        )
        logger.info(f"✓ CV rewritten: {len(latex_content)} characters of LaTeX")
        
        return CVRewriteResponse(
            latex_content=latex_content,
            message="✅ CV successfully rewritten with LLM. Download as PDF."
        )
        
    except Exception as e:
        logger.error(f"Error rewriting CV: {e}", exc_info=True)
        raise
    finally:
        # Clean up temp file
        if temp_pdf and Path(temp_pdf).exists():
            try:
                Path(temp_pdf).unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_pdf}: {e}")


@router.post("/rewrite-to-pdf")
async def rewrite_to_pdf(
    cv_file: UploadFile = File(..., description="Original CV PDF"),
    profile_file: UploadFile = File(..., description="Profile markdown file"),
    jd_text: str = Form("", description="Optional job description to tailor CV"),
):
    """
    Rewrite CV and generate PDF directly.
    
    Returns PDF file of rewritten resume.
    """
    logger.info("🧠 Processing CV rewrite + PDF generation...")
    
    temp_pdf = None
    try:
        # Save CV to temporary file
        cv_content = await cv_file.read()
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(cv_content)
            temp_pdf = tmp.name
        
        # Parse CV using CVParser (for validation)
        parser = CVParser(temp_pdf)
        parser.extract_text()  # Validate PDF can be parsed
        
        # Read profile
        profile_content = await profile_file.read()
        profile_md = profile_content.decode('utf-8')
        
        # Rewrite with LLM
        logger.info("🧠 Rewriting CV with LLM...")
        rewriter = get_cv_rewriter()
        latex_content = rewriter.rewrite_cv(
            profile_md=profile_md,
            job_description=jd_text if jd_text else None
        )
        logger.info("✓ CV rewritten with LLM")
        
        # Convert to PDF
        logger.info("📄 Converting LaTeX to PDF...")
        success, pdf_path, error_msg = compile_latex_to_pdf(latex_content, "resume_rewritten")
        
        if not success:
            logger.error(f"Failed to compile LaTeX: {error_msg}")
            raise RuntimeError(f"LaTeX compilation failed: {error_msg}")
        
        logger.info(f"✓ PDF generated: {pdf_path}")
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename="resume_rewritten.pdf"
        )
        
    except Exception as e:
        logger.error(f"Error in CV rewrite + PDF: {e}", exc_info=True)
        raise
    finally:
        # Clean up temp file
        if temp_pdf and Path(temp_pdf).exists():
            try:
                Path(temp_pdf).unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_pdf}: {e}")
