"""Tests for prompt caching service."""

from __future__ import annotations

import pytest

from app.infrastructure.cache import CacheManager
from app.services.prompt_cache_service import PromptCacheService


@pytest.fixture
def cache_manager() -> CacheManager:
    """Create a fresh cache manager for each test."""
    return CacheManager(default_ttl=3600.0)


@pytest.fixture
def prompt_cache(cache_manager: CacheManager) -> PromptCacheService:
    """Create a fresh prompt cache service for each test."""
    return PromptCacheService(cache_manager, ttl_seconds=3600.0)


class TestPromptCacheService:
    """Test PromptCacheService behavior."""

    def test_get_or_set_first_call_misses(self, prompt_cache: PromptCacheService) -> None:
        """First call should miss cache and return the prompt."""
        prompt = "This is a test prompt"
        result = prompt_cache.get_or_set("test_agent", "1.0", prompt)

        assert result == prompt

    def test_get_or_set_second_call_hits(self, prompt_cache: PromptCacheService) -> None:
        """Second call with same agent/version should hit cache."""
        prompt = "This is a test prompt"
        first_result = prompt_cache.get_or_set("test_agent", "1.0", prompt)
        second_result = prompt_cache.get_or_set("test_agent", "1.0", prompt)

        assert first_result == second_result == prompt

    def test_get_returns_none_when_not_cached(self, prompt_cache: PromptCacheService) -> None:
        """get() should return None when key not in cache."""
        result = prompt_cache.get("nonexistent_agent", "1.0")
        assert result is None

    def test_get_returns_cached_value(self, prompt_cache: PromptCacheService) -> None:
        """get() should return value after set()."""
        prompt = "Cached prompt"
        prompt_cache.set("my_agent", "2.0", prompt)
        result = prompt_cache.get("my_agent", "2.0")

        assert result == prompt

    def test_different_versions_separate_cache(self, prompt_cache: PromptCacheService) -> None:
        """Different versions should have separate cache entries."""
        prompt_v1 = "Prompt version 1"
        prompt_v2 = "Prompt version 2"

        prompt_cache.set("agent", "1.0", prompt_v1)
        prompt_cache.set("agent", "2.0", prompt_v2)

        assert prompt_cache.get("agent", "1.0") == prompt_v1
        assert prompt_cache.get("agent", "2.0") == prompt_v2

    def test_different_agents_separate_cache(self, prompt_cache: PromptCacheService) -> None:
        """Different agents should have separate cache entries."""
        prompt_a = "Agent A prompt"
        prompt_b = "Agent B prompt"

        prompt_cache.set("agent_a", "1.0", prompt_a)
        prompt_cache.set("agent_b", "1.0", prompt_b)

        assert prompt_cache.get("agent_a", "1.0") == prompt_a
        assert prompt_cache.get("agent_b", "1.0") == prompt_b

    def test_get_or_set_uses_provided_prompt_for_miss(self, prompt_cache: PromptCacheService) -> None:
        """get_or_set() should store the provided prompt on miss."""
        prompt = "New prompt to cache"
        result = prompt_cache.get_or_set("new_agent", "1.0", prompt)

        # Verify it was stored
        cached = prompt_cache.get("new_agent", "1.0")
        assert cached == prompt
        assert result == prompt

    def test_get_or_set_ignores_provided_prompt_on_hit(self, prompt_cache: PromptCacheService) -> None:
        """get_or_set() should return cached value even if different prompt provided."""
        original_prompt = "Original prompt"
        different_prompt = "Different prompt"

        prompt_cache.set("agent", "1.0", original_prompt)

        # Call with a different prompt
        result = prompt_cache.get_or_set("agent", "1.0", different_prompt)

        # Should return the original cached prompt, not the different one
        assert result == original_prompt
