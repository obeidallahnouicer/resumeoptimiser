"""SemanticMatcherAgent – computes deterministic cosine similarity scores.

Constraint: NO LLM usage. Similarity is purely embedding-based.

Algorithm (v2 – enriched fields):
1. Build rich text from job: title + hard_skills + soft_skills + tools + responsibilities.
2. Build rich text from CV: per section (as before) PLUS an enriched "skills blob"
   that concatenates hard_skills + soft_skills + tools for a dedicated skills embedding.
3. Cosine similarity per section + enriched skills embedding.
4. Weighted average → overall embedding score.
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
    "experience": 0.30,
    "skills": 0.30,
    "education": 0.15,
    "summary": 0.10,
    "certifications": 0.05,
    "languages": 0.05,
    "other": 0.05,
}
_DEFAULT_WEIGHT = 0.05


class SemanticMatcherAgent(BaseAgent[SemanticMatcherInput, SimilarityScoreSchema]):
    """Scores CV ↔ Job similarity using embeddings only (no LLM)."""

    meta = AgentMeta(name="SemanticMatcherAgent", version="2.0.0")

    def __init__(self, embedding_client: EmbeddingClientProtocol) -> None:
        self._embedder = embedding_client

    def execute(self, input: SemanticMatcherInput) -> SimilarityScoreSchema:  # noqa: A002
        """Compute section-level and overall cosine similarity scores."""
        logger.info("semantic_matcher.start")
        try:
            job_vector = self._embed_job(input.job)
            section_scores = self._score_sections(input.cv, job_vector)

            # Only inject the enriched skills blob when no skills section was
            # produced from CV sections (avoids duplicate "skills" entries).
            has_skills_section = any(
                s.section_type.value == "skills" for s in section_scores
            )
            if not has_skills_section:
                skills_score = self._skills_embedding_score(input.cv, input.job)
                if skills_score is not None:
                    section_scores.append(
                        SectionScoreSchema(section_type="skills", score=skills_score)
                    )

            overall = self._compute_overall(section_scores)
        except SimilarityError:
            raise
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, str(exc)) from exc

        logger.info("semantic_matcher.success", overall=overall)
        return SimilarityScoreSchema(
            overall=overall,
            section_scores=section_scores,
            embedding_score=overall,
        )

    def _embed_job(self, job: StructuredJobSchema) -> NDArray[np.float32]:
        """Build a rich job text using ALL enriched fields and embed it."""
        parts = [job.title]
        parts.extend(s.skill for s in job.required_skills)
        parts.extend(job.hard_skills)
        parts.extend(job.soft_skills)
        parts.extend(job.tools)
        parts.extend(job.responsibilities)
        parts.extend(job.methodologies)
        if job.domain:
            parts.append(job.domain)
        job_text = " ".join(p for p in parts if p).strip()
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

    def _skills_embedding_score(
        self,
        cv: StructuredCVSchema,
        job: StructuredJobSchema,
    ) -> float | None:
        """Compute a dedicated skills cosine similarity using enriched fields."""
        cv_skills_text = " ".join(
            cv.hard_skills + cv.soft_skills + cv.tools
        ).strip()
        job_skills_text = " ".join(
            job.hard_skills + job.soft_skills + job.tools
        ).strip()
        if not cv_skills_text or not job_skills_text:
            return None
        cv_vec = self._embedder.embed(cv_skills_text)
        job_vec = self._embedder.embed(job_skills_text)
        return float(np.dot(cv_vec, job_vec))

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
