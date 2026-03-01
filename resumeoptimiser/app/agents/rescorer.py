"""RescoreAgent – re-runs SemanticMatcherAgent on the optimised CV.

Wraps SemanticMatcherAgent (+ optional LLMMatchAnalyzerAgent) and builds
an ImprovedScoreSchema comparing the before and after scores.
The LLM analysis on the optimised CV gives a fair "after" picture.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.base import AgentMeta, BaseAgent
from app.agents.semantic_matcher import SemanticMatcherAgent
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.schemas.cv import StructuredCVSchema
from app.schemas.job import StructuredJobSchema
from app.schemas.pipeline import ImprovedScoreSchema
from app.schemas.scoring import SemanticMatcherInput, SimilarityScoreSchema

logger = get_logger(__name__)

# Blend weights — same as OptimizationService
_EMBEDDING_WEIGHT = 0.35
_LLM_WEIGHT = 0.65


@dataclass(frozen=True)
class RescoreInput:
    """Input for RescoreAgent."""

    original_cv: StructuredCVSchema
    optimized_cv: StructuredCVSchema
    job: StructuredJobSchema
    original_score: SimilarityScoreSchema


class RescoreAgent(BaseAgent[RescoreInput, ImprovedScoreSchema]):
    """Re-scores the optimised CV and computes the delta vs the original."""

    meta = AgentMeta(name="RescoreAgent", version="2.0.0")

    def __init__(self, matcher: SemanticMatcherAgent, llm_match_analyzer=None) -> None:
        self._matcher = matcher
        self._llm_analyzer = llm_match_analyzer  # optional, injected if available

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
        """Re-score the optimized CV with embeddings + optional LLM analysis."""
        matcher_input = SemanticMatcherInput(cv=input.optimized_cv, job=input.job)
        try:
            embedding_result = self._matcher.execute(matcher_input)
        except Exception as exc:
            raise AgentExecutionError(self.meta.name, str(exc)) from exc

        # Run LLM analysis on optimized CV if analyzer is available
        if self._llm_analyzer is not None:
            try:
                llm_analysis = self._llm_analyzer.execute(matcher_input)
                blended = (
                    _EMBEDDING_WEIGHT * embedding_result.overall
                    + _LLM_WEIGHT * llm_analysis.overall_llm_score
                )
                return SimilarityScoreSchema(
                    overall=round(blended, 4),
                    section_scores=embedding_result.section_scores,
                    llm_analysis=llm_analysis,
                    embedding_score=embedding_result.overall,
                )
            except Exception as exc:
                logger.warning("rescore.llm_fallback", error=str(exc))

        return embedding_result
