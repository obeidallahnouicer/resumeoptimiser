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

Markdown-safe pipeline (parallel, independently callable):
  A. OCRToMarkdownAgent        → MarkdownOutput  (original_cv.md)
  B. MarkdownRewriteAgent      → MarkdownRewriteOutput  (improved_cv.md)
  C. MarkdownDiffService       → MarkdownDiffOutput  (diff)
  D. MarkdownPDFRenderer       → PDF bytes
"""

from __future__ import annotations

from app.agents.cv_parser import CVParserAgent
from app.agents.cv_rewriter import CVRewriteAgent
from app.agents.cv_validator import CVValidatorAgent, CVValidatorInput
from app.agents.ideal_profile_agent import IdealProfileAgent
from app.agents.cv_rewrite_stage1_agent import CVRewriteStage1Agent
from app.agents.cv_rewrite_stage2_agent import CVRewriteStage2Agent
from app.agents.job_normalizer import JobNormalizerAgent
from app.agents.llm_match_analyzer import LLMMatchAnalyzerAgent
from app.agents.markdown_rewriter import MarkdownRewriteAgent
from app.agents.ocr_to_markdown import OCRToMarkdownAgent
from app.agents.report_generator import ReportGeneratorAgent, ReportGeneratorInput
from app.agents.rescorer import RescoreAgent, RescoreInput
from app.agents.score_explainer import ScoreExplainerAgent
from app.agents.semantic_matcher import SemanticMatcherAgent
from app.core.exceptions import AgentExecutionError, ValidationError
from app.core.logging import get_logger
from app.schemas.cv import CVParserInput, StructuredCVSchema
from app.schemas.job import JobNormalizerInput
from app.schemas.markdown import (
    MarkdownInput,
    MarkdownOutput,
    MarkdownRewriteInput,
    MarkdownRewriteOutput,
)
from app.schemas.pipeline import ComparisonReportSchema
from app.schemas.report import (
    CVRewriteInput,
    CVRewriteStage1Input,
    CVRewriteStage2Input,
    IdealProfileInput,
    ScoreExplainerInput,
)
from app.schemas.scoring import SemanticMatcherInput, SimilarityScoreSchema
from app.services.cv_to_markdown import structured_cv_to_markdown

logger = get_logger(__name__)

# Blend weights: how much each scoring method contributes to the final overall
_EMBEDDING_WEIGHT = 0.35
_LLM_WEIGHT = 0.65


class OptimizationService:
    """Orchestrates the full CV optimisation pipeline.

    New pipeline (with ideal profile and two-stage rewrite):
      1. parseCV
      2. normalizeJob
      3. generateIdealProfile (new)
      4. score (embedding + LLM)
      5. explain (LLM)
      6. rewriteStage1 (LLM, language transformation)
      7. rewriteStage2 (LLM, gap closing)
      8. validate (rules)
      9. rescore (embedding)
      10. generateReport (LLM)
    """

    def __init__(
        self,
        cv_parser: CVParserAgent,
        job_normalizer: JobNormalizerAgent,
        ideal_profile_agent: IdealProfileAgent,
        matcher: SemanticMatcherAgent,
        llm_match_analyzer: LLMMatchAnalyzerAgent,
        explainer: ScoreExplainerAgent,
        rewriter_stage1: CVRewriteStage1Agent,
        rewriter_stage2: CVRewriteStage2Agent,
        validator: CVValidatorAgent,
        rescorer: RescoreAgent,
        report_generator: ReportGeneratorAgent,
        ocr_to_markdown: OCRToMarkdownAgent,
        markdown_rewriter: MarkdownRewriteAgent,
    ) -> None:
        self._cv_parser = cv_parser
        self._job_normalizer = job_normalizer
        self._ideal_profile_agent = ideal_profile_agent
        self._matcher = matcher
        self._llm_match_analyzer = llm_match_analyzer
        self._explainer = explainer
        self._rewriter_stage1 = rewriter_stage1
        self._rewriter_stage2 = rewriter_stage2
        self._validator = validator
        self._rescorer = rescorer
        self._report_generator = report_generator
        self._ocr_to_markdown_agent = ocr_to_markdown
        self._markdown_rewriter = markdown_rewriter

    def run(self, cv_text: str, job_text: str) -> ComparisonReportSchema:
        """Execute the full pipeline end-to-end.

        Pipeline flow:
          1. Parse CV and Job (parallel Wave 1)
          2. Generate Ideal Profile from Job
          3. Score CV against Job (embedding + LLM)
          4. Explain gaps (LLM)
          5. Rewrite Stage 1 – language transformation using ideal profile
          6. Rewrite Stage 2 – gap closing
          7. Validate rewritten CV
          8. Rescore improved CV
          9. Generate final report
        """
        logger.info("pipeline.start")

        # Wave 1: Parse CV and Job in parallel
        structured_cv = self._parse_cv(cv_text)
        structured_job = self._parse_job(job_text)

        # Generate ideal profile (guides the rewrite stages)
        ideal_profile = self._generate_ideal_profile(structured_job)

        # Score original CV
        original_score = self._score(structured_cv, structured_job)

        # Explain gaps
        explanation = self._explain(structured_cv, structured_job, original_score)

        # Two-stage rewrite
        rewritten_stage1 = self._rewrite_stage1(structured_cv, ideal_profile)
        optimized_cv = self._rewrite_stage2(rewritten_stage1, explanation)

        # Validate and rescore
        self._validate(structured_cv, optimized_cv)
        optimized_as_structured = self._optimized_to_structured(optimized_cv, structured_cv)
        improved_score = self._rescore(
            structured_cv, optimized_as_structured, structured_job, original_score
        )

        # Generate final report
        report = self._generate_report(improved_score, explanation, optimized_cv, ideal_profile)

        logger.info("pipeline.complete", delta=improved_score.delta)
        return report

    # ------------------------------------------------------------------
    # Private step wrappers
    # ------------------------------------------------------------------

    def _parse_cv(self, cv_text: str):
        return self._cv_parser.execute(CVParserInput(raw_text=cv_text))

    def _parse_job(self, job_text: str):
        return self._job_normalizer.execute(JobNormalizerInput(raw_text=job_text))

    def _generate_ideal_profile(self, job):
        """Generate ideal candidate profile from structured job."""
        return self._ideal_profile_agent.execute(IdealProfileInput(job=job))

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

    def _rewrite_stage1(self, cv, ideal_profile):
        """Rewrite CV using ideal profile vocabulary (language transformation)."""
        return self._rewriter_stage1.execute(CVRewriteStage1Input(cv=cv, ideal_profile=ideal_profile))

    def _rewrite_stage2(self, cv_rewrite_stage1, explanation):
        """Refine rewritten CV by addressing gaps (gap closing)."""
        return self._rewriter_stage2.execute(CVRewriteStage2Input(cv_rewrite_stage1=cv_rewrite_stage1, comparison_report=explanation))

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

    def _generate_report(self, improved_score, explanation, optimized_cv, ideal_profile):
        return self._report_generator.execute(
            ReportGeneratorInput(
                improved_score=improved_score,
                explanation=explanation,
                optimized_cv=optimized_cv,
                ideal_profile=ideal_profile,
            )
        )

    # ------------------------------------------------------------------
    # Markdown-safe pipeline steps (independently callable)
    # ------------------------------------------------------------------

    def structured_cv_to_markdown(self, cv: StructuredCVSchema) -> MarkdownOutput:
        """Deterministic: convert an already-parsed StructuredCVSchema → Markdown.

        This is the CORRECT way to produce original_cv.md.
        No LLM, no OCR — pure structural rendering. Preserves all content exactly.
        """
        markdown = structured_cv_to_markdown(cv)
        return MarkdownOutput(markdown=markdown)

    def ocr_to_markdown(self, input: MarkdownInput) -> MarkdownOutput:  # noqa: A002
        """Step A – Convert raw OCR/PDF text to clean structured Markdown via LLM.

        Prefer calling structured_cv_to_markdown() when a StructuredCVSchema is
        available (after the parse stage) — it is deterministic and more reliable.
        This LLM path is a fallback for raw text without prior parsing.
        """
        return self._ocr_to_markdown_agent.execute(input)

    def rewrite_markdown(self, input: MarkdownRewriteInput) -> MarkdownRewriteOutput:  # noqa: A002
        """Step B – Improve CV wording while preserving Markdown structure.

        Input:  original_cv.md + job context + optional gap analysis.
        Output: improved_cv.md (same structure, better wording) + changes_summary.
        """
        return self._markdown_rewriter.execute(input)
