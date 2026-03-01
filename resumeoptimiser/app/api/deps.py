"""Dependency injection providers for FastAPI.

All service-level dependencies are constructed here and injected
into route handlers. No business logic lives here – only wiring.

The LLM client and embedding client are module-level singletons so that
the SentenceTransformer model is loaded exactly once at startup and reused
across every request, avoiding the meta-tensor error caused by concurrent
model initialisation.
"""

from __future__ import annotations

from app.agents.cv_parser import CVParserAgent
from app.agents.cv_rewriter import CVRewriteAgent
from app.agents.cv_validator import CVValidatorAgent
from app.agents.job_normalizer import JobNormalizerAgent
from app.agents.llm_match_analyzer import LLMMatchAnalyzerAgent
from app.agents.report_generator import ReportGeneratorAgent
from app.agents.rescorer import RescoreAgent
from app.agents.score_explainer import ScoreExplainerAgent
from app.agents.semantic_matcher import SemanticMatcherAgent
from app.core.config import AppSettings, get_settings
from app.infrastructure.embedding_client import SentenceTransformerEmbeddingClient
from app.infrastructure.llm_client import OpenAILLMClient
from app.services.optimization_service import OptimizationService

# ---------------------------------------------------------------------------
# Module-level singletons – created once when the module is first imported
# (i.e. at server startup) and reused for the lifetime of the process.
# ---------------------------------------------------------------------------

_settings = get_settings()
_llm_client = OpenAILLMClient(_settings.llm)
_embedding_client = SentenceTransformerEmbeddingClient(_settings.embedding)

_matcher_agent = SemanticMatcherAgent(embedding_client=_embedding_client)
_llm_match_analyzer = LLMMatchAnalyzerAgent(llm=_llm_client)
_rescorer_agent = RescoreAgent(matcher=_matcher_agent, llm_match_analyzer=_llm_match_analyzer)

_optimization_service = OptimizationService(
    cv_parser=CVParserAgent(llm=_llm_client),
    job_normalizer=JobNormalizerAgent(llm=_llm_client),
    matcher=_matcher_agent,
    llm_match_analyzer=_llm_match_analyzer,
    explainer=ScoreExplainerAgent(llm=_llm_client),
    rewriter=CVRewriteAgent(llm=_llm_client),
    validator=CVValidatorAgent(),
    rescorer=_rescorer_agent,
    report_generator=ReportGeneratorAgent(llm=_llm_client),
)


# ---------------------------------------------------------------------------
# FastAPI dependency functions – return the singletons
# ---------------------------------------------------------------------------


def get_optimization_service() -> OptimizationService:
    """Return the shared OptimizationService singleton."""
    return _optimization_service
