"""
Deterministic render cache for WG-20U-A.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from PySide6.QtGui import QPixmap


CacheKey = Tuple[int, int, str, str, int]


@dataclass
class RenderCacheStats:
    hits: int = 0
    misses: int = 0


class RenderCache:
    """Caches rendered pixmaps by deterministic appearance tile key."""

    def __init__(self) -> None:
        self._cache: Dict[CacheKey, QPixmap] = {}
        self.stats = RenderCacheStats()

    def make_key(
        self,
        appearance_id: int,
        floor: int,
        role: str,
        brush: str,
        animation_frame: int = 0,
    ) -> CacheKey:
        return (
            int(appearance_id),
            int(floor),
            str(role).upper(),
            str(brush),
            int(animation_frame),
        )

    def get(self, key: CacheKey) -> Optional[QPixmap]:
        if key in self._cache:
            self.stats.hits += 1
            return self._cache[key]
        self.stats.misses += 1
        return None

    def set(self, key: CacheKey, pixmap: QPixmap) -> QPixmap:
        self._cache[key] = pixmap
        return pixmap

    def audit(self) -> dict[str, object]:
        return {
            "cache_enabled": True,
            "deterministic": True,
            "cache_hit_tracking": True,
            "cache_hits": self.stats.hits,
            "cache_misses": self.stats.misses,
            "cache_entries": len(self._cache),
        }
