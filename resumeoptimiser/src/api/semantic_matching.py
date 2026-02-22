"""
API routes for semantic CV matching.

Provides endpoints for:
- Semantic CV to JD matching
- Gap analysis
- CV optimization with re-scoring
"""

import logging
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from datetime import datetime

from src.models.schemas import (
    SemanticMatchingRequest,
    CVOptimizationRequest,
    SemanticMatchResult,
    CVOptimizationResult,
    SemanticCVReport,
    GapAnalysisItem
)
from src.services.embedder import get_embedder
from src.services.cv_parser import CVParser
from src.services.semantic_matcher import get_matcher
from src.services.gap_analyzer import GapAnalyzer
from src.services.jd_preprocessor import get_jd_preprocessor
from src.services.cv_optimizer import CVOptimizer
from src.core.config import TEMP_UPLOAD_DIR

router = APIRouter(prefix="/semantic-matching", tags=["semantic-matching"])
logger = logging.getLogger("semantic_matching_api")


@router.post("/match", response_model=SemanticMatchResult)
async def match_cv_to_job(
    cv_file: UploadFile = File(...),
    job_description_text: str = Form(...),
    profile_file: UploadFile = File(None)
):
    """
    Match CV to job description semantically.
    
    Args:
        cv_file: CV PDF file upload
        job_description_text: Job description text
        profile_file: Optional profile markdown file
        
    Returns:
        Semantic matching result with scores and gaps
    """
    cv_path = None
    profile_path = None
    
    try:
        logger.info("Processing semantic matching request")
        
        # Validate file types early
        if not cv_file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="CV file must be a PDF")
        
        if profile_file and not profile_file.filename.lower().endswith(('.md', '.txt')):
            raise HTTPException(status_code=400, detail="Profile file must be markdown or text")
        
        # Save uploaded CV file to temp location
        cv_path = TEMP_UPLOAD_DIR / cv_file.filename
        with open(cv_path, "wb") as f:
            content = await cv_file.read()
            f.write(content)
        logger.info(f"✓ CV uploaded: {cv_file.filename}")
        
        # Save profile file if provided
        if profile_file:
            profile_path = TEMP_UPLOAD_DIR / profile_file.filename
            with open(profile_path, "wb") as f:
                content = await profile_file.read()
                f.write(content)
            logger.info(f"✓ Profile uploaded: {profile_file.filename}")
        
        # Parse CV
        cv_parser = CVParser(str(cv_path))
        cv_data = cv_parser.get_structured_cv()
        logger.info(f"✓ CV parsed: {len(cv_data['sections'])} sections")
        
        # Parse JD into sections
        jd_sections = _parse_jd_sections(job_description_text)
        logger.info(f"✓ JD parsed: {len(jd_sections)} sections")
        
        # Load profile if provided
        profile_data = None
        if profile_path:
            profile_data = _load_profile(str(profile_path))
            logger.info("✓ Profile loaded")
        
        # Perform semantic matching
        matcher = get_matcher()
        match_result = matcher.match_cv_to_jd(
            cv_data.get("sections", {}),
            jd_sections
        )
        
        # Perform skill matching
        cv_skills = cv_data.get("bullets", {}).get("skills", [])
        jd_skills = _extract_skills_from_jd(jd_sections)
        skill_match = matcher.match_skill_list(cv_skills, jd_skills)
        
        # Analyze gaps
        gap_analyzer = GapAnalyzer()
        gaps = gap_analyzer.analyze_gaps(
            cv_data,
            {"sections": jd_sections},
            profile_data
        )
        
        # Convert gaps to response format
        gap_items = [
            GapAnalysisItem(
                gap_id=gap.gap_id,
                requirement=gap.requirement,
                gap_type=gap.gap_type,
                severity=gap.severity,
                similarity=gap.similarity,
                closest_match=gap.closest_match,
                suggested_improvement=gap.suggested_improvement,
                source=gap.source
            )
            for gap in gaps
        ]
        
        # Categorize and prioritize gaps
        categorized_gaps = gap_analyzer.categorize_gaps(gaps)
        critical_gap_count = len(categorized_gaps.get("skill_gap", []))
        
        # Generate recommendations
        recommendations = _generate_recommendations(
            match_result,
            skill_match,
            gaps,
            critical_gap_count
        )
        
        # Classify confidence
        overall_score = match_result["overall_score"]
        if overall_score >= 0.75:
            confidence = "strong"
        elif overall_score >= 0.60:
            confidence = "viable"
        elif overall_score >= 0.45:
            confidence = "risky"
        else:
            confidence = "low"
        
        result = SemanticMatchResult(
            overall_score=overall_score,
            confidence=confidence,
            section_scores=match_result.get("section_scores", {}),
            skill_match_ratio=skill_match.get("match_ratio", 0.0),
            gaps=gap_items,
            critical_gaps=critical_gap_count,
            recommendations=recommendations
        )
        
        logger.info(f"✓ Semantic matching complete: {overall_score:.1%} score")
        return result
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error in semantic matching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        # Clean up temp files
        if cv_path and cv_path.exists():
            try:
                cv_path.unlink()
            except Exception:
                pass
        if profile_path and profile_path.exists():
            try:
                profile_path.unlink()
            except Exception:
                pass
        
        # Perform semantic matching
        matcher = get_matcher()
        match_result = matcher.match_cv_to_jd(
            cv_data.get("sections", {}),
            jd_sections
        )
        
        # Perform skill matching
        cv_skills = cv_data.get("bullets", {}).get("skills", [])
        jd_skills = _extract_skills_from_jd(jd_sections)
        skill_match = matcher.match_skill_list(cv_skills, jd_skills)
        
        # Analyze gaps
        gap_analyzer = GapAnalyzer()
        gaps = gap_analyzer.analyze_gaps(
            cv_data,
            {"sections": jd_sections},
            profile_data
        )
        
        # Convert gaps to response format
        gap_items = [
            GapAnalysisItem(
                gap_id=gap.gap_id,
                requirement=gap.requirement,
                gap_type=gap.gap_type,
                severity=gap.severity,
                similarity=gap.similarity,
                closest_match=gap.closest_match,
                suggested_improvement=gap.suggested_improvement,
                source=gap.source
            )
            for gap in gaps
        ]
        
        # Categorize and prioritize gaps
        categorized_gaps = gap_analyzer.categorize_gaps(gaps)
        critical_gap_count = len(categorized_gaps.get("skill_gap", []))
        
        # Generate recommendations
        recommendations = _generate_recommendations(
            match_result,
            skill_match,
            gaps,
            critical_gap_count
        )
        
        # Classify confidence
        overall_score = match_result["overall_score"]
        if overall_score >= 0.75:
            confidence = "strong"
        elif overall_score >= 0.60:
            confidence = "viable"
        elif overall_score >= 0.45:
            confidence = "risky"
        else:
            confidence = "low"
        
        result = SemanticMatchResult(
            overall_score=overall_score,
            confidence=confidence,
            section_scores=match_result.get("section_scores", {}),
            skill_match_ratio=skill_match.get("match_ratio", 0.0),
            gaps=gap_items,
            critical_gaps=critical_gap_count,
            recommendations=recommendations
        )
        
        logger.info(f"✓ Semantic matching complete: {overall_score:.1%} score")
        return result
    


@router.post("/match-smart", response_model=SemanticMatchResult)
async def match_cv_to_job_smart(
    cv_file: UploadFile = File(...),
    job_description_text: str = Form(...),
    profile_file: UploadFile = File(None)
):
    """
    Smart match: Uses LLM to preprocess job description before semantic matching.
    
    This provides much better gap analysis compared to naive fragmentation:
    - LLM extracts structured requirements from JD
    - Groups related skills and responsibilities
    - Removes duplicates and fragments
    - Analyzes complete requirements, not pieces
    
    Args:
        cv_file: CV PDF file upload
        job_description_text: Job description text
        profile_file: Optional profile markdown file
        
    Returns:
        Semantic matching result with high-quality gaps and recommendations
    """
    cv_path = None
    profile_path = None
    
    try:
        logger.info("🧠 Processing SMART semantic matching request (LLM-powered)")
        
        # Validate file types
        if not cv_file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="CV file must be a PDF")
        
        if profile_file and not profile_file.filename.lower().endswith(('.md', '.txt')):
            raise HTTPException(status_code=400, detail="Profile file must be markdown or text")
        
        # Save uploaded CV file
        cv_path = TEMP_UPLOAD_DIR / cv_file.filename
        with open(cv_path, "wb") as f:
            content = await cv_file.read()
            f.write(content)
        logger.info(f"✓ CV uploaded: {cv_file.filename}")
        
        # Save profile file if provided
        profile_data = None
        if profile_file:
            profile_path = TEMP_UPLOAD_DIR / profile_file.filename
            with open(profile_path, "wb") as f:
                content = await profile_file.read()
                f.write(content)
            logger.info(f"✓ Profile uploaded: {profile_file.filename}")
            profile_data = _load_profile(str(profile_path))
        
        # Parse CV
        cv_parser = CVParser(str(cv_path))
        cv_data = cv_parser.get_structured_cv()
        logger.info(f"✓ CV parsed: {len(cv_data['sections'])} sections")
        
        # ⭐ SMART STEP: Use LLM to preprocess job description
        logger.info("🧠 Using LLM to intelligently parse job description...")
        preprocessor = get_jd_preprocessor()
        structured_jd = preprocessor.preprocess(job_description_text)
        logger.info(
            f"✓ JD preprocessed by LLM: "
            f"{len(structured_jd.required_skills)} required skills, "
            f"{len(structured_jd.preferred_skills)} preferred skills, "
            f"{len(structured_jd.responsibilities)} responsibilities"
        )
        
        # Perform semantic matching (using parsed JD sections)
        matcher = get_matcher()
        jd_sections_dict = {
            "required_skills": "\n".join([r.text for r in structured_jd.required_skills]),
            "preferred_skills": "\n".join([r.text for r in structured_jd.preferred_skills]),
            "responsibilities": "\n".join([r.text for r in structured_jd.responsibilities]),
            "qualifications": "\n".join([r.text for r in structured_jd.qualifications])
        }
        match_result = matcher.match_cv_to_jd(
            cv_data.get("sections", {}),
            jd_sections_dict
        )
        
        # Perform skill matching
        cv_skills = cv_data.get("bullets", {}).get("skills", [])
        jd_skills = [r.text for r in structured_jd.required_skills]
        skill_match = matcher.match_skill_list(cv_skills, jd_skills)
        
        # ⭐ SMART STEP: Analyze gaps using structured JD (much better quality)
        logger.info("🧠 Analyzing gaps using structured requirements...")
        gap_analyzer = GapAnalyzer()
        gaps = gap_analyzer.analyze_gaps(
            cv_data,
            structured_jd,  # Pass structured JD instead of dict
            profile_data
        )
        logger.info(f"✓ Identified {len(gaps)} high-quality gaps")
        
        # Convert gaps to response format
        gap_items = [
            GapAnalysisItem(
                gap_id=gap.gap_id,
                requirement=gap.requirement,
                gap_type=gap.gap_type,
                severity=gap.severity,
                similarity=gap.similarity,
                closest_match=gap.closest_match,
                suggested_improvement=gap.suggested_improvement,
                source=gap.source
            )
            for gap in gaps
        ]
        
        # Calculate critical gap count
        critical_gap_count = sum(
            1 for g in gaps if g.severity == "critical"
        )
        
        # Generate smart recommendations
        recommendations = _generate_smart_recommendations(
            match_result,
            skill_match,
            gaps,
            structured_jd
        )
        
        # Classify confidence
        overall_score = match_result["overall_score"]
        if overall_score >= 0.75:
            confidence = "strong"
        elif overall_score >= 0.60:
            confidence = "viable"
        elif overall_score >= 0.45:
            confidence = "risky"
        else:
            confidence = "low"
        
        result = SemanticMatchResult(
            overall_score=overall_score,
            confidence=confidence,
            section_scores=match_result.get("section_scores", {}),
            skill_match_ratio=skill_match.get("match_ratio", 0.0),
            gaps=gap_items,
            critical_gaps=critical_gap_count,
            recommendations=recommendations
        )
        
        logger.info(f"✓ SMART semantic matching complete: {overall_score:.1%} score")
        return result
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {str(e)}")
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error in smart semantic matching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        # Clean up temp files
        if cv_path and cv_path.exists():
            try:
                cv_path.unlink()
            except Exception:
                pass
        if profile_path and profile_path.exists():
            try:
                profile_path.unlink()
            except Exception:
                pass


@router.post("/optimize", response_model=CVOptimizationResult)
async def optimize_cv(
    cv_file: UploadFile = File(...),
    job_description_text: str = Form(...),
    profile_file: UploadFile = File(None),
    apply_optimizations: str = Form("true")
):
    """
    Optimize CV based on job description.
    
    Args:
        cv_file: CV PDF file upload
        job_description_text: Job description text
        profile_file: Optional profile markdown file
        apply_optimizations: Whether to apply optimizations
        
    Returns:
        Optimization result with before/after scores
    """
    cv_path = None
    profile_path = None
    
    try:
        logger.info("🔄 Starting CV optimization")
        
        # Save uploaded CV file
        cv_path = TEMP_UPLOAD_DIR / cv_file.filename
        with open(cv_path, "wb") as f:
            content = await cv_file.read()
            f.write(content)
        logger.info(f"✓ CV uploaded: {cv_file.filename}")
        
        # Save profile file if provided
        if profile_file:
            profile_path = TEMP_UPLOAD_DIR / profile_file.filename
            with open(profile_path, "wb") as f:
                content = await profile_file.read()
                f.write(content)
            logger.info(f"✓ Profile uploaded: {profile_file.filename}")
        
        # Parse CV
        cv_parser = CVParser(str(cv_path))
        cv_data = cv_parser.get_structured_cv()
        
        # Parse JD
        jd_sections = _parse_jd_sections(job_description_text)
        
        # Load profile
        profile_data = None
        if profile_path:
            profile_data = _load_profile(str(profile_path))
        
        # First pass: analyze gaps
        matcher = get_matcher()
        match_result_before = matcher.match_cv_to_jd(
            cv_data.get("sections", {}),
            jd_sections
        )
        score_before = match_result_before["overall_score"]
        
        gap_analyzer = GapAnalyzer()
        gaps = gap_analyzer.analyze_gaps(
            cv_data,
            {"sections": jd_sections},
            profile_data
        )
        
        # Optimize CV
        optimizer = CVOptimizer()
        optimization_result = optimizer.optimize_cv(
            cv_data,
            profile_data or {},
            gaps,
            {"sections": jd_sections}
        )
        
        # Embed optimized sections for potential future use
        optimized_cv_sections = optimization_result.get("optimized_sections", {})
        
        # Second pass: re-score
        match_result_after = matcher.match_cv_to_jd(
            optimized_cv_sections,
            jd_sections
        )
        score_after = match_result_after["overall_score"]
        
        improvement_delta = score_after - score_before
        
        # Compliance check
        compliance_check = {
            "no_hallucination": _verify_no_hallucination(
                cv_data, optimized_cv_sections
            ),
            "uses_profile_data": profile_path is not None,
            "jd_aligned": improvement_delta >= -0.05  # Allow small variance
        }
        
        result = CVOptimizationResult(
            original_score=score_before,
            optimized_score=score_after,
            improvement_delta=improvement_delta,
            improvements_made=optimization_result.get("improvements", []),
            optimized_sections=optimized_cv_sections,
            warnings=optimization_result.get("warnings", []),
            compliance_check=compliance_check
        )
        
        logger.info(
            f"✓ Optimization complete: {score_before:.1%} → {score_after:.1%} "
            f"(+{improvement_delta:.1%})"
        )
        return result
    
    except Exception as e:
        logger.error(f"Error in CV optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        # Clean up temp files
        if cv_path and cv_path.exists():
            try:
                cv_path.unlink()
            except Exception:
                pass
        if profile_path and profile_path.exists():
            try:
                profile_path.unlink()
            except Exception:
                pass


@router.post("/full-report", response_model=SemanticCVReport)
async def generate_full_report(
    cv_file: UploadFile = File(...),
    job_description_text: str = Form(...),
    profile_file: UploadFile = File(None),
    apply_optimizations: str = Form("false")
):
    """
    Generate complete semantic CV matching report.
    
    Args:
        cv_file: CV PDF file upload
        job_description_text: Job description text
        profile_file: Optional profile markdown file
        apply_optimizations: Whether to apply optimizations
        
    Returns:
        Complete report with matching and optimization results
    """
    cv_path = None
    profile_path = None
    
    try:
        logger.info("🔄 Generating full semantic CV report")
        
        # Save uploaded files
        cv_path = TEMP_UPLOAD_DIR / cv_file.filename
        with open(cv_path, "wb") as f:
            content = await cv_file.read()
            f.write(content)
        
        if profile_file:
            profile_path = TEMP_UPLOAD_DIR / profile_file.filename
            with open(profile_path, "wb") as f:
                content = await profile_file.read()
                f.write(content)
        
        # Parse CV
        cv_parser = CVParser(str(cv_path))
        cv_data = cv_parser.get_structured_cv()
        
        # Parse JD
        jd_sections = _parse_jd_sections(job_description_text)
        
        # Load profile
        profile_data = None
        if profile_path:
            profile_data = _load_profile(str(profile_path))
        
        # Get matching result
        matcher = get_matcher()
        match_result_dict = matcher.match_cv_to_jd(
            cv_data.get("sections", {}),
            jd_sections
        )
        
        # Perform skill matching
        cv_skills = cv_data.get("bullets", {}).get("skills", [])
        jd_skills = _extract_skills_from_jd(jd_sections)
        skill_match = matcher.match_skill_list(cv_skills, jd_skills)
        
        # Analyze gaps
        gap_analyzer = GapAnalyzer()
        gaps = gap_analyzer.analyze_gaps(
            cv_data,
            {"sections": jd_sections},
            profile_data
        )
        
        # Convert gaps to response format
        gap_items = [
            GapAnalysisItem(
                gap_id=gap.gap_id,
                requirement=gap.requirement,
                gap_type=gap.gap_type,
                severity=gap.severity,
                similarity=gap.similarity,
                closest_match=gap.closest_match,
                suggested_improvement=gap.suggested_improvement,
                source=gap.source
            )
            for gap in gaps
        ]
        
        # Categorize gaps
        categorized_gaps = gap_analyzer.categorize_gaps(gaps)
        critical_gap_count = len(categorized_gaps.get("skill_gap", []))
        
        # Generate recommendations
        recommendations = _generate_recommendations(
            match_result_dict,
            skill_match,
            gaps,
            critical_gap_count
        )
        
        # Create matching result
        overall_score = match_result_dict["overall_score"]
        if overall_score >= 0.75:
            confidence = "strong"
        elif overall_score >= 0.60:
            confidence = "viable"
        elif overall_score >= 0.45:
            confidence = "risky"
        else:
            confidence = "low"
        
        matching_result = SemanticMatchResult(
            overall_score=overall_score,
            confidence=confidence,
            section_scores=match_result_dict.get("section_scores", {}),
            skill_match_ratio=skill_match.get("match_ratio", 0.0),
            gaps=gap_items,
            critical_gaps=critical_gap_count,
            recommendations=recommendations
        )
        
        # Get optimization result if requested
        optimization_result = None
        if apply_optimizations.lower() == "true":
            # Optimize CV
            optimizer = CVOptimizer()
            optimization_dict = optimizer.optimize_cv(
                cv_data,
                profile_data or {},
                gaps,
                {"sections": jd_sections}
            )
            
            # Re-score optimized CV
            optimized_cv_sections = optimization_dict.get("optimized_sections", {})
            match_result_after = matcher.match_cv_to_jd(
                optimized_cv_sections,
                jd_sections
            )
            score_after = match_result_after["overall_score"]
            improvement_delta = score_after - overall_score
            
            # Create optimization result
            compliance_check = {
                "no_hallucination": _verify_no_hallucination(cv_data, optimized_cv_sections),
                "uses_profile_data": profile_path is not None,
                "jd_aligned": improvement_delta >= -0.05
            }
            
            optimization_result = CVOptimizationResult(
                original_score=overall_score,
                optimized_score=score_after,
                improvement_delta=improvement_delta,
                improvements_made=optimization_dict.get("improvements", []),
                optimized_sections=optimized_cv_sections,
                warnings=optimization_dict.get("warnings", []),
                compliance_check=compliance_check
            )
        
        # Generate summary
        summary = _generate_summary(matching_result, optimization_result)
        
        report = SemanticCVReport(
            matching_result=matching_result,
            optimization_result=optimization_result,
            analysis_timestamp=datetime.now().isoformat(),
            summary=summary
        )
        
        logger.info("✓ Full report generated")
        return report
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        # Clean up temp files
        if cv_path and cv_path.exists():
            try:
                cv_path.unlink()
            except Exception:
                pass
        if profile_path and profile_path.exists():
            try:
                profile_path.unlink()
            except Exception:
                pass


def _parse_jd_sections(jd_text: str) -> dict:
    """Parse JD into sections."""
    sections = {
        "requirements": jd_text,
        "full_text": jd_text
    }
    return sections


def _extract_skills_from_jd(jd_sections: dict) -> list:
    """Extract skill keywords from JD sections."""
    import re
    skills = []
    for section_text in jd_sections.values():
        if not section_text:
            continue
        # Simple extraction: look for capitalized words
        matches = re.findall(r'\b[A-Z][a-zA-Z]+\b', section_text)
        skills.extend(matches)
    return list(set(skills))[:30]


def _load_profile(profile_path: str) -> dict:
    """Load and parse profile.md file."""
    try:
        with open(profile_path, 'r') as f:
            content = f.read()
        return {"raw_text": content}
    except Exception as e:
        logger.warning(f"Failed to load profile: {str(e)}")
        return {"raw_text": ""}


def _generate_recommendations(match_result: dict, skill_match: dict, gaps: list, critical_count: int) -> list:
    """Generate actionable recommendations."""
    recommendations = []
    
    overall_score = match_result.get("overall_score", 0.0)
    
    if overall_score >= 0.75:
        recommendations.append("✓ Strong match - Ready to apply")
    elif overall_score >= 0.60:
        recommendations.append("⚠ Good match - Address wording gaps before applying")
    elif overall_score >= 0.45:
        recommendations.append("✗ Weak match - Optimize CV or build skills")
    else:
        recommendations.append("✗ Poor match - Major skill gaps or career shift needed")
    
    if critical_count > 5:
        recommendations.append(f"🔴 Address {critical_count} critical skill gaps")
    elif critical_count > 0:
        recommendations.append(f"🟠 Address {critical_count} skill gaps")
    
    if skill_match.get("match_ratio", 0.0) < 0.5:
        recommendations.append("Consider building missing technical skills")
    
    return recommendations


def _generate_smart_recommendations(match_result: dict, skill_match: dict, gaps: list, structured_jd) -> list:
    """Generate intelligent recommendations based on LLM-structured job requirements."""
    recommendations = []
    
    overall_score = match_result.get("overall_score", 0.0)
    
    # Match quality assessment
    if overall_score >= 0.75:
        recommendations.append("✅ Excellent match - This is a strong fit for your profile")
    elif overall_score >= 0.60:
        recommendations.append("✅ Good match - You're qualified for this role with minor improvements")
    elif overall_score >= 0.45:
        recommendations.append("⚠️  Moderate match - Consider skill development or tailored CV version")
    else:
        recommendations.append("❌ Weak match - Would require significant skill development")
    
    # Analyze skill gaps by category
    critical_skills = [g for g in gaps if g.severity == "critical"]
    high_skills = [g for g in gaps if g.severity == "high"]
    
    if critical_skills:
        skill_names = ", ".join([g.requirement[:30] for g in critical_skills[:3]])
        count_str = f" and {len(critical_skills) - 3} more" if len(critical_skills) > 3 else ""
        recommendations.append(f"🔴 Critical gaps: {skill_names}{count_str}")
    
    if high_skills and not critical_skills:
        recommendations.append(f"🟠 {len(high_skills)} required skills need emphasis in CV")
    
    # Check preferred skills
    preferred_skills = structured_jd.preferred_skills
    
    if preferred_skills:
        recommendations.append(f"💡 Highlighting {len(preferred_skills)} preferred skills could strengthen application")
    
    if skill_match.get("match_ratio", 0.0) < 0.3:
        recommendations.append("🎯 Major skill gap - Upskilling recommended before applying")
    elif skill_match.get("match_ratio", 0.0) < 0.6:
        recommendations.append("📚 Some skill gaps - Consider targeted learning")
    
    # Tailor recommendation
    wording_gaps = [g for g in gaps if g.gap_type == "wording_gap"]
    if wording_gaps:
        recommendations.append(f"✏️  {len(wording_gaps)} wording improvements needed - rephrase to match job language")
    
    return recommendations


def _verify_no_hallucination(original_cv: dict, optimized_cv: dict) -> bool:
    """Verify that optimizations didn't add fabricated information."""
    for section, optimized_text in optimized_cv.items():
        # New content should be minimal
        original_section = original_cv.get("sections", {}).get(section, "").lower()
        if len(optimized_text) > len(original_section) * 1.5:
            logger.warning(f"Section '{section}' grew significantly - possible hallucination")
            return False
    
    return True


def _generate_summary(matching_result: SemanticMatchResult, optimization_result: CVOptimizationResult = None) -> str:
    """Generate human-readable summary."""
    score = matching_result.overall_score
    confidence = matching_result.confidence
    gaps = len(matching_result.gaps)
    critical = matching_result.critical_gaps
    
    summary = f"CV-JD Alignment: {score:.0%} ({confidence}). "
    summary += f"Identified {gaps} gaps ({critical} critical). "
    
    if optimization_result:
        delta = optimization_result.improvement_delta
        after = optimization_result.optimized_score
        summary += f"After optimization: {after:.0%} (+{delta:.0%}). "
    
    summary += f"Recommendations: {', '.join(matching_result.recommendations[:2])}"
    
    return summary
