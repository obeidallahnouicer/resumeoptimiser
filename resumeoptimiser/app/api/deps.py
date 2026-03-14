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
from app.agents.markdown_rewriter import MarkdownRewriteAgent
from app.agents.ocr_to_markdown import OCRToMarkdownAgent
from app.agents.report_generator import ReportGeneratorAgent
from app.agents.rescorer import RescoreAgent
from app.agents.score_explainer import ScoreExplainerAgent
from app.agents.semantic_matcher import SemanticMatcherAgent
from app.core.config import AppSettings, get_settings
from app.infrastructure.cache import CacheManager
from app.infrastructure.embedding_client import SentenceTransformerEmbeddingClient
from app.infrastructure.llm_client import RotatingLLMClient
from app.services.cv_cache_service import CVCacheService
from app.services.optimization_service import OptimizationService
from app.services.prompt_cache_service import PromptCacheService

# ---------------------------------------------------------------------------
# Module-level singletons – created once when the module is first imported
# (i.e. at server startup) and reused for the lifetime of the process.
# ---------------------------------------------------------------------------

_settings = get_settings()
_provider_configs = _settings.llm.provider_configs()
if not _provider_configs:
    raise RuntimeError(
        "No LLM providers configured. Set LLM_OPENROUTER_API_KEY or LLM_API_KEY/LLM_NVIDIA_API_KEY."
    )

_llm_client = RotatingLLMClient(_provider_configs)
_embedding_client = SentenceTransformerEmbeddingClient(_settings.embedding)

# Cache layer singletons
_cache_manager = CacheManager(default_ttl=_settings.cache.ttl_seconds)
_prompt_cache_service = PromptCacheService(_cache_manager, ttl_seconds=_settings.cache.ttl_seconds)
_cv_cache_service = CVCacheService(_cache_manager, ttl_seconds=_settings.cache.ttl_seconds)

_matcher_agent = SemanticMatcherAgent(embedding_client=_embedding_client)
_llm_match_analyzer = LLMMatchAnalyzerAgent(llm=_llm_client)
_rescorer_agent = RescoreAgent(matcher=_matcher_agent, llm_match_analyzer=_llm_match_analyzer)

_optimization_service = OptimizationService(
    cv_parser=CVParserAgent(llm=_llm_client, cv_cache=_cv_cache_service),
    job_normalizer=JobNormalizerAgent(llm=_llm_client, prompt_cache=_prompt_cache_service),
    matcher=_matcher_agent,
    llm_match_analyzer=_llm_match_analyzer,
    explainer=ScoreExplainerAgent(llm=_llm_client, prompt_cache=_prompt_cache_service),
    rewriter=CVRewriteAgent(llm=_llm_client, prompt_cache=_prompt_cache_service),
    validator=CVValidatorAgent(),
    rescorer=_rescorer_agent,
    report_generator=ReportGeneratorAgent(llm=_llm_client, prompt_cache=_prompt_cache_service),
    # Markdown-safe pipeline agents
    ocr_to_markdown=OCRToMarkdownAgent(llm=_llm_client, cv_cache=_cv_cache_service),
    markdown_rewriter=MarkdownRewriteAgent(llm=_llm_client, prompt_cache=_prompt_cache_service),
)


# ---------------------------------------------------------------------------
# FastAPI dependency functions – return the singletons
# ---------------------------------------------------------------------------


def get_optimization_service() -> OptimizationService:
    """Return the shared OptimizationService singleton."""
    return _optimization_service
