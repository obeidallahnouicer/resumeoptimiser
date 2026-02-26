"""ReportGeneratorAgent – compiles the full pipeline output into a narrative.

Uses the LLM to produce a short, human-readable narrative.
All data is already structured; the LLM only writes prose.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.agents.base import AgentMeta, BaseAgent
from app.core.exceptions import AgentExecutionError
from app.core.logging import get_logger
from app.infrastructure.llm_client import LLMClientProtocol
from app.schemas.pipeline import ComparisonReportSchema, ImprovedScoreSchema
from app.schemas.report import ExplanationReportSchema, OptimizedCVSchema

logger = get_logger(__name__)

_SYSTEM_PROMPT = """
You are a concise technical writer. Summarise the CV optimisation results in
2-3 sentences for the candidate.  Be specific about improvements made and
remaining gaps. Be encouraging but honest.  Return plain text, no markdown.
""".strip()


@dataclass(frozen=True)
class ReportGeneratorInput:
    """Input for ReportGeneratorAgent."""

    improved_score: ImprovedScoreSchema
    explanation: ExplanationReportSchema
    optimized_cv: OptimizedCVSchema


class ReportGeneratorAgent(BaseAgent[ReportGeneratorInput, ComparisonReportSchema]):
    """Assembles the final ComparisonReportSchema with an LLM-written narrative."""

    meta = AgentMeta(name="ReportGeneratorAgent", version="1.0.0")

    def __init__(self, llm: LLMClientProtocol) -> None:
        self._llm = llm

    def execute(self, input: ReportGeneratorInput) -> ComparisonReportSchema:  # noqa: A002
        """Build and return the final comparison report."""
        logger.info("report_generator.start")

        narrative = self._generate_narrative(input)

        logger.info("report_generator.success")
        return ComparisonReportSchema(
            improved_score=input.improved_score,
            explanation=input.explanation,
            optimized_cv=input.optimized_cv,
            narrative=narrative,
        )

    def _generate_narrative(self, input: ReportGeneratorInput) -> str:  # noqa: A002
        """Ask the LLM to write a brief narrative about the optimisation."""
        user_prompt = self._build_prompt(input)
        try:
            return self._llm.complete(system=_SYSTEM_PROMPT, user=user_prompt)
        except Exception as exc:
            logger.warning("report_generator.narrative_failed", error=str(exc))
            # Narrative is non-critical – fall back to empty string
            return ""

    def _build_prompt(self, input: ReportGeneratorInput) -> str:  # noqa: A002
        """Construct a concise prompt summarising the pipeline results."""
        changes = "; ".join(input.optimized_cv.changes_summary[:5])
        return (
            f"Score before: {input.improved_score.before.overall:.0%}\n"
            f"Score after:  {input.improved_score.after.overall:.0%}\n"
            f"Delta: +{input.improved_score.delta:.0%}\n"
            f"Gaps addressed: {len(input.explanation.mismatches)}\n"
            f"Changes made: {changes or 'None listed'}"
        )
