"""
PMX-04R1 — High-performance LRU sprite cache with QPixmap storage,
lazy loading, automatic reuse, and no duplicated decoding.
"""

from __future__ import annotations

import time
from collections import OrderedDict

from PySide6.QtGui import QPixmap

from .appearance_models import MaterializedSprite, ResolvedSprite
from .sprite_materializer import SpriteMaterializer


class LRUSpriteCache:
    """LRU cache for sprite pixmaps with automatic eviction and metrics tracking.

    Features:
    - QPixmap cache with LRU eviction
    - Lazy loading (sprites are decoded on first access)
    - Automatic reuse of cached entries
    - No duplicated decoding
    - Memory usage tracking
    """

    def __init__(
        self,
        materializer: SpriteMaterializer | None = None,
        max_entries: int = 10000,
        max_memory_bytes: int = 512 * 1024 * 1024,  # 512 MB
    ) -> None:
        self.materializer = materializer or SpriteMaterializer()
        self._max_entries = max_entries
        self._max_memory_bytes = max_memory_bytes

        # LRU cache: OrderedDict where keys are cache keys and values are (pixmap, material, last_access_time)
        self._cache: OrderedDict[tuple, tuple[QPixmap, MaterializedSprite, float]] = OrderedDict()

        # Metrics
        self._hits: int = 0
        self._misses: int = 0
        self._loaded: int = 0
        self._evictions: int = 0
        self._current_memory: int = 0

    # ── Internal helpers (defined before use) ───────────────────────────────

    @staticmethod
    def _make_key(resolved: ResolvedSprite, size: int, frame: int) -> tuple:
        return (resolved.item_id, resolved.primary_sprite_id or resolved.status, int(size), int(frame))

    def _evict_if_needed(self, new_cost: int) -> None:
        """Evict entries if cache exceeds limits."""
        while len(self._cache) >= self._max_entries or (self._current_memory + new_cost) > self._max_memory_bytes:
            if not self._cache:
                break
            # Evict least recently used (first item in OrderedDict)
            key, (pixmap, _, _) = self._cache.popitem(last=False)
            self._current_memory -= pixmap.width() * pixmap.height() * 4
            self._evictions += 1

    # ── Public API ──────────────────────────────────────────────────────────

    def get(
        self,
        resolved: ResolvedSprite,
        size: int = 32,
        frame: int = 0,
    ) -> tuple[QPixmap, MaterializedSprite]:
        """Get a sprite pixmap from cache or load it."""
        key = self._make_key(resolved, size, frame)

        # Cache hit
        if key in self._cache:
            self._hits += 1
            pixmap, material, _ = self._cache.pop(key)
            self._cache[key] = (pixmap, material, time.perf_counter())
            return pixmap, material

        # Cache miss - load
        self._misses += 1
        pixmap, material = self.materializer.materialize(resolved, size=size, frame=frame)

        # Track memory
        memory_cost = pixmap.width() * pixmap.height() * 4  # RGBA

        # Evict if needed
        self._evict_if_needed(memory_cost)

        # Store
        self._cache[key] = (pixmap, material, time.perf_counter())
        self._current_memory += memory_cost
        self._loaded += 1

        return pixmap, material

    def get_or_placeholder(
        self,
        resolved: ResolvedSprite,
        size: int = 32,
        frame: int = 0,
    ) -> QPixmap:
        """Get a sprite pixmap, returning a placeholder on miss instead of loading."""
        key = self._make_key(resolved, size, frame)

        if key in self._cache:
            self._hits += 1
            pixmap, material, _ = self._cache.pop(key)
            self._cache[key] = (pixmap, material, time.perf_counter())
            return pixmap

        self._misses += 1
        placeholder = QPixmap(size, size)
        placeholder.fill()
        return placeholder

    def contains(self, resolved: ResolvedSprite, size: int = 32, frame: int = 0) -> bool:
        """Check if a sprite is in the cache without loading it."""
        key = self._make_key(resolved, size, frame)
        return key in self._cache

    def invalidate(self, resolved: ResolvedSprite) -> None:
        """Remove all cached entries for a specific sprite."""
        base_key = (resolved.item_id, resolved.primary_sprite_id or resolved.status)
        keys_to_remove = [k for k in self._cache if k[:2] == base_key]
        for key in keys_to_remove:
            pixmap, _, _ = self._cache.pop(key)
            self._current_memory -= pixmap.width() * pixmap.height() * 4

    def invalidate_all(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
        self._current_memory = 0
        self._evictions = 0

    def preload(self, resolved: ResolvedSprite, size: int = 32, frame: int = 0) -> None:
        """Preload a sprite into cache."""
        self.get(resolved, size=size, frame=frame)

    # ── Metrics ─────────────────────────────────────────────────────────────

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def size(self) -> int:
        return len(self._cache)

    @property
    def memory_usage(self) -> int:
        return self._current_memory

    @property
    def evictions(self) -> int:
        return self._evictions

    @property
    def loaded_count(self) -> int:
        return self._loaded

    def report(self) -> dict:
        """Get a detailed cache report."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self.hit_rate,
            "cache_entries": len(self._cache),
            "memory_usage_bytes": self._current_memory,
            "memory_usage_mb": self._current_memory / (1024 * 1024),
            "max_entries": self._max_entries,
            "max_memory_bytes": self._max_memory_bytes,
            "evictions": self._evictions,
            "loaded_sprites": self._loaded,
        }

