"""Tests for in-memory cache infrastructure."""

from __future__ import annotations

import time

import pytest

from app.infrastructure.cache import CacheManager, CacheEntry


class TestCacheEntry:
    """Test individual cache entry behavior."""

    def test_entry_not_expired_when_fresh(self) -> None:
        """Fresh entry should not be expired."""
        entry = CacheEntry("value", ttl_seconds=3600.0)
        assert not entry.is_expired()

    def test_entry_expired_after_ttl(self) -> None:
        """Entry should expire after TTL."""
        entry = CacheEntry("value", ttl_seconds=0.01)
        time.sleep(0.02)
        assert entry.is_expired()

    def test_entry_no_expiry_when_ttl_zero(self) -> None:
        """Entry with zero TTL should never expire."""
        entry = CacheEntry("value", ttl_seconds=0)
        time.sleep(0.1)
        assert not entry.is_expired()

    def test_entry_no_expiry_when_ttl_negative(self) -> None:
        """Entry with negative TTL should never expire."""
        entry = CacheEntry("value", ttl_seconds=-1.0)
        time.sleep(0.1)
        assert not entry.is_expired()


class TestCacheManager:
    """Test CacheManager behavior."""

    @pytest.fixture
    def cache(self) -> CacheManager:
        """Create a fresh cache manager for each test."""
        return CacheManager(default_ttl=3600.0)

    def test_get_nonexistent_key_returns_none(self, cache: CacheManager) -> None:
        """get() on nonexistent key should return None."""
        result = cache.get("nonexistent")
        assert result is None

    def test_set_and_get(self, cache: CacheManager) -> None:
        """set() followed by get() should return the value."""
        cache.set("key", "value")
        result = cache.get("key")
        assert result == "value"

    def test_set_multiple_keys(self, cache: CacheManager) -> None:
        """Can store multiple different keys."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"

    def test_get_returns_none_for_expired_entry(self) -> None:
        """get() should return None for expired entry and remove it."""
        cache = CacheManager(default_ttl=0.01)
        cache.set("key", "value")
        time.sleep(0.02)

        result = cache.get("key")
        assert result is None

    def test_delete_existing_key(self, cache: CacheManager) -> None:
        """delete() should remove a key and return True."""
        cache.set("key", "value")
        result = cache.delete("key")

        assert result is True
        assert cache.get("key") is None

    def test_delete_nonexistent_key(self, cache: CacheManager) -> None:
        """delete() on nonexistent key should return False."""
        result = cache.delete("nonexistent")
        assert result is False

    def test_clear_removes_all_entries(self, cache: CacheManager) -> None:
        """clear() should remove all entries."""
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.size() == 0

    def test_size_returns_entry_count(self, cache: CacheManager) -> None:
        """size() should return number of entries."""
        assert cache.size() == 0

        cache.set("key1", "value1")
        assert cache.size() == 1

        cache.set("key2", "value2")
        assert cache.size() == 2

        cache.delete("key1")
        assert cache.size() == 1

    def test_cleanup_expired_removes_expired_entries(self) -> None:
        """cleanup_expired() should remove expired entries."""
        cache = CacheManager(default_ttl=0.01)

        cache.set("key1", "value1")
        time.sleep(0.02)
        cache.set("key2", "value2")  # Fresh entry

        removed = cache.cleanup_expired()

        assert removed == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"

    def test_set_with_custom_ttl_override(self) -> None:
        """set() with custom ttl_seconds should override default."""
        cache = CacheManager(default_ttl=3600.0)

        cache.set("key", "value", ttl_seconds=0.01)
        time.sleep(0.02)

        result = cache.get("key")
        assert result is None

    def test_set_with_zero_ttl_never_expires(self, cache: CacheManager) -> None:
        """set() with ttl_seconds=0 should never expire."""
        cache.set("key", "value", ttl_seconds=0)
        time.sleep(0.1)

        result = cache.get("key")
        assert result == "value"

    def test_thread_safety_multiple_sets(self, cache: CacheManager) -> None:
        """Concurrent sets should not cause data loss."""
        import threading

        def set_values(prefix: str, count: int) -> None:
            for i in range(count):
                cache.set(f"{prefix}_{i}", f"value_{i}")

        threads = [
            threading.Thread(target=set_values, args=("thread1", 10)),
            threading.Thread(target=set_values, args=("thread2", 10)),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All 20 entries should be present
        assert cache.size() == 20

    def test_get_removes_expired_entry(self, cache: CacheManager) -> None:
        """get() on expired entry should remove it from cache."""
        custom_cache = CacheManager(default_ttl=0.01)
        custom_cache.set("key", "value")

        initial_size = custom_cache.size()
        assert initial_size == 1

        time.sleep(0.02)
        result = custom_cache.get("key")

        assert result is None
        assert custom_cache.size() == 0

    def test_overwrite_key(self, cache: CacheManager) -> None:
        """set() on existing key should overwrite."""
        cache.set("key", "value1")
        cache.set("key", "value2")

        result = cache.get("key")
        assert result == "value2"
        assert cache.size() == 1
