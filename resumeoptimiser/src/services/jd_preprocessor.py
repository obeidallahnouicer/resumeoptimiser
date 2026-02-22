"""
JD Preprocessor: LLM-powered job description parsing and structuring.

Uses an LLM to intelligently parse job descriptions into structured
requirements before semantic matching. This ensures:
- Complete requirement understanding (no fragmentation)
- Semantic grouping of related skills
- Removal of duplicates/redundancy
- Clear skill vs responsibility vs qualification distinction
"""

import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.services.llm_service import get_llm_service

logger = logging.getLogger("jd_preprocessor")


@dataclass
class StructuredRequirement:
    """A single requirement parsed from JD."""
    id: str
    text: str
    category: str  # "skill", "responsibility", "qualification", "nice_to_have"
    section: str  # "required", "preferred"
    keywords: List[str]  # Extracted keywords
    proficiency_level: Optional[str] = None  # "basic", "intermediate", "advanced"


@dataclass
class StructuredJD:
    """Fully structured job description."""
    title: str
    company: Optional[str]
    description: str
    required_skills: List[StructuredRequirement]
    preferred_skills: List[StructuredRequirement]
    responsibilities: List[StructuredRequirement]
    qualifications: List[StructuredRequirement]
    all_requirements: List[StructuredRequirement]  # Flattened list

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "required_skills": [
                {
                    "id": r.id,
                    "text": r.text,
                    "category": r.category,
                    "keywords": r.keywords,
                    "proficiency_level": r.proficiency_level
                }
                for r in self.required_skills
            ],
            "preferred_skills": [
                {
                    "id": r.id,
                    "text": r.text,
                    "category": r.category,
                    "keywords": r.keywords,
                    "proficiency_level": r.proficiency_level
                }
                for r in self.preferred_skills
            ],
            "responsibilities": [
                {
                    "id": r.id,
                    "text": r.text,
                    "category": r.category,
                    "keywords": r.keywords
                }
                for r in self.responsibilities
            ],
            "qualifications": [
                {
                    "id": r.id,
                    "text": r.text,
                    "category": r.category,
                    "keywords": r.keywords
                }
                for r in self.qualifications
            ]
        }


class JDPreprocessor:
    """Intelligently parse and structure job descriptions using LLM."""

    def __init__(self):
        """Initialize preprocessor."""
        self.llm = get_llm_service()
        logger.info("✓ JD preprocessor initialized with LLM backend")

    def preprocess(self, job_description: str) -> StructuredJD:
        """
        Parse job description into structured requirements using LLM.

        Args:
            job_description: Raw job description text

        Returns:
            StructuredJD with parsed requirements
        """
        logger.info("🧠 Preprocessing job description with OpenRouter LLM...")

        # Step 1: Extract basic info (title, company)
        basic_info = self._extract_basic_info(job_description)
        logger.info(f"✓ Extracted basic info: {basic_info['title']}")

        # Step 2: Parse requirements into categories
        parsed_requirements = self._parse_requirements(job_description)
        logger.info(f"✓ Parsed {len(parsed_requirements)} requirements")

        # Step 3: Deduplicate and normalize
        deduplicated = self._deduplicate_requirements(parsed_requirements)
        logger.info(f"✓ Deduplicated to {len(deduplicated)} unique requirements")

        # Step 4: Extract keywords for each requirement
        requirements_with_keywords = self._extract_keywords(deduplicated)

        # Step 5: Categorize requirements
        categorized = self._categorize_requirements(requirements_with_keywords)

        # Build structured JD
        structured_jd = StructuredJD(
            title=basic_info.get("title", "Unknown Position"),
            company=basic_info.get("company"),
            description=job_description[:500],  # First 500 chars as summary
            required_skills=categorized.get("required_skills", []),
            preferred_skills=categorized.get("preferred_skills", []),
            responsibilities=categorized.get("responsibilities", []),
            qualifications=categorized.get("qualifications", []),
            all_requirements=categorized.get("all", [])
        )

        logger.info(
            f"✓ LLM JD preprocessing complete: "
            f"{len(structured_jd.required_skills)} required skills, "
            f"{len(structured_jd.preferred_skills)} preferred skills, "
            f"{len(structured_jd.responsibilities)} responsibilities"
        )

        return structured_jd

    def _extract_basic_info(self, jd: str) -> Dict[str, str]:
        """
        Extract job title and company from JD.

        Args:
            jd: Job description text

        Returns:
            Dict with title and company
        """
        prompt = f"""Extract the job title and company name from this job description.
        
Job Description:
{jd[:1000]}

Return as JSON:
{{
    "title": "Job title",
    "company": "Company name or null"
}}"""

        try:
            response = self.llm.generate(prompt, max_tokens=200)
            data = json.loads(response)
            return data
        except Exception as e:
            logger.warning(f"⚠️  Failed to extract basic info: {e}")
            # Fallback: try to extract from first lines
            lines = jd.split('\n')
            title = "Unknown Position"
            company = None
            for line in lines[:5]:
                if 'position' in line.lower() or 'role' in line.lower():
                    title = line.strip()
                if 'company' in line.lower() or 'at ' in line.lower():
                    company = line.strip()
            return {"title": title, "company": company}

    def _parse_requirements(self, jd: str) -> List[Dict]:
        """
        Parse JD into individual requirements using LLM.

        Args:
            jd: Job description text

        Returns:
            List of parsed requirements
        """
        prompt = f"""Parse this job description into distinct requirements.
Return ONLY valid JSON with no markdown formatting.

For each requirement:
- Extract the complete, standalone text
- Identify if it's in "required" or "preferred" section
- Classify as "skill", "responsibility", or "qualification"

Job Description:
{jd}

Return as JSON:
{{
    "requirements": [
        {{
            "text": "Complete requirement text",
            "section": "required" or "preferred",
            "type": "skill", "responsibility", or "qualification"
        }},
        ...
    ]
}}

Important:
- Each requirement must be complete and understandable on its own
- Do NOT fragment sentences (e.g., don't split "Design and develop AI applications" into two requirements)
- Do NOT include generic statements like job titles or company info
- Remove duplicates within the same category
- Keep requirements that describe actual work, skills, or qualifications"""

        try:
            response = self.llm.generate(prompt, max_tokens=2000)
            # Clean response - remove markdown formatting if present
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
                response = response.strip()

            data = json.loads(response)
            requirements = data.get("requirements", [])
            logger.info(f"✓ Parsed {len(requirements)} requirements from LLM")
            return requirements
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response was: {response[:200]}")
            return []
        except Exception as e:
            logger.warning(f"⚠️  Error parsing requirements: {e}")
            return []

    def _deduplicate_requirements(self, requirements: List[Dict]) -> List[Dict]:
        """
        Remove duplicate or very similar requirements.

        Args:
            requirements: List of parsed requirements

        Returns:
            Deduplicated list
        """
        if not requirements:
            return []

        prompt = f"""Remove duplicate requirements from this list. 
Keep only distinct requirements, removing near-duplicates and rephrased versions.

Requirements:
{json.dumps(requirements, indent=2)}

Return as JSON:
{{
    "deduplicated": [
        {{
            "text": "...",
            "section": "...",
            "type": "..."
        }},
        ...
    ]
}}

Keep conceptually distinct requirements even if worded differently.
Remove true duplicates."""

        try:
            response = self.llm.generate(prompt, max_tokens=2000)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
                response = response.strip()

            data = json.loads(response)
            return data.get("deduplicated", requirements)
        except Exception as e:
            logger.warning(f"⚠️  Deduplication failed, using original list: {e}")
            return requirements

    def _extract_keywords(self, requirements: List[Dict]) -> List[Dict]:
        """
        Extract keywords from each requirement.

        Args:
            requirements: Parsed requirements

        Returns:
            Requirements with keywords extracted
        """
        if not requirements:
            return []

        prompt = f"""For each requirement, extract 2-5 key keywords/phrases.

Requirements:
{json.dumps(requirements, indent=2)}

Return as JSON:
{{
    "requirements": [
        {{
            "text": "...",
            "section": "...",
            "type": "...",
            "keywords": ["keyword1", "keyword2", ...]
        }},
        ...
    ]
}}

Keywords should be:
- Specific technical terms, skills, or concepts
- Short (1-3 words typically)
- The most important parts of the requirement
- Suitable for semantic matching"""

        try:
            response = self.llm.generate(prompt, max_tokens=2000)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
                response = response.strip()

            data = json.loads(response)
            return data.get("requirements", requirements)
        except Exception as e:
            logger.warning(f"⚠️  Keyword extraction failed: {e}")
            # Add empty keywords if extraction fails
            for req in requirements:
                req["keywords"] = []
            return requirements

    def _categorize_requirements(
        self, requirements: List[Dict]
    ) -> Dict[str, List[StructuredRequirement]]:
        """
        Categorize requirements and create StructuredRequirement objects.

        Args:
            requirements: Requirements with keywords

        Returns:
            Dict with categorized requirements
        """
        categorized = {
            "required_skills": [],
            "preferred_skills": [],
            "responsibilities": [],
            "qualifications": [],
            "all": []
        }

        req_id = 0
        for req in requirements:
            req_id += 1
            req_text = req.get("text", "")
            section = req.get("section", "required")
            req_type = req.get("type", "skill")
            keywords = req.get("keywords", [])

            structured = StructuredRequirement(
                id=f"REQ_{req_id:03d}",
                text=req_text,
                category=req_type,
                section=section,
                keywords=keywords,
                proficiency_level=self._infer_proficiency(req_text)
            )

            # Categorize
            if req_type == "skill":
                if section == "required":
                    categorized["required_skills"].append(structured)
                else:
                    categorized["preferred_skills"].append(structured)
            elif req_type == "responsibility":
                categorized["responsibilities"].append(structured)
            elif req_type == "qualification":
                categorized["qualifications"].append(structured)

            categorized["all"].append(structured)

        return categorized

    def _infer_proficiency(self, requirement_text: str) -> Optional[str]:
        """
        Infer proficiency level from requirement text.

        Args:
            requirement_text: Requirement text

        Returns:
            "basic", "intermediate", "advanced", or None
        """
        text_lower = requirement_text.lower()

        if any(word in text_lower for word in ["expert", "advanced", "deep", "mastery"]):
            return "advanced"
        elif any(
            word in text_lower for word in ["experience with", "familiar with", "knowledge"]
        ):
            return "intermediate"
        elif any(word in text_lower for word in ["understand", "basic", "awareness"]):
            return "basic"

        return None


def get_jd_preprocessor() -> JDPreprocessor:
    """Get or create JD preprocessor instance."""
    return JDPreprocessor()
