"""OptimizationService – orchestrates the full 9-step pipeline.

This is the ONLY place where agents are wired together.
No business logic in the API layer – the API calls this service.

Pipeline:
  1. CVParserAgent             → StructuredCVSchema
  2. JobNormalizerAgent        → StructuredJobSchema
  3. SemanticMatcherAgent      → SimilarityScoreSchema  (embeddings only)
  4. LLMMatchAnalyzerAgent     → LLMMatchAnalysisSchema  (LLM deep analysis)
  ── Blend embedding + LLM scores ──
  5. ScoreExplainerAgent       → ExplanationReportSchema (LLM)
  6. CVRewriteAgent            → OptimizedCVSchema       (LLM)
  7. CVValidatorAgent          → CVValidatorOutput       (rules only)
  8. RescoreAgent              → ImprovedScoreSchema     (embeddings only)
  9. ReportGeneratorAgent      → ComparisonReportSchema  (LLM)
"""

from __future__ import annotations

from app.agents.cv_parser import CVParserAgent
from app.agents.cv_rewriter import CVRewriteAgent
from app.agents.cv_validator import CVValidatorAgent, CVValidatorInput
from app.agents.job_normalizer import JobNormalizerAgent
from app.agents.llm_match_analyzer import LLMMatchAnalyzerAgent
from app.agents.report_generator import ReportGeneratorAgent, ReportGeneratorInput
from app.agents.rescorer import RescoreAgent, RescoreInput
from app.agents.score_explainer import ScoreExplainerAgent
from app.agents.semantic_matcher import SemanticMatcherAgent
from app.core.exceptions import AgentExecutionError, ValidationError
from app.core.logging import get_logger
from app.schemas.cv import CVParserInput, StructuredCVSchema
from app.schemas.job import JobNormalizerInput
from app.schemas.pipeline import ComparisonReportSchema
from app.schemas.report import CVRewriteInput, ScoreExplainerInput
from app.schemas.scoring import SemanticMatcherInput, SimilarityScoreSchema

logger = get_logger(__name__)

# Blend weights: how much each scoring method contributes to the final overall
_EMBEDDING_WEIGHT = 0.35
_LLM_WEIGHT = 0.65


class OptimizationService:
    """Orchestrates the full CV optimisation pipeline."""

    def __init__(
        self,
        cv_parser: CVParserAgent,
        job_normalizer: JobNormalizerAgent,
        matcher: SemanticMatcherAgent,
        llm_match_analyzer: LLMMatchAnalyzerAgent,
        explainer: ScoreExplainerAgent,
        rewriter: CVRewriteAgent,
        validator: CVValidatorAgent,
        rescorer: RescoreAgent,
        report_generator: ReportGeneratorAgent,
    ) -> None:
        self._cv_parser = cv_parser
        self._job_normalizer = job_normalizer
        self._matcher = matcher
        self._llm_match_analyzer = llm_match_analyzer
        self._explainer = explainer
        self._rewriter = rewriter
        self._validator = validator
        self._rescorer = rescorer
        self._report_generator = report_generator

    def run(self, cv_text: str, job_text: str) -> ComparisonReportSchema:
        """Execute the full pipeline end-to-end."""
        logger.info("pipeline.start")

        structured_cv = self._parse_cv(cv_text)
        structured_job = self._parse_job(job_text)
        original_score = self._score(structured_cv, structured_job)
        explanation = self._explain(structured_cv, structured_job, original_score)
        optimized_cv = self._rewrite(structured_cv, structured_job, explanation)
        self._validate(structured_cv, optimized_cv)
        optimized_as_structured = self._optimized_to_structured(optimized_cv, structured_cv)
        improved_score = self._rescore(structured_cv, optimized_as_structured, structured_job, original_score)
        report = self._generate_report(improved_score, explanation, optimized_cv)

        logger.info("pipeline.complete", delta=improved_score.delta)
        return report

    # ------------------------------------------------------------------
    # Private step wrappers
    # ------------------------------------------------------------------

    def _parse_cv(self, cv_text: str):
        return self._cv_parser.execute(CVParserInput(raw_text=cv_text))

    def _parse_job(self, job_text: str):
        return self._job_normalizer.execute(JobNormalizerInput(raw_text=job_text))

    def _score(self, cv, job) -> SimilarityScoreSchema:
        """Run embedding matcher + LLM match analyzer, then blend."""
        matcher_input = SemanticMatcherInput(cv=cv, job=job)

        # Step 3: embedding-based similarity
        embedding_result = self._matcher.execute(matcher_input)

        # Step 4: LLM deep analysis (graceful fallback on error)
        try:
            llm_analysis = self._llm_match_analyzer.execute(matcher_input)
        except Exception as exc:
            logger.warning("llm_match_analyzer.fallback", error=str(exc))
            llm_analysis = None

        # Blend scores
        if llm_analysis:
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

        # Fallback: embedding only
        return embedding_result

    def _explain(self, cv, job, score):
        return self._explainer.execute(ScoreExplainerInput(cv=cv, job=job, score=score))

    def _rewrite(self, cv, job, explanation):
        return self._rewriter.execute(CVRewriteInput(cv=cv, job=job, explanation=explanation))

    def _validate(self, original_cv, optimized_cv):
        result = self._validator.execute(CVValidatorInput(original=original_cv, optimized=optimized_cv))
        if not result.is_valid:
            raise ValidationError(f"Optimised CV failed validation: {result.violations}")

    def _optimized_to_structured(self, optimized_cv, original_cv: StructuredCVSchema) -> StructuredCVSchema:
        """Promote OptimizedCVSchema back to StructuredCVSchema for re-scoring."""
        return StructuredCVSchema(
            contact=optimized_cv.contact,
            sections=optimized_cv.sections,
            raw_text=original_cv.raw_text,
        )

    def _rescore(self, original_cv, optimized_structured, job, original_score):
        return self._rescorer.execute(
            RescoreInput(
                original_cv=original_cv,
                optimized_cv=optimized_structured,
                job=job,
                original_score=original_score,
            )
        )

    def _generate_report(self, improved_score, explanation, optimized_cv):
        return self._report_generator.execute(
            ReportGeneratorInput(
                improved_score=improved_score,
                explanation=explanation,
                optimized_cv=optimized_cv,
            )
        )
