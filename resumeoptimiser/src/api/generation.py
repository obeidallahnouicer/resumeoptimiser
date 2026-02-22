"""API routes for end-to-end CV generation."""

import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from pathlib import Path

from src.models.schemas import EndToEndResponse
from src.services.jd_parser import parse_jd_with_llm, validate_parsed_jd
from src.services.skill_matcher import match_skills, load_base_skills
from src.services.scoring_engine import score_cv
from src.services.pdf_compiler import compile_latex_to_pdf
from src.core.config import MAX_UPLOAD_SIZE_BYTES, TEMP_UPLOAD_DIR

logger = logging.getLogger("generation")
router = APIRouter(prefix="/generation", tags=["generation"])


async def extract_cv_text_from_pdf(file_path: str) -> Optional[str]:
    """
    Extract text from PDF file.
    Placeholder - implement with pdfplumber or PyPDF2.
    """
    # TODO: Implement actual PDF text extraction with pdfplumber
    return None


@router.post("/generate", response_model=EndToEndResponse)
async def generate_cv_endpoint(
    jd_text: str = Form(...),
    cv_file: Optional[UploadFile] = File(None)
):
    """
    Complete end-to-end CV optimization flow.
    
    Args:
        jd_text: Job description text (required)
        cv_file: Optional PDF resume file
    """
    base_skills = load_base_skills()
    logs: List[str] = []
    temp_file_path: Optional[str] = None
    
    logger.info("=" * 60)
    logger.info("🚀 CV Generation Request Started")
    logger.info("=" * 60)

    try:
        # Step 0: Handle CV file upload
        if cv_file:
            try:
                temp_file_path = str(TEMP_UPLOAD_DIR / cv_file.filename)
                logger.info(f"📥 Uploading CV file: {cv_file.filename}")
                
                # Read file and validate size
                contents = await cv_file.read()
                file_size = len(contents)
                
                if file_size > MAX_UPLOAD_SIZE_BYTES:
                    raise ValueError(f"File size exceeds {MAX_UPLOAD_SIZE_BYTES / 1024 / 1024:.0f}MB limit")
                
                # Write to temp file
                Path(temp_file_path).write_bytes(contents)
                logs.append(f"✓ CV PDF uploaded: {cv_file.filename} ({file_size / 1024:.1f}KB)")
                logger.info(f"✓ Saved CV to: {temp_file_path} ({file_size / 1024:.1f}KB)")
                
                # Extract text from PDF (placeholder)
                cv_text_extracted = await extract_cv_text_from_pdf(temp_file_path)
                if cv_text_extracted:
                    logs.append(f"✓ Extracted {len(cv_text_extracted)} characters from CV")
                    logger.info(f"✓ Extracted {len(cv_text_extracted)} characters from CV")
                else:
                    logs.append("⚠ PDF extraction not fully implemented, using base skills only")
                    logger.info("⚠ PDF extraction not fully implemented, using base skills only")
                    
            except ValueError as e:
                logger.error(f"❌ File validation error: {str(e)}")
                raise HTTPException(status_code=413, detail=str(e))
            except Exception as e:
                logs.append(f"⚠ File processing error: {str(e)}")
                logger.warning(f"⚠ File processing error: {str(e)}")
        
        # Step 1: Parse JD
        logger.info("[1/6] Parsing job description with LLM...")
        logs.append("[PARSE] Analyzing job description...")
        parsed_jd = parse_jd_with_llm(jd_text)
        if not validate_parsed_jd(parsed_jd):
            raise ValueError("Invalid job description - could not extract requirements")
        logs.append(f"[PARSE] ✓ Found {len(parsed_jd.core_stack)} core technologies, seniority: {parsed_jd.seniority}")
        logger.info(f"✓ JD Parsed: {len(parsed_jd.core_stack)} core techs, {len(parsed_jd.secondary_stack)} secondary, seniority={parsed_jd.seniority}")

        # Step 2: Match skills
        logger.info("[2/6] Matching candidate skills with job requirements...")
        logs.append("[MATCH] Matching candidate skills with job requirements...")
        skill_match = match_skills(base_skills, parsed_jd)
        if skill_match.total_jd_requirements > 0:
            match_pct = (skill_match.total_matched / skill_match.total_jd_requirements) * 100
            logs.append(f"[MATCH] ✓ {skill_match.total_matched}/{skill_match.total_jd_requirements} skills matched ({match_pct:.0f}%)")
            logger.info(f"✓ Skills Matched: {skill_match.total_matched}/{skill_match.total_jd_requirements} ({match_pct:.0f}%)")
        else:
            logs.append("[MATCH] ✓ Matching complete")
            logger.info("✓ Skills Matching complete")

        # Step 3: Score CV
        logger.info("[3/6] Running multi-factor scoring engine...")
        logs.append("[SCORE] Running multi-factor scoring engine...")
        cv_score = score_cv(skill_match, parsed_jd)
        logs.append(f"[SCORE] ✓ Total Score: {cv_score.total_score:.1f}/100 ({cv_score.category.upper()})")
        logs.append(f"[SCORE] Stack Alignment: {cv_score.breakdown.stack_alignment}/40")
        logs.append(f"[SCORE] Capability Match: {cv_score.breakdown.capability_match}/20")
        logs.append(f"[SCORE] Seniority Fit: {cv_score.breakdown.seniority_fit}/15")
        logs.append(f"[SCORE] Domain Relevance: {cv_score.breakdown.domain_relevance}/10")
        logs.append(f"[SCORE] Sponsorship Feasibility: {cv_score.breakdown.sponsorship_feasibility}/15")
        logger.info(f"✓ CV Scored: {cv_score.total_score:.1f}/100 ({cv_score.category.upper()}) - Recommendation: {cv_score.recommendation}")

        # Step 4: Rewrite CV (DEPRECATED - use /api/v1/cv-rewrite instead)
        logger.info("[4/6] CV rewriting moved to /api/v1/cv-rewrite endpoint...")
        logs.append("[GEN] Use /api/v1/cv-rewrite endpoint for CV generation with profile.md")
        logger.info("✓ For CV rewriting, use the new cv_rewrite API endpoint")

        # Step 5: Skip PDF compilation (use cv_rewrite endpoint instead)
        logger.info("[5/6] PDF compilation - use cv_rewrite endpoint...")
        logs.append("[COMPILE] PDF compilation available via cv_rewrite endpoint")
        pdf_path = None

        logger.info("[6/6] CV optimization analysis complete!")
        logs.append("[SUCCESS] ✓ CV analysis complete! Use /api/v1/cv-rewrite for PDF generation")
        logger.info("=" * 60)
        logger.info("✅ CV Analysis Request Completed Successfully")
        logger.info("=" * 60)

        return EndToEndResponse(
            parsed_jd=parsed_jd,
            skill_match=skill_match,
            cv_score=cv_score,
            rewritten_cv=None,
            pdf_path=pdf_path,
            logs=logs
        )

    except HTTPException:
        raise
    except Exception as e:
        logs.append(f"[ERROR] ✗ {str(e)}")
        logger.error(f"❌ CV Generation Error: {type(e).__name__}: {str(e)}")
        logger.info("=" * 60)
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temp file
        if temp_file_path and Path(temp_file_path).exists():
            try:
                Path(temp_file_path).unlink()
                logger.debug(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")