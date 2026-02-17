"""JD parsing service."""

import re
import logging
from typing import List, Dict, Optional
from src.models.schemas import ParsedJobDescription
from src.core.config import CORE_TECH_STACK, SECONDARY_TECH_STACK, DOMAIN_KEYWORDS, SeniorityLevel

logger = logging.getLogger("generation")


def parse_jd_with_regex(jd_text: str) -> ParsedJobDescription:
    """
    Parse job description using regex and keyword extraction.
    
    Args:
        jd_text: Raw job description text
        
    Returns:
        ParsedJobDescription with extracted structure
    """
    # Extract technologies
    jd_lower = jd_text.lower()
    found_core = [tech for tech in CORE_TECH_STACK if tech.lower() in jd_lower]
    found_secondary = [tech for tech in SECONDARY_TECH_STACK if tech.lower() in jd_lower]

    # Extract seniority level
    seniority = SeniorityLevel.MID.value
    seniority_keywords = {
        SeniorityLevel.PRINCIPAL: ["principal", "distinguished", "fellow"],
        SeniorityLevel.SENIOR: ["senior", "lead", "staff", "architect"],
        SeniorityLevel.JUNIOR: ["junior", "entry", "entry-level", "graduate"],
    }
    
    for level, keywords in seniority_keywords.items():
        if any(word in jd_lower for word in keywords):
            seniority = level.value
            break

    # Extract domain
    domains = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in jd_lower for kw in keywords):
            domains.append(domain)

    # Extract keywords
    keywords = re.findall(r'\b[a-z]+(?:\s+[a-z]+)?\b', jd_lower)
    keywords = list(set(keywords))[:20]  # Top 20 unique keywords

    return ParsedJobDescription(
        core_stack=list(set(found_core)),
        secondary_stack=list(set(found_secondary)),
        domain=domains,
        seniority=seniority,
        keywords=keywords,
        raw_jd=jd_text
    )


def parse_jd_with_llm(jd_text: str) -> ParsedJobDescription:
    """
    Parse job description using LLM (OpenRouter).
    Falls back to regex extraction if LLM fails.
    
    Args:
        jd_text: Raw job description text
        
    Returns:
        ParsedJobDescription with extracted structure
    """
    try:
        from src.services.llm_service import get_llm_service
        
        logger.info("Attempting to parse JD with LLM...")
        llm = get_llm_service()
        parsed_data = llm.parse_job_description(jd_text)
        
        return ParsedJobDescription(
            core_stack=parsed_data.get("core_stack", []),
            secondary_stack=parsed_data.get("secondary_stack", []),
            domain=parsed_data.get("domain", []),
            seniority=parsed_data.get("seniority", "mid"),
            keywords=parsed_data.get("keywords", []),
            raw_jd=jd_text
        )
    except Exception as e:
        logger.warning(f"⚠ LLM parsing failed: {type(e).__name__}: {e}. Falling back to regex.")
        return parse_jd_with_regex(jd_text)


def validate_parsed_jd(parsed_jd: ParsedJobDescription) -> bool:
    """
    Validate parsed job description has required fields.
    
    Args:
        parsed_jd: Parsed job description to validate
        
    Returns:
        True if valid, False otherwise
    """
    return (
        len(parsed_jd.core_stack) > 0 or
        len(parsed_jd.secondary_stack) > 0 or
        len(parsed_jd.domain) > 0
    )