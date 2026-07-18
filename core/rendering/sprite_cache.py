"""Pixmap cache for PMX-03 sprite thumbnails."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass

from PySide6.QtGui import QPixmap

from .appearance_models import MaterializedSprite, ResolvedSprite
from .sprite_materializer import SpriteMaterializer


@dataclass
class SpriteCacheMetrics:
    hits: int = 0
    misses: int = 0
    loaded_sprites: int = 0
    unresolved_sprites: int = 0
    evictions: int = 0


class SpriteCache:
    def __init__(
        self,
        materializer: SpriteMaterializer | None = None,
        *,
        max_entries: int = 2048,
        max_memory_bytes: int = 64 * 1024 * 1024,
    ) -> None:
        if max_entries < 1 or max_memory_bytes < 1:
            raise ValueError("Sprite cache limits must be positive")
        self.materializer = materializer or SpriteMaterializer()
        self.max_entries = max_entries
        self.max_memory_bytes = max_memory_bytes
        self._memory_bytes = 0
        self._cache: OrderedDict[
            tuple[int | str | None, int | str | None, int, int], QPixmap
        ] = OrderedDict()
        self._materials: dict[
            tuple[int | str | None, int | str | None, int, int], MaterializedSprite
        ] = {}
        self.metrics = SpriteCacheMetrics()

    def thumbnail(self, resolved: ResolvedSprite, size: int = 32, frame: int = 0) -> tuple[QPixmap, MaterializedSprite]:
        key = (resolved.item_id, resolved.primary_sprite_id or resolved.status, int(size), int(frame))
        if key in self._cache:
            self.metrics.hits += 1
            self._cache.move_to_end(key)
            return self._cache[key], self._materials[key]
        self.metrics.misses += 1
        pixmap, material = self.materializer.materialize(resolved, size=size, frame=frame)
        memory_cost = pixmap.width() * pixmap.height() * 4
        if memory_cost > self.max_memory_bytes:
            self.metrics.unresolved_sprites += 1
            return pixmap, material
        while self._cache and (
            len(self._cache) >= self.max_entries
            or self._memory_bytes + memory_cost > self.max_memory_bytes
        ):
            old_key, old_pixmap = self._cache.popitem(last=False)
            self._materials.pop(old_key, None)
            self._memory_bytes -= old_pixmap.width() * old_pixmap.height() * 4
            self.metrics.evictions += 1
        self._cache[key] = pixmap
        self._materials[key] = material
        self._memory_bytes += memory_cost
        if material.status in {
            "REAL_SPRITE_RENDERED",
            "PIXEL_SOURCE_MISSING",
            "PIXEL_SOURCE_IDENTIFIED",
            "SPRITE_PIXEL_SOURCE_MISSING",
            "SPRITE_PIXEL_DECODER_PENDING",
        }:
            self.metrics.loaded_sprites += 1
        else:
            self.metrics.unresolved_sprites += 1
        return pixmap, material

    def report(self) -> dict[str, int]:
        return {
            "hits": self.metrics.hits,
            "misses": self.metrics.misses,
            "loaded_sprites": self.metrics.loaded_sprites,
            "unresolved_sprites": self.metrics.unresolved_sprites,
            "cache_entries": len(self._cache),
            "memory_estimate": self._memory_bytes,
            "max_entries": self.max_entries,
            "max_memory_bytes": self.max_memory_bytes,
            "evictions": self.metrics.evictions,
        }
