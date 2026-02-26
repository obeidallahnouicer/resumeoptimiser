"""Dependency injection providers for FastAPI.

All service-level dependencies are constructed here and injected
into route handlers. No business logic lives here – only wiring.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from app.agents.cv_parser import CVParserAgent
from app.agents.cv_rewriter import CVRewriteAgent
from app.agents.cv_validator import CVValidatorAgent
from app.agents.job_normalizer import JobNormalizerAgent
from app.agents.report_generator import ReportGeneratorAgent
from app.agents.rescorer import RescoreAgent
from app.agents.score_explainer import ScoreExplainerAgent
from app.agents.semantic_matcher import SemanticMatcherAgent
from app.core.config import AppSettings, get_settings
from app.infrastructure.embedding_client import SentenceTransformerEmbeddingClient
from app.infrastructure.llm_client import OpenAILLMClient
from app.services.optimization_service import OptimizationService


@lru_cache(maxsize=1)
def get_llm_client(settings: AppSettings = Depends(get_settings)) -> OpenAILLMClient:
    return OpenAILLMClient(settings.llm)


@lru_cache(maxsize=1)
def get_embedding_client(
    settings: AppSettings = Depends(get_settings),
) -> SentenceTransformerEmbeddingClient:
    return SentenceTransformerEmbeddingClient(settings.embedding)


def get_optimization_service(
    settings: AppSettings = Depends(get_settings),
) -> OptimizationService:
    """Build the full agent pipeline and return an OptimizationService."""
    llm = OpenAILLMClient(settings.llm)
    embedder = SentenceTransformerEmbeddingClient(settings.embedding)

    matcher = SemanticMatcherAgent(embedding_client=embedder)

    return OptimizationService(
        cv_parser=CVParserAgent(llm=llm),
        job_normalizer=JobNormalizerAgent(llm=llm),
        matcher=matcher,
        explainer=ScoreExplainerAgent(llm=llm),
        rewriter=CVRewriteAgent(llm=llm),
        validator=CVValidatorAgent(),
        rescorer=RescoreAgent(matcher=matcher),
        report_generator=ReportGeneratorAgent(llm=llm),
    )
