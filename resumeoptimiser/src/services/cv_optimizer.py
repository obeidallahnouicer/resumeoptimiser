"""
CV Optimizer: Rewrite CV sections using profile.md as source of truth.

Rule-based optimization with optional LLM enhancement for rewrites.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.services.embedder import get_embedder
from src.services.gap_analyzer import GapItem

logger = logging.getLogger("cv_optimizer")


@dataclass
class OptimizationResult:
    """Result of CV optimization."""
    original_text: str
    optimized_text: str
    improvements_made: List[str]
    score_before: float
    score_after: float
    improvement_delta: float


class CVOptimizer:
    """Optimizes CV content using profile and gap analysis."""
    
    def __init__(self):
        """Initialize CV optimizer."""
        self.embedder = get_embedder()
        logger.info("✓ CV optimizer initialized")
    
    def optimize_cv(
        self,
        cv_data: Dict[str, any],
        profile_data: Dict[str, any],
        gaps: List[GapItem],
        jd_data: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Optimize CV sections based on gaps and profile.
        
        Args:
            cv_data: Parsed CV data
            profile_data: Profile data from profile.md
            gaps: List of identified gaps
            jd_data: Job description data
            
        Returns:
            Optimized CV data with original and improved versions
        """
        logger.info("🔄 Optimizing CV...")
        
        optimized = {
            "original_sections": cv_data.get("sections", {}),
            "optimized_sections": {},
            "improvements": [],
            "warnings": []
        }
        
        # Optimize each section
        for section_name, section_text in cv_data.get("sections", {}).items():
            logger.debug(f"Optimizing section: {section_name}")
            
            optimized_section = self._optimize_section(
                section_name,
                section_text,
                profile_data,
                gaps,
                jd_data
            )
            
            if optimized_section["improved"]:
                optimized["optimized_sections"][section_name] = optimized_section["text"]
                optimized["improvements"].extend(optimized_section["improvements"])
            else:
                optimized["optimized_sections"][section_name] = section_text
        
        logger.info(f"✓ CV optimization complete - {len(optimized['improvements'])} improvements")
        return optimized
    
    def _optimize_section(
        self,
        section_name: str,
        section_text: str,
        profile_data: Dict,
        gaps: List[GapItem],
        jd_data: Dict
    ) -> Dict:
        """
        Optimize a single section.
        
        Args:
            section_name: Name of section
            section_text: Section text
            profile_data: Profile data
            gaps: List of gaps
            jd_data: JD data
            
        Returns:
            Dict with optimized text and improvements
        """
        result = {
            "text": section_text,
            "improved": False,
            "improvements": []
        }
        
        section_lower = section_name.lower()
        
        # Route to appropriate optimizer
        if any(x in section_lower for x in ["skill", "technical"]):
            result = self._optimize_skills_section(
                section_text, profile_data, gaps
            )
        elif any(x in section_lower for x in ["experience", "work", "professional"]):
            result = self._optimize_experience_section(
                section_text, gaps, jd_data
            )
        elif any(x in section_lower for x in ["education", "qualification"]):
            result = self._optimize_education_section(
                section_text, profile_data
            )
        
        return result
    
    def _optimize_skills_section(
        self,
        section_text: str,
        profile_data: Dict,
        gaps: List[GapItem]
    ) -> Dict:
        """
        Optimize skills section.
        
        Args:
            section_text: Original skills section
            profile_data: Profile data
            gaps: List of gaps
            
        Returns:
            Optimized section result
        """
        result = {
            "text": section_text,
            "improved": False,
            "improvements": []
        }
        
        # Find skill gaps that can be filled from profile
        skill_gaps = [g for g in gaps if g.gap_type == "skill_gap"]
        
        if not skill_gaps:
            return result
        
        optimized_lines = section_text.split('\n')
        additions = []
        
        # Check which skills from profile exist in CV
        profile_skills = self._extract_profile_skills(profile_data)
        cv_skills_lower = section_text.lower()
        
        for skill in profile_skills:
            skill_lower = skill.lower()
            
            # Check if mentioned in CV
            if skill_lower not in cv_skills_lower:
                # Check if this skill would help with any gap
                for gap in skill_gaps:
                    gap_embedding = self.embedder.embed([gap.requirement])[0]
                    skill_embedding = self.embedder.embed([skill])[0]
                    similarity = self.embedder.cosine_similarity(gap_embedding, skill_embedding)
                    
                    if similarity > 0.60:
                        additions.append(skill)
                        result["improvements"].append(
                            f"Added skill from profile: {skill}"
                        )
                        result["improved"] = True
                        break
        
        if additions:
            optimized_lines.append("\n".join(f"• {s}" for s in additions))
            result["text"] = "\n".join(optimized_lines)
        
        return result
    
    def _optimize_experience_section(
        self,
        section_text: str,
        gaps: List[GapItem],
        jd_data: Dict
    ) -> Dict:
        """
        Optimize experience section with better alignment to JD.
        
        Args:
            section_text: Original experience section
            profile_data: Profile data
            gaps: List of gaps
            jd_data: JD data
            
        Returns:
            Optimized section result
        """
        result = {
            "text": section_text,
            "improved": False,
            "improvements": []
        }
        
        # Extract key requirements from JD
        jd_keywords = self._extract_jd_keywords(jd_data)
        
        # Split into bullet points
        bullets = self._extract_bullets(section_text)
        
        if not bullets:
            return result
        
        optimized_bullets = []
        
        for bullet in bullets:
            bullet_lower = bullet.lower()
            
            # Check if bullet mentions key JD requirements
            mentioned_keywords = [kw for kw in jd_keywords if kw.lower() in bullet_lower]
            
            if mentioned_keywords:
                # Highlight these achievements
                optimized_bullets.append(self._enhance_bullet(bullet))
                result["improved"] = True
                result["improvements"].append(
                    f"Enhanced bullet point to highlight JD keywords: {bullet[:50]}..."
                )
            else:
                # Try to rephrase to align better
                enhanced = self._rephrase_for_alignment(bullet, jd_keywords)
                if enhanced != bullet:
                    optimized_bullets.append(enhanced)
                    result["improved"] = True
                    result["improvements"].append(
                        f"Rephrased bullet point for JD alignment: {bullet[:50]}..."
                    )
                else:
                    optimized_bullets.append(bullet)
        
        if optimized_bullets:
            result["text"] = "\n".join(optimized_bullets)
        
        return result
    
    def _optimize_education_section(
        self,
        section_text: str,
        profile_data: Dict
    ) -> Dict:
        """
        Optimize education section.
        
        Args:
            section_text: Original education section
            profile_data: Profile data
            
        Returns:
            Optimized section result
        """
        result = {
            "text": section_text,
            "improved": False,
            "improvements": []
        }
        
        # Extract education from profile
        profile_education = self._extract_profile_education(profile_data)
        
        if profile_education:
            # Ensure profile education is included
            if not any(edu.lower() in section_text.lower() for edu in profile_education):
                optimized_text = section_text + "\n\n" + "\n".join(profile_education)
                result["text"] = optimized_text
                result["improved"] = True
                result["improvements"].append(
                    f"Added {len(profile_education)} education items from profile"
                )
        
        return result
    
    def _extract_profile_skills(self, profile_data: Dict) -> List[str]:
        """Extract skills from profile.md."""
        profile_text = profile_data.get("raw_text", "")
        
        # Look for skills section
        skills_section_match = re.search(
            r'(?:skills|competencies|expertise)[:\s]+([\s\S]*)',
            profile_text,
            re.IGNORECASE
        )
        
        if not skills_section_match:
            return []
        
        skills_text = skills_section_match.group(1)
        # Find next section or end
        next_section = re.search(r'\n\n', skills_text)
        if next_section:
            skills_text = skills_text[:next_section.start()]
        
        # Extract skill items
        skills = re.findall(
            r'(?:^|\n)\s*(?:[-•]|\d+\.)\s*([^\n]+)',
            skills_text
        )
        
        return [s.strip() for s in skills if len(s.strip()) > 2]
    
    def _extract_profile_education(self, profile_data: Dict) -> List[str]:
        """Extract education from profile.md."""
        profile_text = profile_data.get("raw_text", "")
        
        # Look for education section
        edu_section_match = re.search(
            r'(?:education|academic|qualification)[:\s]+([\s\S]*)',
            profile_text,
            re.IGNORECASE
        )
        
        if not edu_section_match:
            return []
        
        edu_text = edu_section_match.group(1)
        # Find next section or end
        next_section = re.search(r'\n\n', edu_text)
        if next_section:
            edu_text = edu_text[:next_section.start()]
        
        # Extract education items
        education = re.findall(
            r'(?:^|\n)\s*(?:[-•]|\d+\.)\s*([^\n]+)',
            edu_text
        )
        
        return [e.strip() for e in education if len(e.strip()) > 10]
    
    def _extract_jd_keywords(self, jd_data: Dict) -> List[str]:
        """Extract key keywords from JD."""
        keywords = []
        
        sections = jd_data.get("sections", {})
        for section_text in sections.values():
            if not section_text:
                continue
            
            # Extract key terms (2-3 words)
            terms = re.findall(r'\b[a-z]+(?:\s+[a-z]+){0,2}\b', section_text.lower())
            keywords.extend(terms)
        
        # Remove duplicates and short words
        keywords = {kw for kw in keywords if len(kw) > 3}
        
        return list(keywords)[:20]  # Top 20 keywords
    
    def _extract_bullets(self, text: str) -> List[str]:
        """Extract bullet points from text."""
        bullets = re.split(r'\n\s*[•\-\*]\s*', text)
        return [b.strip() for b in bullets if b.strip()]
    
    def _enhance_bullet(self, bullet: str) -> str:
        """Enhance bullet to highlight key terms."""
        # Capitalize first letter
        enhanced = bullet[0].upper() + bullet[1:] if bullet else bullet
        
        # Ensure it's well-formatted
        return enhanced
    
    def _rephrase_for_alignment(self, bullet: str, jd_keywords: List[str]) -> str:
        """Try to rephrase bullet for better JD alignment."""
        # Check if bullet is already quite good
        bullet_lower = bullet.lower()
        mentioned = sum(1 for kw in jd_keywords if kw in bullet_lower)
        
        # For now, preserve original to avoid hallucination
        # In production, implement rule-based rewrites only
        return bullet if mentioned >= 2 else self._preserve_formatting(bullet)
    
    def _preserve_formatting(self, bullet: str) -> str:
        """Preserve bullet formatting (no rewrites to avoid hallucination)."""
        return bullet
    
    def compute_optimization_score(
        self,
        original_embedding: Dict[str, any],
        optimized_embedding: Dict[str, any],
        jd_embedding: Dict[str, any]
    ) -> Tuple[float, float]:
        """
        Compute similarity scores before and after optimization.
        
        Args:
            original_embedding: Original CV embeddings
            optimized_embedding: Optimized CV embeddings
            jd_embedding: JD embeddings
            
        Returns:
            Tuple of (original_score, optimized_score)
        """
        original_score = 0.0
        optimized_score = 0.0
        count = 0
        
        for section_name, jd_emb in jd_embedding.items():
            if section_name in original_embedding:
                cv_emb = original_embedding[section_name]
                original_score += self.embedder.cosine_similarity(cv_emb, jd_emb)
                count += 1
            
            if section_name in optimized_embedding:
                cv_emb = optimized_embedding[section_name]
                optimized_score += self.embedder.cosine_similarity(cv_emb, jd_emb)
        
        if count > 0:
            original_score /= count
            optimized_score /= count
        
        return float(original_score), float(optimized_score)
