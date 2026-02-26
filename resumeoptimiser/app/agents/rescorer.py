"""RescoreAgent – re-runs SemanticMatcherAgent on the optimised CV.

Wraps SemanticMatcherAgent and builds an ImprovedScoreSchema comparing
the before and after scores.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import AgentMeta, BaseAgent
from app.agents.semantic_matcher import SemanticMatcherAgent
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.schemas.cv import StructuredCVSchema
from app.schemas.job import StructuredJobSchema
from app.schemas.pipeline import ImprovedScoreSchema
from app.schemas.scoring import SemanticMatcherInput, SimilarityScoreSchema

logger = get_logger(__name__)


@dataclass(frozen=True)
class RescoreInput:
    """Input for RescoreAgent."""

    original_cv: StructuredCVSchema
    optimized_cv: StructuredCVSchema
    job: StructuredJobSchema
    original_score: SimilarityScoreSchema


class RescoreAgent(BaseAgent[RescoreInput, ImprovedScoreSchema]):
    """Re-scores the optimised CV and computes the delta vs the original."""

    meta = AgentMeta(name="RescoreAgent", version="1.0.0")

    def __init__(self, matcher: SemanticMatcherAgent) -> None:
        self._matcher = matcher

    def execute(self, input: RescoreInput) -> ImprovedScoreSchema:  # noqa: A002
        """Compute new score for the optimised CV and return the delta."""
        logger.info("rescore.start", before=input.original_score.overall)

        new_score = self._score_optimized(input)
        delta = round(new_score.overall - input.original_score.overall, 4)

        logger.info("rescore.success", after=new_score.overall, delta=delta)
        return ImprovedScoreSchema(
            before=input.original_score,
            after=new_score,
            delta=delta,
        )

    def _score_optimized(self, input: RescoreInput) -> SimilarityScoreSchema:  # noqa: A002
        """Convert OptimizedCV to StructuredCV format and re-score."""
        try:
            return self._matcher.execute(
                SemanticMatcherInput(cv=input.optimized_cv, job=input.job)
            )
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, str(exc)) from exc
