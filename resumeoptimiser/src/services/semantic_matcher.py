"""
Semantic Matcher: Section-aware CV to job description matching.

Computes weighted similarity scores based on:
- Hard skills match (40%)
- Experience alignment (30%)
- Responsibilities alignment (20%)
- Education/domain alignment (10%)
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from src.services.embedder import get_embedder

logger = logging.getLogger("semantic_matcher")

# Weighting configuration for scoring
WEIGHTS = {
    "hard_skills": 0.40,
    "experience": 0.30,
    "responsibilities": 0.20,
    "education": 0.10
}

# Similarity thresholds
STRONG_MATCH_THRESHOLD = 0.75
VIABLE_MATCH_THRESHOLD = 0.60
RISKY_MATCH_THRESHOLD = 0.45


@dataclass
class MatchResult:
    """Result of matching a single item."""
    matched_item: str
    similarity_score: float
    section: str
    confidence: str  # "strong", "viable", "risky", "low"
    explanation: Optional[str] = None


@dataclass
class SectionSimilarity:
    """Similarity scores for a CV section."""
    section_name: str
    overall_score: float
    matches: List[MatchResult]
    unmapped_requirements: List[str]
    coverage_ratio: float  # percentage of requirements covered


class SemanticMatcher:
    """Performs semantic matching between CV and job description."""
    
    def __init__(self):
        """Initialize semantic matcher."""
        self.embedder = get_embedder()
        logger.info("✓ Semantic matcher initialized")
    
    def match_cv_to_jd(
        self,
        cv_sections: Dict[str, str],
        jd_sections: Dict[str, str]
    ) -> Dict[str, any]:
        """
        Match CV sections to job description.
        
        Args:
            cv_sections: Dict of {section_name: section_text} from CV
            jd_sections: Dict of {section_name: section_text} from JD
            
        Returns:
            Comprehensive matching result with scores and analysis
        """
        logger.info("🔄 Starting semantic matching...")
        
        results = {
            "overall_score": 0.0,
            "section_scores": {},
            "top_matches": [],
            "missing_requirements": [],
            "gaps": [],
            "weighted_breakdown": {}
        }
        
        # Match each section
        for jd_section, jd_text in jd_sections.items():
            if not jd_text.strip():
                continue
            
            logger.debug(f"Matching section: {jd_section}")
            best_match_score = 0.0
            best_cv_section = None
            
            for cv_section, cv_text in cv_sections.items():
                if not cv_text.strip():
                    continue
                
                score = self._compute_semantic_similarity(jd_text, cv_text)
                
                if score > best_match_score:
                    best_match_score = score
                    best_cv_section = cv_section
            
            if best_cv_section:
                results["section_scores"][jd_section] = {
                    "cv_section": best_cv_section,
                    "similarity": best_match_score,
                    "confidence": self._classify_confidence(best_match_score)
                }
                logger.debug(f"  {jd_section} → {best_cv_section}: {best_match_score:.2%}")
        
        # Compute weighted overall score
        results["overall_score"] = self._compute_weighted_score(
            results["section_scores"]
        )
        
        # Analyze gaps
        results["gaps"] = self._analyze_gaps(
            jd_sections, results["section_scores"]
        )
        
        logger.info(f"✓ Matching complete - Overall score: {results['overall_score']:.2%}")
        return results
    
    def _compute_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Compute semantic similarity between two text segments.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0-1)
        """
        # Clean and normalize texts
        text1 = self._normalize_text(text1)
        text2 = self._normalize_text(text2)
        
        if not text1 or not text2:
            return 0.0
        
        # Embed both texts
        embedding1 = self.embedder.embed([text1])[0]
        embedding2 = self.embedder.embed([text2])[0]
        
        # Compute cosine similarity
        similarity = self.embedder.cosine_similarity(embedding1, embedding2)
        return similarity
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for comparison.
        
        Args:
            text: Raw text
            
        Returns:
            Normalized text
        """
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Convert to lowercase
        text = text.lower()
        return text.strip()
    
    def _classify_confidence(self, score: float) -> str:
        """
        Classify confidence level based on score.
        
        Args:
            score: Similarity score (0-1)
            
        Returns:
            Confidence classification
        """
        if score >= STRONG_MATCH_THRESHOLD:
            return "strong"
        elif score >= VIABLE_MATCH_THRESHOLD:
            return "viable"
        elif score >= RISKY_MATCH_THRESHOLD:
            return "risky"
        else:
            return "low"
    
    def _compute_weighted_score(self, section_scores: Dict) -> float:
        """
        Compute weighted overall score.
        
        Args:
            section_scores: Section-level similarity scores
            
        Returns:
            Weighted overall score (0-1)
        """
        if not section_scores:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        # Map JD sections to weight categories
        section_weights = {
            "hard_skills": WEIGHTS["hard_skills"],
            "skills": WEIGHTS["hard_skills"],
            "technical": WEIGHTS["hard_skills"],
            "experience": WEIGHTS["experience"],
            "work_experience": WEIGHTS["experience"],
            "professional_experience": WEIGHTS["experience"],
            "responsibilities": WEIGHTS["responsibilities"],
            "requirements": WEIGHTS["responsibilities"],
            "education": WEIGHTS["education"],
            "qualifications": WEIGHTS["education"],
            "degree": WEIGHTS["education"],
            "summary": 0.0,  # Not weighted
            "about": 0.0
        }
        
        for section, data in section_scores.items():
            section_lower = section.lower()
            weight = 0.0
            
            # Find matching weight
            for key, w in section_weights.items():
                if key in section_lower:
                    weight = w
                    break
            
            if weight > 0:
                weighted_sum += data["similarity"] * weight
                total_weight += weight
        
        # Normalize
        if total_weight > 0:
            overall_score = weighted_sum / total_weight
        else:
            overall_score = np.mean([s["similarity"] for s in section_scores.values()])
        
        return float(np.clip(overall_score, 0.0, 1.0))
    
    def _analyze_gaps(
        self,
        jd_sections: Dict[str, str],
        section_scores: Dict
    ) -> List[Dict]:
        """
        Analyze gaps between CV and JD.
        
        Args:
            jd_sections: JD sections
            section_scores: Matching scores
            
        Returns:
            List of gap analyses
        """
        gaps = []
        
        for jd_section, jd_text in jd_sections.items():
            if not jd_text.strip():
                continue
            
            score_data = section_scores.get(jd_section, {})
            similarity = score_data.get("similarity", 0.0)
            
            if similarity < VIABLE_MATCH_THRESHOLD:
                gap = {
                    "section": jd_section,
                    "severity": self._classify_gap_severity(similarity),
                    "similarity": similarity,
                    "type": self._classify_gap_type(jd_section),
                    "requirement_snippet": jd_text[:200]  # First 200 chars
                }
                gaps.append(gap)
        
        return gaps
    
    def _classify_gap_severity(self, score: float) -> str:
        """
        Classify gap severity.
        
        Args:
            score: Similarity score
            
        Returns:
            Severity classification
        """
        if score >= VIABLE_MATCH_THRESHOLD:
            return "none"
        elif score >= RISKY_MATCH_THRESHOLD:
            return "moderate"
        else:
            return "critical"
    
    def _classify_gap_type(self, section: str) -> str:
        """
        Classify type of gap.
        
        Args:
            section: Section name
            
        Returns:
            Gap type
        """
        section_lower = section.lower()
        
        if any(x in section_lower for x in ["skill", "technical", "tool"]):
            return "skill_gap"
        elif any(x in section_lower for x in ["experience", "work", "professional"]):
            return "experience_gap"
        elif any(x in section_lower for x in ["education", "degree", "qualification"]):
            return "education_gap"
        else:
            return "experience_gap"
    
    def match_skill_list(
        self,
        cv_skills: List[str],
        jd_skills: List[str]
    ) -> Dict[str, any]:
        """
        Match skills lists with detailed similarity.
        
        Args:
            cv_skills: List of skills from CV
            jd_skills: List of skills from job description
            
        Returns:
            Detailed skill matching result
        """
        logger.info(f"🔄 Matching {len(jd_skills)} required skills...")
        
        result = {
            "total_required": len(jd_skills),
            "strong_matches": [],
            "viable_matches": [],
            "risky_matches": [],
            "missing": [],
            "match_ratio": 0.0
        }
        
        if not jd_skills:
            return result
        
        # Embed all skills
        cv_embeddings = self.embedder.embed(cv_skills)
        jd_embeddings = self.embedder.embed(jd_skills)
        
        matched_count = 0
        
        for jd_idx, jd_skill in enumerate(jd_skills):
            jd_embedding = jd_embeddings[jd_idx]
            best_match = None
            best_score = 0.0
            
            # Find best match
            for cv_idx, cv_skill in enumerate(cv_skills):
                cv_embedding = cv_embeddings[cv_idx]
                score = self.embedder.cosine_similarity(jd_embedding, cv_embedding)
                
                if score > best_score:
                    best_score = score
                    best_match = cv_skill
            
            if best_score >= STRONG_MATCH_THRESHOLD:
                result["strong_matches"].append({
                    "required": jd_skill,
                    "matched": best_match,
                    "similarity": best_score
                })
                matched_count += 1
            elif best_score >= VIABLE_MATCH_THRESHOLD:
                result["viable_matches"].append({
                    "required": jd_skill,
                    "matched": best_match,
                    "similarity": best_score
                })
                matched_count += 1
            elif best_score >= RISKY_MATCH_THRESHOLD:
                result["risky_matches"].append({
                    "required": jd_skill,
                    "matched": best_match,
                    "similarity": best_score
                })
            else:
                result["missing"].append(jd_skill)
        
        result["match_ratio"] = matched_count / len(jd_skills) if jd_skills else 0.0
        
        logger.info(
            f"✓ Skill matching: {matched_count}/{len(jd_skills)} strong+viable matches"
        )
        return result


def get_matcher() -> SemanticMatcher:
    """Get semantic matcher instance."""
    return SemanticMatcher()
