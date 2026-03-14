"""Tests for CV caching service."""

from __future__ import annotations

import pytest

from app.infrastructure.cache import CacheManager
from app.schemas.markdown import MarkdownOutput
from app.services.cv_cache_service import CVCacheService


@pytest.fixture
def cache_manager() -> CacheManager:
    """Create a fresh cache manager for each test."""
    return CacheManager(default_ttl=3600.0)


@pytest.fixture
def cv_cache(cache_manager: CacheManager) -> CVCacheService:
    """Create a fresh CV cache service for each test."""
    return CVCacheService(cache_manager, ttl_seconds=3600.0)


class TestCVCacheService:
    """Test CVCacheService behavior."""

    def test_compute_cv_hash_deterministic(self) -> None:
        """compute_cv_hash should produce the same hash for the same input."""
        text = "This is a CV"
        hash1 = CVCacheService.compute_cv_hash(text)
        hash2 = CVCacheService.compute_cv_hash(text)

        assert hash1 == hash2

    def test_compute_cv_hash_different_for_different_text(self) -> None:
        """compute_cv_hash should produce different hashes for different inputs."""
        text1 = "CV version 1"
        text2 = "CV version 2"

        hash1 = CVCacheService.compute_cv_hash(text1)
        hash2 = CVCacheService.compute_cv_hash(text2)

        assert hash1 != hash2

    def test_get_returns_none_when_not_cached(self, cv_cache: CVCacheService) -> None:
        """get() should return None when hash not in cache."""
        cv_hash = CVCacheService.compute_cv_hash("some cv")
        result = cv_cache.get(cv_hash)

        assert result is None

    def test_get_returns_cached_markdown(self, cv_cache: CVCacheService) -> None:
        """get() should return cached MarkdownOutput."""
        cv_text = "raw cv text"
        cv_hash = CVCacheService.compute_cv_hash(cv_text)
        markdown = MarkdownOutput(markdown="# Name\nemail@example.com")

        cv_cache.set(cv_hash, markdown)
        result = cv_cache.get(cv_hash)

        assert result == markdown
        assert result.markdown == markdown.markdown

    def test_get_or_compute_misses_on_first_call(self, cv_cache: CVCacheService) -> None:
        """get_or_compute should miss on first call and invoke compute_fn."""
        cv_text = "raw cv"
        call_count = 0

        def compute_fn() -> MarkdownOutput:
            nonlocal call_count
            call_count += 1
            return MarkdownOutput(markdown="# Result")

        result, cache_hit = cv_cache.get_or_compute(cv_text, compute_fn)

        assert call_count == 1
        assert cache_hit is False
        assert result.markdown == "# Result"

    def test_get_or_compute_hits_on_second_call(self, cv_cache: CVCacheService) -> None:
        """get_or_compute should hit on second call and not invoke compute_fn."""
        cv_text = "raw cv"
        call_count = 0

        def compute_fn() -> MarkdownOutput:
            nonlocal call_count
            call_count += 1
            return MarkdownOutput(markdown="# Result")

        # First call - miss
        result1, hit1 = cv_cache.get_or_compute(cv_text, compute_fn)
        assert call_count == 1
        assert hit1 is False

        # Second call - hit
        result2, hit2 = cv_cache.get_or_compute(cv_text, compute_fn)
        assert call_count == 1  # Not called again
        assert hit2 is True
        assert result1 == result2

    def test_get_or_compute_returns_same_result_on_cache_hit(self, cv_cache: CVCacheService) -> None:
        """get_or_compute should return cached result unchanged."""
        cv_text = "my cv"
        expected_markdown = MarkdownOutput(markdown="# Full Name\nemail | phone")

        def compute_fn() -> MarkdownOutput:
            return expected_markdown

        result1, _ = cv_cache.get_or_compute(cv_text, compute_fn)
        result2, _ = cv_cache.get_or_compute(cv_text, compute_fn)

        assert result1 == result2 == expected_markdown

    def test_get_or_compute_different_cv_different_hash(self, cv_cache: CVCacheService) -> None:
        """Different CV text should produce different cache entries."""
        cv_text1 = "CV version 1"
        cv_text2 = "CV version 2"

        markdown1 = MarkdownOutput(markdown="# Result 1")
        markdown2 = MarkdownOutput(markdown="# Result 2")

        def compute_fn1() -> MarkdownOutput:
            return markdown1

        def compute_fn2() -> MarkdownOutput:
            return markdown2

        result1, _ = cv_cache.get_or_compute(cv_text1, compute_fn1)
        result2, _ = cv_cache.get_or_compute(cv_text2, compute_fn2)

        assert result1 == markdown1
        assert result2 == markdown2
        assert result1 != result2


class TestCacheLookupByHash:
    """Test cache lookup using computed hashes."""

    def test_set_and_get_by_hash(self, cv_cache: CVCacheService) -> None:
        """Can set and retrieve using explicit hash."""
        cv_text = "some cv"
        cv_hash = CVCacheService.compute_cv_hash(cv_text)
        markdown = MarkdownOutput(markdown="# Name")

        cv_cache.set(cv_hash, markdown)
        result = cv_cache.get(cv_hash)

        assert result == markdown

    def test_hash_from_text_matches_explicit_hash(self, cv_cache: CVCacheService) -> None:
        """Hash computed from text should match when using get_or_compute."""
        cv_text = "test cv"
        markdown = MarkdownOutput(markdown="# Result")

        def compute_fn() -> MarkdownOutput:
            return markdown

        # Use get_or_compute
        result1, _ = cv_cache.get_or_compute(cv_text, compute_fn)

        # Compute hash explicitly and retrieve
        cv_hash = CVCacheService.compute_cv_hash(cv_text)
        result2 = cv_cache.get(cv_hash)

        assert result1 == result2 == markdown
