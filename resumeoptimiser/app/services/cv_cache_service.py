"""CV parsing and markdown caching service.

Manages the lifecycle of parsed CV markdown output.
Uses deterministic keys derived from file hash: 'parsed_cv:{cv_hash}'

Key benefit: The OCR → Markdown conversion is expensive and deterministic.
By caching the result keyed by the file's content hash, we avoid re-parsing
the same CV multiple times, reducing both latency and token usage.

Example usage:
    cache_svc = CVCacheService(cache_manager, ttl=3600)
    cv_text = "raw PDF text..."
    
    markdown, hit = cache_svc.get_or_compute(
        cv_text,
        compute_fn=lambda: ocr_agent.execute(cv_text)
    )
    # First call: computes via compute_fn, caches result, returns (result, False)
    # Subsequent calls: returns cached result, logs CACHE_HIT, returns (result, True)
"""

from __future__ import annotations

import hashlib
from typing import Callable

from app.core.logging import get_logger
from app.infrastructure.cache import CacheManager
from app.schemas.markdown import MarkdownOutput

logger = get_logger(__name__)


class CVCacheService:
    """Manages caching of parsed CV markdown output."""

    def __init__(self, cache: CacheManager, ttl_seconds: float = 3600.0) -> None:
        """Initialize the CV cache service.

        Args:
            cache: CacheManager instance (typically a singleton)
            ttl_seconds: Default TTL for cached CV markdown
        """
        self._cache = cache
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def compute_cv_hash(cv_text: str) -> str:
        """Compute a stable SHA256 hash of CV text.

        Args:
            cv_text: Raw CV text content

        Returns:
            Hex digest of SHA256 hash
        """
        return hashlib.sha256(cv_text.encode("utf-8")).hexdigest()

    def _build_key(self, cv_hash: str) -> str:
        """Build a deterministic cache key for a parsed CV.

        Args:
            cv_hash: SHA256 hash of CV content

        Returns:
            Cache key like 'parsed_cv:{cv_hash}'
        """
        return f"parsed_cv:{cv_hash}"

    def get(self, cv_hash: str) -> MarkdownOutput | None:
        """Retrieve a cached parsed CV markdown.

        Args:
            cv_hash: SHA256 hash of CV content

        Returns:
            The cached MarkdownOutput if found, None otherwise.
        """
        key = self._build_key(cv_hash)
        return self._cache.get(key)

    def set(self, cv_hash: str, markdown_output: MarkdownOutput) -> None:
        """Store a parsed CV markdown in cache.

        Args:
            cv_hash: SHA256 hash of CV content
            markdown_output: The MarkdownOutput to cache
        """
        key = self._build_key(cv_hash)
        self._cache.set(key, markdown_output, ttl_seconds=self._ttl_seconds)
        logger.info("cv_cache.set", key=key)

    def get_or_compute(
        self,
        cv_text: str,
        compute_fn: Callable[[], MarkdownOutput],
    ) -> tuple[MarkdownOutput, bool]:
        """Retrieve parsed CV from cache or compute it if not found.

        Typical usage in OCRToMarkdownAgent:
            markdown_output, cache_hit = self._cv_cache.get_or_compute(
                cv_text,
                compute_fn=lambda: self._parse_and_convert(cv_text)
            )
            if cache_hit:
                logger.info("ocr_to_markdown.cache_hit")
            else:
                logger.info("ocr_to_markdown.cache_miss")

        Args:
            cv_text: Raw CV text content
            compute_fn: Callable that performs the actual OCR → Markdown conversion

        Returns:
            Tuple of (MarkdownOutput, cache_hit_bool)
            - MarkdownOutput: Either cached or newly computed
            - cache_hit_bool: True if from cache, False if newly computed
        """
        cv_hash = self.compute_cv_hash(cv_text)
        key = self._build_key(cv_hash)

        # Check cache first
        cached = self._cache.get(key)
        if cached is not None:
            logger.info("cv_cache.hit", key=key, cv_hash=cv_hash)
            return cached, True

        # Not in cache: compute
        logger.info("cv_cache.miss", key=key, cv_hash=cv_hash)
        result = compute_fn()
        self._cache.set(key, result, ttl_seconds=self._ttl_seconds)
        return result, False
