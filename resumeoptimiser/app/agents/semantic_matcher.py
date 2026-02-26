"""SemanticMatcherAgent – computes deterministic cosine similarity scores.

Constraint: NO LLM usage. Similarity is purely embedding-based.

Algorithm:
1. Build a single text representation of the job (title + skills + responsibilities).
2. For each CV section, embed the section text.
3. Embed the job representation once.
4. Cosine similarity between each section vector and the job vector.
5. Weighted average → overall score.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError, SimilarityError
from app.core.logging import get_logger
from app.infrastructure.embedding_client import EmbeddingClientProtocol
from app.schemas.cv import StructuredCVSchema
from app.schemas.job import StructuredJobSchema
from app.schemas.scoring import (
    SemanticMatcherInput,
    SectionScoreSchema,
    SimilarityScoreSchema,
)

logger = get_logger(__name__)

# Weight each section type for the overall score
_SECTION_WEIGHTS: dict[str, float] = {
    "experience": 0.40,
    "skills": 0.30,
    "education": 0.15,
    "summary": 0.10,
    "other": 0.05,
}
_DEFAULT_WEIGHT = 0.05


class SemanticMatcherAgent(BaseAgent[SemanticMatcherInput, SimilarityScoreSchema]):
    """Scores CV ↔ Job similarity using embeddings only (no LLM)."""

    meta = AgentMeta(name="SemanticMatcherAgent", version="1.0.0")

    def __init__(self, embedding_client: EmbeddingClientProtocol) -> None:
        self._embedder = embedding_client

    def execute(self, input: SemanticMatcherInput) -> SimilarityScoreSchema:  # noqa: A002
        """Compute section-level and overall cosine similarity scores."""
        logger.info("semantic_matcher.start")
        try:
            job_vector = self._embed_job(input.job)
            section_scores = self._score_sections(input.cv, job_vector)
            overall = self._compute_overall(section_scores)
        except SimilarityError:
            raise
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, str(exc)) from exc

        logger.info("semantic_matcher.success", overall=overall)
        return SimilarityScoreSchema(overall=overall, section_scores=section_scores)

    def _embed_job(self, job: StructuredJobSchema) -> NDArray[np.float32]:
        """Build a single job text and embed it."""
        skills_text = " ".join(s.skill for s in job.required_skills)
        responsibilities_text = " ".join(job.responsibilities)
        job_text = f"{job.title} {skills_text} {responsibilities_text}".strip()
        if not job_text:
            raise SimilarityError("Job description produced empty embedding text.")
        return self._embedder.embed(job_text)

    def _score_sections(
        self,
        cv: StructuredCVSchema,
        job_vector: NDArray[np.float32],
    ) -> list[SectionScoreSchema]:
        """Embed each CV section and compute its cosine score vs the job."""
        scores: list[SectionScoreSchema] = []
        for section in cv.sections:
            if not section.raw_text.strip():
                continue
            section_vector = self._embedder.embed(section.raw_text)
            score = float(np.dot(section_vector, job_vector))
            scores.append(SectionScoreSchema(section_type=section.section_type, score=score))
        return scores

    def _compute_overall(self, section_scores: list[SectionScoreSchema]) -> float:
        """Compute a weighted average of section scores."""
        if not section_scores:
            return 0.0
        total_weight = 0.0
        weighted_sum = 0.0
        for s in section_scores:
            w = _SECTION_WEIGHTS.get(s.section_type.value, _DEFAULT_WEIGHT)
            weighted_sum += s.score * w
            total_weight += w
        return weighted_sum / total_weight if total_weight > 0 else 0.0
