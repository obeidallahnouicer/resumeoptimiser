"""
Gap Analyzer: Identify missing skills, wording gaps, and structural issues.

Performs deep analysis to categorize gaps and suggest improvements.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

from src.services.embedder import get_embedder
from src.services.jd_preprocessor import StructuredJD, StructuredRequirement

logger = logging.getLogger("gap_analyzer")

# Gap thresholds
WORDING_GAP_THRESHOLD = 0.50  # Semantically similar but not identical
STRONG_MATCH_THRESHOLD = 0.75


@dataclass
class GapItem:
    """Represents a gap between CV and JD."""
    gap_id: str
    requirement: str
    gap_type: str  # "skill_gap", "wording_gap", "structural_gap", "experience_gap"
    severity: str  # "critical", "high", "moderate", "low"
    similarity: float  # If applicable
    closest_match: Optional[str] = None
    suggested_improvement: Optional[str] = None
    source: Optional[str] = None  # Where this requirement appears in JD


class GapAnalyzer:
    """Analyzes gaps between CV and job description."""
    
    def __init__(self):
        """Initialize gap analyzer."""
        self.embedder = get_embedder()
        logger.info("✓ Gap analyzer initialized")
    
    def analyze_gaps(
        self,
        cv_data: Dict[str, any],
        jd_data: Union[Dict[str, any], StructuredJD],
        profile_data: Optional[Dict[str, str]] = None
    ) -> List[GapItem]:
        """
        Analyze all gaps between CV and JD.
        
        Args:
            cv_data: Parsed CV data
            jd_data: Parsed JD data (dict or StructuredJD from preprocessor)
            profile_data: Optional profile.md content
            
        Returns:
            List of gap items
        """
        logger.info("🔄 Analyzing gaps...")
        
        gaps = []
        
        # Check if using structured JD from preprocessor
        if isinstance(jd_data, StructuredJD):
            gaps = self._analyze_structured_gaps(
                cv_data, jd_data, profile_data
            )
        else:
            # Fall back to legacy method for dict-based JD
            gaps = self._analyze_legacy_gaps(
                cv_data, jd_data, profile_data
            )
        
        logger.info(f"✓ Identified {len(gaps)} gaps")
        return gaps

    def _analyze_structured_gaps(
        self,
        cv_data: Dict[str, any],
        structured_jd: StructuredJD,
        profile_data: Optional[Dict[str, str]] = None
    ) -> List[GapItem]:
        """
        Analyze gaps using LLM-structured JD (much higher quality).
        
        Args:
            cv_data: Parsed CV data
            structured_jd: StructuredJD from preprocessor
            profile_data: Optional profile.md content
            
        Returns:
            List of gap items
        """
        gaps = []
        
        # Extract CV content
        cv_skills = self._extract_cv_skills(cv_data)
        cv_text = cv_data.get("raw_text", "").lower()
        
        # Use all requirements from structured JD
        all_requirements = structured_jd.all_requirements
        
        logger.info(f"🔄 Analyzing {len(all_requirements)} structured requirements...")
        
        # Analyze each requirement (these are complete, not fragmented)
        for req in all_requirements:
            gap = self._analyze_structured_requirement(
                req, cv_skills, cv_text
            )
            if gap:
                gaps.append(gap)
        
        return gaps

    def _analyze_legacy_gaps(
        self,
        cv_data: Dict[str, any],
        jd_data: Dict[str, any],
        profile_data: Optional[Dict[str, str]] = None
    ) -> List[GapItem]:
        """
        Legacy gap analysis for dict-based JD (fallback).
        
        Args:
            cv_data: Parsed CV data
            jd_data: Parsed JD data (dict)
            profile_data: Optional profile.md content
            
        Returns:
            List of gap items
        """
        gaps = []
        gap_counter = 0
        
        # Extract requirements from JD
        jd_requirements = self._extract_requirements(jd_data)
        
        # Limit requirements to top 50 to avoid excessive processing
        if len(jd_requirements) > 50:
            logger.warning(f"⚠️  Limiting gap analysis to top 50 of {len(jd_requirements)} requirements")
            jd_requirements = jd_requirements[:50]
        
        # Extract CV content
        cv_skills = self._extract_cv_skills(cv_data)
        cv_text = cv_data.get("raw_text", "").lower()
        
        # Analyze each requirement
        for req in jd_requirements:
            gap_counter += 1
            gap = self._analyze_requirement(
                req, cv_skills, cv_text, profile_data, gap_counter
            )
            if gap:
                gaps.append(gap)
        
        return gaps
    
    def _analyze_requirement(
        self,
        requirement: Tuple[str, str],
        cv_skills: List[str],
        cv_text: str,
        profile_data: Optional[Dict],
        gap_id: int
    ) -> Optional[GapItem]:
        """
        Analyze a single requirement for gaps.

        Args:
            requirement: (requirement_text, source_section) tuple
            cv_skills: List of skills from CV
            cv_text: Full CV text (lowercase)
            profile_data: Profile data
            gap_id: Gap ID for tracking

        Returns:
            GapItem if gap found, None otherwise
        """
        req_text, source_section = requirement
        req_text_lower = req_text.lower()

        # Check for exact match in CV
        if req_text_lower in cv_text:
            return None  # No gap - exact match found

        # Extract key terms from requirement
        key_terms = self._extract_key_terms(req_text)

        if not key_terms:
            return None  # Cannot analyze

        # Check semantic similarity with CV skills
        similarities = self._find_similar_skills(key_terms, cv_skills)

        if similarities:
            best_match, best_score = max(similarities, key=lambda x: x[1])

            if best_score >= STRONG_MATCH_THRESHOLD:
                return None  # Strong match exists

            if best_score >= WORDING_GAP_THRESHOLD:
                # Wording gap - skill exists but not well-represented
                return GapItem(
                    gap_id=f"GAP_{gap_id:03d}",
                    requirement=req_text,
                    gap_type="wording_gap",
                    severity="moderate",
                    similarity=best_score,
                    closest_match=best_match,
                    source=source_section,
                    suggested_improvement=self._suggest_wording_improvement(
                        req_text, best_match
                    )
                )
            else:
                # Semantic gap - missing or low similarity
                return GapItem(
                    gap_id=f"GAP_{gap_id:03d}",
                    requirement=req_text,
                    gap_type="skill_gap",
                    severity="high",
                    similarity=best_score,
                    closest_match=best_match,
                    source=source_section,
                    suggested_improvement=self._suggest_skill_improvement(
                        req_text, profile_data
                    )
                )
        else:
            # No similar skills found
            return GapItem(
                gap_id=f"GAP_{gap_id:03d}",
                requirement=req_text,
                gap_type="skill_gap",
                severity="critical",
                similarity=0.0,
                source=source_section,
                suggested_improvement=self._suggest_skill_improvement(
                    req_text, profile_data
                )
            )

    def _extract_requirements(self, jd_data: Dict) -> List[Tuple[str, str]]:
        """
        Extract all requirements from JD.
        
        Args:
            jd_data: Parsed JD data
            
        Returns:
            List of (requirement, source_section) tuples
        """
        requirements = []
        
        # Extract from sections
        sections = jd_data.get("sections", {})
        for section_name, section_text in sections.items():
            if not section_text:
                continue
            
            # Split by bullet points
            bullets = re.split(r'[\n•\-\*]', section_text)
            for bullet in bullets:
                bullet = bullet.strip()
                if len(bullet) > 20:  # Minimum requirement length
                    requirements.append((bullet, section_name))
        
        logger.debug(f"Extracted {len(requirements)} requirements from JD")
        return requirements
    
    def _extract_cv_skills(self, cv_data: Dict) -> List[str]:
        """
        Extract skills from CV.
        
        Args:
            cv_data: Parsed CV data
            
        Returns:
            List of skill strings
        """
        skills = []
        
        # From skills section bullets
        bullets = cv_data.get("bullets", {})
        if "skills" in bullets:
            skills.extend(bullets["skills"])
        
        # From experience bullets
        if "experience" in bullets:
            skills.extend(bullets["experience"])
        
        # Parse skill keywords from text
        sections = cv_data.get("sections", {})
        if "skills" in sections:
            skill_section = sections["skills"]
            # Split by common delimiters
            parsed = re.split(r'[,;\n]', skill_section)
            skills.extend([s.strip() for s in parsed if len(s.strip()) > 2])
        
        return skills
    
    def _analyze_structured_requirement(
        self,
        requirement: StructuredRequirement,
        cv_skills: List[str],
        cv_text: str
    ) -> Optional[GapItem]:
        """
        Analyze a structured requirement from LLM-parsed JD.
        
        Work section by section (skills, experience, education, tools).
        Each category has different matching logic.
        
        Args:
            requirement: StructuredRequirement from JD preprocessor
            cv_skills: List of skills from CV
            cv_text: Full CV text (lowercase)
            
        Returns:
            GapItem if gap found, None otherwise
        """
        req_text = requirement.text
        req_text_lower = req_text.lower()
        req_category = requirement.category
        
        # Check for exact match in CV
        if req_text_lower in cv_text:
            return None  # No gap - exact match found
        
        # Route by category - work section by section
        if req_category == "skill":
            return self._analyze_skill_gap(requirement, cv_skills)
        elif req_category == "responsibility":
            return self._analyze_experience_gap(requirement, cv_text)
        elif req_category == "qualification":
            return self._analyze_education_gap(requirement, cv_text)
        else:
            # Generic analysis for other categories
            return self._analyze_generic_gap(requirement, cv_skills, cv_text)
    
    def _analyze_skill_gap(
        self,
        requirement: StructuredRequirement,
        cv_skills: List[str]
    ) -> Optional[GapItem]:
        """
        Analyze a SKILL requirement against CV skills section.
        
        Skills should match directly - either you have it or you don't.
        No "wording gaps" for skills - either it's there or it's missing.
        """
        req_text = requirement.text
        key_terms = requirement.keywords if requirement.keywords else self._extract_key_terms(req_text)
        
        if not key_terms:
            return None
        
        # Check exact skill match first
        for skill in cv_skills:
            if skill.lower() in req_text.lower() or req_text.lower() in skill.lower():
                return None  # Found it
        
        # Check semantic similarity
        similarities = self._find_similar_skills(key_terms, cv_skills)
        
        if similarities:
            _, best_score = max(similarities, key=lambda x: x[1])
            
            if best_score >= STRONG_MATCH_THRESHOLD:
                return None  # Strong match exists
            
            if best_score >= 0.60:  # Moderate match - still usable
                return None  # We'll give them credit
            
            # Below moderate - it's a gap
            severity = "critical" if requirement.section == "required" else "high"
            return GapItem(
                gap_id=requirement.id,
                requirement=req_text,
                gap_type="skill_gap",
                severity=severity,
                similarity=best_score,
                source="skills",
                suggested_improvement=f"Add '{req_text}' to your skills section"
            )
        
        # Missing skill
        severity = "critical" if requirement.section == "required" else "high"
        return GapItem(
            gap_id=requirement.id,
            requirement=req_text,
            gap_type="skill_gap",
            severity=severity,
            similarity=0.0,
            source="skills",
            suggested_improvement=f"Add '{req_text}' to your skills section"
        )
    
    def _analyze_experience_gap(
        self,
        requirement: StructuredRequirement,
        cv_text: str
    ) -> Optional[GapItem]:
        """
        Analyze an EXPERIENCE/RESPONSIBILITY requirement.
        
        These match against experience section - looking for evidence of doing similar work.
        """
        req_text = requirement.text
        key_terms = requirement.keywords if requirement.keywords else self._extract_key_terms(req_text)
        
        if not key_terms:
            return None
        
        # Check if any key term appears in CV experience
        for term in key_terms:
            if term.lower() in cv_text:
                return None  # Found evidence
        
        # No match found
        severity = "critical" if requirement.section == "required" else "moderate"
        return GapItem(
            gap_id=requirement.id,
            requirement=req_text,
            gap_type="experience_gap",
            severity=severity,
            similarity=0.0,
            source="experience",
            suggested_improvement=f"Add experience with: {req_text}"
        )
    
    def _analyze_education_gap(
        self,
        requirement: StructuredRequirement,
        cv_text: str
    ) -> Optional[GapItem]:
        """
        Analyze an EDUCATION/QUALIFICATION requirement.
        
        These match against education section - degree, certifications, etc.
        """
        req_text = requirement.text
        key_terms = requirement.keywords if requirement.keywords else self._extract_key_terms(req_text)
        
        if not key_terms:
            return None
        
        # Check if any key term appears in CV education
        for term in key_terms:
            if term.lower() in cv_text:
                return None  # Found it
        
        # No match found
        severity = "high" if requirement.section == "required" else "moderate"
        return GapItem(
            gap_id=requirement.id,
            requirement=req_text,
            gap_type="education_gap",
            severity=severity,
            similarity=0.0,
            source="education",
            suggested_improvement=f"Add to education: {req_text}"
        )
    
    def _analyze_generic_gap(
        self,
        requirement: StructuredRequirement,
        cv_skills: List[str],
        cv_text: str
    ) -> Optional[GapItem]:
        """
        Generic analysis for uncategorized requirements.
        """
        req_text = requirement.text
        key_terms = requirement.keywords if requirement.keywords else self._extract_key_terms(req_text)
        
        if not key_terms:
            return None
        
        similarities = self._find_similar_skills(key_terms, cv_skills)
        
        best_score = 0.0
        if similarities:
            _, best_score = max(similarities, key=lambda x: x[1])
            
            if best_score >= STRONG_MATCH_THRESHOLD:
                return None
            
            if best_score >= 0.60:
                return None
        
        severity = "high" if requirement.section == "required" else "moderate"
        return GapItem(
            gap_id=requirement.id,
            requirement=req_text,
            gap_type="requirement_gap",
            severity=severity,
            similarity=best_score,
            source=requirement.section,
            suggested_improvement=f"Address requirement: {req_text}"
        )
    
    def _analyze_requirement(
        self,
        requirement: Tuple[str, str],
        cv_skills: List[str],
        cv_text: str,
        profile_data: Optional[Dict],
        gap_id: int
    ) -> Optional[GapItem]:
        """
        Analyze a single requirement for gaps.
        
        Args:
            requirement: (requirement_text, source_section) tuple
            cv_skills: List of skills from CV
            cv_text: Full CV text (lowercase)
            profile_data: Profile data
            gap_id: Gap ID for tracking
            
        Returns:
            GapItem if gap found, None otherwise
        """
        req_text, source_section = requirement
        req_text_lower = req_text.lower()
        
        # Check for exact match in CV
        if req_text_lower in cv_text:
            return None  # No gap - exact match found
        
        # Extract key terms from requirement
        key_terms = self._extract_key_terms(req_text)
        
        if not key_terms:
            return None  # Cannot analyze
        
        # Check semantic similarity with CV skills
        similarities = self._find_similar_skills(key_terms, cv_skills)
        
        if similarities:
            best_match, best_score = max(similarities, key=lambda x: x[1])
            
            if best_score >= STRONG_MATCH_THRESHOLD:
                return None  # Strong match exists
            
            if best_score >= WORDING_GAP_THRESHOLD:
                # Wording gap - skill exists but not well-represented
                return GapItem(
                    gap_id=f"GAP_{gap_id:03d}",
                    requirement=req_text,
                    gap_type="wording_gap",
                    severity="moderate",
                    similarity=best_score,
                    closest_match=best_match,
                    source=source_section,
                    suggested_improvement=self._suggest_wording_improvement(
                        req_text, best_match
                    )
                )
            else:
                # Semantic gap - missing or low similarity
                return GapItem(
                    gap_id=f"GAP_{gap_id:03d}",
                    requirement=req_text,
                    gap_type="skill_gap",
                    severity="high",
                    similarity=best_score,
                    closest_match=best_match,
                    source=source_section,
                    suggested_improvement=self._suggest_skill_improvement(
                        req_text, profile_data
                    )
                )
        else:
            # No similar skills found
            return GapItem(
                gap_id=f"GAP_{gap_id:03d}",
                requirement=req_text,
                gap_type="skill_gap",
                severity="critical",
                similarity=0.0,
                source=source_section,
                suggested_improvement=self._suggest_skill_improvement(
                    req_text, profile_data
                )
            )
    
    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract key terms from requirement.
        
        Args:
            text: Requirement text
            
        Returns:
            List of key terms
        """
        # Remove common words
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "as", "is", "are", "be",
            "have", "has", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "must", "can"
        }
        
        words = text.lower().split()
        terms = [
            w.strip('.,!?;:') for w in words
            if len(w) > 3 and w.lower() not in stopwords
        ]
        
        return terms[:5]  # Top 5 key terms
    
    def _find_similar_skills(
        self,
        key_terms: List[str],
        cv_skills: List[str]
    ) -> List[Tuple[str, float]]:
        """
        Find CV skills similar to key terms.
        
        Args:
            key_terms: Key terms from requirement
            cv_skills: Available CV skills
            
        Returns:
            List of (skill, similarity_score) tuples
        """
        if not key_terms or not cv_skills:
            return []
        
        similarities = []
        
        # Batch embed all terms and skills at once (much faster!)
        all_texts = key_terms + cv_skills
        all_embeddings = self.embedder.embed(all_texts)
        
        term_embeddings = all_embeddings[:len(key_terms)]
        skill_embeddings = all_embeddings[len(key_terms):]
        
        # Compare each term to each skill
        for i, term in enumerate(key_terms):
            best_match = None
            best_score = 0.0
            
            for j, skill in enumerate(cv_skills):
                score = self.embedder.cosine_similarity(term_embeddings[i], skill_embeddings[j])
                
                if score > best_score:
                    best_score = score
                    best_match = skill
            
            if best_match and best_score > WORDING_GAP_THRESHOLD:
                similarities.append((best_match, best_score))
        
        # Return unique matches with highest scores
        seen = set()
        unique_similarities = []
        for skill, score in sorted(similarities, key=lambda x: x[1], reverse=True):
            if skill not in seen:
                unique_similarities.append((skill, score))
                seen.add(skill)
        
        return unique_similarities
    
    def _suggest_wording_improvement(
        self,
        requirement: str,
        existing_match: str
    ) -> str:
        """
        Suggest how to rephrase CV to match requirement better.
        
        Args:
            requirement: JD requirement
            existing_match: Existing CV skill
            
        Returns:
            Suggested improvement text
        """
        return f"Rephrase '{existing_match}' to include: {requirement}"
    
    def _suggest_skill_improvement(
        self,
        requirement: str,
        profile_data: Optional[Dict]
    ) -> str:
        """
        Suggest how to add missing skill from profile.
        
        Args:
            requirement: Missing requirement
            profile_data: Profile content
            
        Returns:
            Suggested improvement text
        """
        # Check if skill exists in profile
        if profile_data:
            profile_text = profile_data.get("raw_text", "").lower()
            req_lower = requirement.lower()
            
            if any(term in profile_text for term in req_lower.split()[:3]):
                return f"Add from profile.md: '{requirement}' is mentioned in your experience"
        
        return f"Consider adding: {requirement}"
    
    def categorize_gaps(self, gaps: List[GapItem]) -> Dict[str, List[GapItem]]:
        """
        Categorize gaps by type.
        
        Args:
            gaps: List of gap items
            
        Returns:
            Dict mapping gap_type to list of gaps
        """
        categorized = {
            "skill_gap": [],
            "wording_gap": [],
            "structural_gap": [],
            "experience_gap": []
        }
        
        for gap in gaps:
            categorized.setdefault(gap.gap_type, []).append(gap)
        
        return {k: v for k, v in categorized.items() if v}
    
    def prioritize_gaps(self, gaps: List[GapItem]) -> List[GapItem]:
        """
        Sort gaps by priority (severity and similarity).
        
        Args:
            gaps: List of gap items
            
        Returns:
            Sorted list with highest priority first
        """
        severity_rank = {
            "critical": 3,
            "high": 2,
            "moderate": 1,
            "low": 0
        }
        
        def priority_key(gap: GapItem) -> Tuple[int, float]:
            return (
                severity_rank.get(gap.severity, -1),
                -gap.similarity  # Higher similarity = lower priority (easier to fix)
            )
        
        return sorted(gaps, key=priority_key, reverse=True)
