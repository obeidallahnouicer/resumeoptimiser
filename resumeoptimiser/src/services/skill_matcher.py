"""Skill matching service with semantic similarity."""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.models.schemas import SkillMatchResult, SkillMatch, MatchStatus, BaseSkillsData, ParsedJobDescription
from src.core.config import BASE_SKILLS_FILE, MIN_TRANSFERABLE_SIMILARITY, MIN_DIRECT_SIMILARITY, EMBEDDING_MODEL

# Initialize the embedding model
_embedding_model = None

def get_embedding_model():
    """Get or initialize the embedding model (lazy loading)."""
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def load_base_skills(filepath: str = str(BASE_SKILLS_FILE)) -> BaseSkillsData:
    """
    Load and validate base skills JSON.
    
    Args:
        filepath: Path to base_skills.json
        
    Returns:
        Validated BaseSkillsData
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    return BaseSkillsData(**data)


def compute_skill_embeddings(skills_list: List[str]) -> Dict[str, np.ndarray]:
    """
    Compute embeddings for skills using BGE model.
    
    Args:
        skills_list: List of skill names
        
    Returns:
        Dictionary mapping skill names to embedding vectors
    """
    if len(skills_list) == 0:
        return {}
    
    model = get_embedding_model()
    embeddings = model.encode(skills_list, convert_to_numpy=True)
    return {skill: embeddings[i] for i, skill in enumerate(skills_list)}


def cosine_similarity_score(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Similarity score between 0 and 1
    """
    if len(vec1) == 0 or len(vec2) == 0:
        return 0.0
    return float(cosine_similarity([vec1], [vec2])[0][0])


def find_direct_match(skill_name: str, base_skill_names: List[str]) -> bool:
    """Check if skill has direct match in base skills."""
    return any(skill_name.lower() == base.lower() for base in base_skill_names)


def find_transferable_match(
    jd_skill: str,
    skill_embeddings: Dict[str, np.ndarray],
    base_skills: BaseSkillsData
) -> Tuple[Optional[str], float]:
    """
    Find best transferable match for a JD skill.
    
    Args:
        jd_skill: JD requirement skill
        skill_embeddings: Precomputed embeddings
        base_skills: Base skills data
        
    Returns:
        Tuple of (matching skill name, similarity score) or (None, 0.0)
    """
    jd_embedding = skill_embeddings.get(jd_skill, np.array([]))
    best_match = None
    best_similarity = MIN_TRANSFERABLE_SIMILARITY

    for base_skill in base_skills.skills:
        base_embedding = skill_embeddings.get(base_skill.name, np.array([]))
        similarity = cosine_similarity_score(jd_embedding, base_embedding)

        if similarity > best_similarity:
            best_similarity = similarity
            best_match = base_skill.name

    return best_match, best_similarity if best_match else (None, 0.0)


def match_skills(
    base_skills: BaseSkillsData,
    jd_parsed: ParsedJobDescription
) -> SkillMatchResult:
    """
    Match base skills to JD requirements with semantic similarity.
    Returns direct matches, transferable matches, and missing skills.
    
    Args:
        base_skills: User's base skills and experience
        jd_parsed: Parsed job description
        
    Returns:
        SkillMatchResult with match details
    """
    jd_requirements = jd_parsed.core_stack + jd_parsed.secondary_stack
    base_skill_names = [skill.name for skill in base_skills.skills]

    # Compute embeddings
    skill_embeddings = compute_skill_embeddings(base_skill_names + jd_requirements)

    matches: Dict[str, SkillMatch] = {}
    matched_count = 0

    for jd_skill in jd_requirements:
        # Direct match
        if find_direct_match(jd_skill, base_skill_names):
            matched_skill = next(
                (s for s in base_skills.skills if s.name.lower() == jd_skill.lower()),
                None
            )
            if matched_skill:
                matches[jd_skill] = SkillMatch(
                    status=MatchStatus.DIRECT,
                    source=matched_skill.projects[0] if matched_skill.projects else "General",
                    similarity=1.0
                )
                matched_count += 1
                continue

        # Transferable match using embeddings
        best_match, best_similarity = find_transferable_match(jd_skill, skill_embeddings, base_skills)

        if best_match:
            matched_skill = next((s for s in base_skills.skills if s.name == best_match), None)
            matches[jd_skill] = SkillMatch(
                status=MatchStatus.TRANSFERABLE,
                source=matched_skill.projects[0] if matched_skill and matched_skill.projects else "General",
                similarity=best_similarity,
                closest_match=best_match
            )
            matched_count += 1
        else:
            matches[jd_skill] = SkillMatch(
                status=MatchStatus.MISSING,
                similarity=0.0
            )

    unmatched = [
        jd_skill for jd_skill in jd_requirements
        if matches[jd_skill].status == MatchStatus.MISSING
    ]

    return SkillMatchResult(
        matches=matches,
        unmatched_jd_requirements=unmatched,
        total_matched=matched_count,
        total_jd_requirements=len(jd_requirements)
    )