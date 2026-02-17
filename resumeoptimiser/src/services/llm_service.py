"""LLM service using OpenRouter."""

import json
import logging
from typing import Optional, Dict, Any

from src.core.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    OPENROUTER_BASE_URL,
    OPENROUTER_SITE_URL,
    OPENROUTER_SITE_NAME,
)

logger = logging.getLogger("llm")

# Import OpenAI client with error handling
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠ OpenAI client not available: {e}. LLM parsing will not be available.")
    OPENAI_AVAILABLE = False
    OpenAI = None


class LLMService:
    """Service for interacting with OpenRouter LLM API."""

    def __init__(self):
        """Initialize LLM client."""
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not available. LLM service disabled.")
            self.client = None
            self.model = None
            self.extra_headers = None
            return
        
        if not OPENROUTER_API_KEY:
            logger.error("OPENROUTER_API_KEY not set in environment variables")
            raise ValueError("OPENROUTER_API_KEY not set in environment variables")

        logger.info(f"🔧 Initializing LLMService with model: {OPENROUTER_MODEL}")
        self.client = OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=OPENROUTER_API_KEY,
        )
        self.model = OPENROUTER_MODEL
        self.extra_headers = {
            "HTTP-Referer": OPENROUTER_SITE_URL,
            "X-Title": OPENROUTER_SITE_NAME,
        }
        logger.info("✓ LLMService initialized successfully")

    def parse_job_description(self, jd_text: str) -> Dict[str, Any]:
        """
        Parse job description using LLM.

        Args:
            jd_text: Raw job description text

        Returns:
            Dictionary with parsed structure:
            {
                "core_stack": [...],
                "secondary_stack": [...],
                "domain": [...],
                "seniority": "...",
                "keywords": [...]
            }
        """
        if not self.client:
            logger.error("LLM client not available. Cannot parse JD with LLM.")
            raise RuntimeError("LLM service not available")
        
        logger.debug(f"Parsing JD with LLM (model: {self.model})...")
        
        prompt = f"""Analyze this job description and extract the key information. 
Return a JSON object with the following structure:
{{
    "core_stack": [list of main technologies/skills required],
    "secondary_stack": [list of secondary technologies/nice-to-haves],
    "domain": [list of industry/domain keywords],
    "seniority": "junior/mid/senior/principal/cto",
    "keywords": [list of important keywords]
}}

Job Description:
{jd_text}

Return ONLY valid JSON, no other text."""

        try:
            logger.debug(f"Sending request to OpenRouter API ({self.model})...")
            response = self.client.chat.completions.create(
                extra_headers=self.extra_headers,
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent parsing
            )

            # Extract JSON from response
            response_text = response.choices[0].message.content
            logger.debug(f"LLM response received: {response_text[:100]}...")
            
            # Handle markdown code blocks (```json ... ```)
            if response_text.startswith("```"):
                logger.debug("Stripping markdown code blocks from response...")
                # Remove opening ```json or ``` and closing ```
                response_text = response_text.strip()
                if response_text.startswith("```"):
                    response_text = response_text[response_text.find("\n")+1:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                logger.debug(f"Cleaned response: {response_text[:100]}...")
            
            parsed = json.loads(response_text)
            logger.info(f"✓ JD parsed successfully with LLM: {len(parsed.get('core_stack', []))} core techs, seniority={parsed.get('seniority', 'unknown')}")
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response was: {response_text}")
            raise ValueError(f"LLM returned invalid JSON: {response_text}")
        except Exception as e:
            logger.error(f"LLM parsing error: {type(e).__name__}: {e}")
            raise

    def rewrite_cv_section(
        self,
        section_type: str,
        original_content: str,
        job_requirements: str,
        skills_matched: list
    ) -> str:
        """
        Rewrite a CV section to match job requirements.

        Args:
            section_type: "experience" or "skills"
            original_content: Original CV section content
            job_requirements: Parsed job requirements
            skills_matched: List of matched skills

        Returns:
            Rewritten section content
        """
        if not self.client:
            logger.warning("LLM client not available. Returning original content.")
            return original_content
        
        logger.debug(f"Rewriting CV {section_type} section with LLM...")
        
        if section_type == "experience":
            prompt = f"""You are an expert resume writer. Rewrite this experience section to better match the job requirements.

Original Experience Section:
{original_content}

Target Job Requirements:
{job_requirements}

Matched Skills to Highlight:
{', '.join(skills_matched)}

Guidelines:
- Keep the experience factual and truthful
- Emphasize relevant accomplishments
- Use strong action verbs
- Highlight technical achievements
- Keep it concise and impactful

Return ONLY the rewritten section, no other text."""

        elif section_type == "skills":
            prompt = f"""You are an expert resume writer. Reorganize this skills section to prioritize job requirements.

Original Skills Section:
{original_content}

Target Job Requirements:
{job_requirements}

Matched Skills (prioritize these):
{', '.join(skills_matched)}

Guidelines:
- Put most relevant skills first
- Group by category if possible
- Use industry terminology
- Be concise

Return ONLY the rewritten section, no other text."""

        else:
            return original_content

        try:
            response = self.client.chat.completions.create(
                extra_headers=self.extra_headers,
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Slightly higher for more creative writing
            )
            
            result = response.choices[0].message.content
            logger.info(f"✓ CV {section_type} section rewritten successfully")
            return result

        except Exception as e:
            logger.error(f"CV section rewriting error: {type(e).__name__}: {e}")
            # Return original if rewriting fails
            return original_content

    def generate_recommendation(
        self,
        cv_score: float,
        category: str,
        missing_skills: list,
        matched_skills: list
    ) -> str:
        """
        Generate a recommendation based on CV score.

        Args:
            cv_score: Total score (0-100)
            category: Score category (green/yellow/red)
            missing_skills: List of skills the candidate lacks
            matched_skills: List of matched skills

        Returns:
            Recommendation text
        """
        if not self.client:
            logger.warning("LLM client not available. Returning fallback recommendation.")
            if category == "green":
                return "Your profile is a strong match for this position. Consider highlighting your key achievements."
            elif category == "yellow":
                return "Your profile has potential matches. Consider deepening expertise in highlighted areas."
            else:
                return "Your profile would benefit from developing the key skills listed. Consider targeted learning."
        
        logger.debug("Generating AI recommendation...")
        
        prompt = f"""Generate a brief, actionable recommendation for a job candidate based on their CV analysis.

Score: {cv_score}/100 ({category.upper()})
Matched Skills: {', '.join(matched_skills)}
Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}

Guidelines:
- Be professional but encouraging
- Focus on what the candidate does well
- If score is low, suggest learning opportunities
- Keep it to 2-3 sentences

Return ONLY the recommendation text, no other text."""

        try:
            response = self.client.chat.completions.create(
                extra_headers=self.extra_headers,
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,
            )

            result = response.choices[0].message.content
            logger.info("✓ Recommendation generated successfully")
            return result

        except Exception as e:
            logger.error(f"Recommendation generation error: {type(e).__name__}: {e}")
            # Return generic recommendation if fails
            if category == "green":
                return "Your profile is a strong match for this position. Consider highlighting your key achievements."
            elif category == "yellow":
                return "Your profile has potential matches. Consider deepening expertise in highlighted areas."
            else:
                return "Your profile would benefit from developing the key skills listed. Consider targeted learning."


# Singleton instance
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create LLM service instance."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
