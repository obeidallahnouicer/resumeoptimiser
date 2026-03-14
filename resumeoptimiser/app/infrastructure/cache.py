"""In-memory cache with TTL support.

A thread-safe, simple key-value store with time-to-live (TTL) expiration.
Designed for caching system prompts and parsed CV markdown.

Thread-safe: Uses threading.Lock for concurrent access.
TTL: Expired entries are removed on access or via cleanup.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Generic, Optional, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class CacheEntry(Generic[T]):
    """Single cache entry with timestamp and TTL."""

    def __init__(self, value: T, ttl_seconds: float) -> None:
        self.value = value
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if this entry has exceeded its TTL."""
        if self.ttl_seconds <= 0:
            # Negative or zero TTL means no expiration
            return False
        elapsed = time.time() - self.created_at
        return elapsed > self.ttl_seconds


class CacheManager:
    """Thread-safe in-memory cache with TTL support."""

    def __init__(self, default_ttl: float = 3600.0) -> None:
        """Initialize the cache manager.

        Args:
            default_ttl: Default time-to-live in seconds. 0 = no expiration.
        """
        self._cache: dict[str, CacheEntry[Any]] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from cache if it exists and hasn't expired.

        Args:
            key: Cache key

        Returns:
            The cached value if found and valid, None otherwise.
        """
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                logger.debug("cache.expired", key=key)
                return None

            logger.debug("cache.hit", key=key)
            return entry.value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Store a value in cache with optional TTL override.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional TTL override. If None, uses default_ttl.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl

        with self._lock:
            self._cache[key] = CacheEntry(value, ttl)
            logger.debug("cache.set", key=key, ttl=ttl)

    def delete(self, key: str) -> bool:
        """Delete a key from cache.

        Args:
            key: Cache key

        Returns:
            True if the key existed, False otherwise.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug("cache.delete", key=key)
                return True
            return False

    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
            logger.debug("cache.clear")

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v.is_expired()]
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                logger.debug("cache.cleanup", removed_count=len(expired_keys))
            return len(expired_keys)

    def size(self) -> int:
        """Return current number of entries in cache."""
        with self._lock:
            return len(self._cache)
