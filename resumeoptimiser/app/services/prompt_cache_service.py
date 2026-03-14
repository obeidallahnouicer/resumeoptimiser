"""System prompt caching service.

Manages the lifecycle of system prompts for LLM agents.
Uses deterministic keys: 'system_prompt:{prompt_version}'

Key benefit: System prompts are static and expensive to send.
By caching them, we avoid re-sending the same system prompt
on every LLM call, reducing token usage and latency.

Example usage:
    cache = PromptCacheService(cache_manager, ttl=3600)
    prompt = cache.get_or_set("job_normalizer", "2.0", job_normalizer_system_prompt)
    # First call: stores in cache, returns the prompt
    # Subsequent calls: returns from cache (CACHE_HIT logged)
"""

from __future__ import annotations

from app.core.logging import get_logger
from app.infrastructure.cache import CacheManager

logger = get_logger(__name__)


class PromptCacheService:
    """Manages caching and retrieval of system prompts for LLM agents."""

    def __init__(self, cache: CacheManager, ttl_seconds: float = 3600.0) -> None:
        """Initialize the prompt cache service.

        Args:
            cache: CacheManager instance (typically a singleton)
            ttl_seconds: Default TTL for cached prompts
        """
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    def _build_key(self, agent_name: str, version: str) -> str:
        """Build a deterministic cache key for a prompt.

        Args:
            agent_name: Name of the agent (e.g. 'job_normalizer')
            version: Version string (e.g. '2.0')

        Returns:
            Cache key like 'system_prompt:job_normalizer:2.0'
        """
        return f"system_prompt:{agent_name}:{version}"

    def get(self, agent_name: str, version: str) -> str | None:
        """Retrieve a cached system prompt.

        Args:
            agent_name: Name of the agent
            version: Version string

        Returns:
            The cached prompt if found, None otherwise.
        """
        key = self._build_key(agent_name, version)
        return self._cache.get(key)

    def set(self, agent_name: str, version: str, prompt: str) -> None:
        """Store a system prompt in cache.

        Args:
            agent_name: Name of the agent
            version: Version string
            prompt: The system prompt text
        """
        key = self._build_key(agent_name, version)
        self._cache.set(key, prompt, ttl_seconds=self._ttl_seconds)
        logger.info("prompt_cache.set", key=key)

    def get_or_set(self, agent_name: str, version: str, prompt: str) -> str:
        """Retrieve a prompt from cache or store it if not found.

        Typical usage in an agent:
            system_prompt = self._prompt_cache.get_or_set(
                "job_normalizer", "2.0", JOB_NORMALIZER_SYSTEM_PROMPT
            )

        Args:
            agent_name: Name of the agent
            version: Version string
            prompt: The system prompt text (used if not in cache)

        Returns:
            The cached prompt (or the provided prompt if not cached)
        """
        key = self._build_key(agent_name, version)

        # Check cache first
        cached = self._cache.get(key)
        if cached is not None:
            logger.info("prompt_cache.hit", key=key)
            return cached

        # Not in cache: store and return
        logger.info("prompt_cache.miss", key=key)
        self._cache.set(key, prompt, ttl_seconds=self._ttl_seconds)
        return prompt
