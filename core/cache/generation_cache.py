from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


class GenerationCache:
    """
    Prevents recalculation of biomes, blueprints, and RAG queries.

    Simple TTL-based file cache.

    Usage:
        cache = GenerationCache(max_size_mb=256, ttl=3600)
        cache.set("biome:issavi", biome_data)
        biome = cache.get("biome:issavi")
    """

    def __init__(self, cache_dir: str = ".cache", max_size_mb: int = 256,
                 ttl_seconds: int = 3600):
        self._dir = Path(cache_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._max_size = max_size_mb * 1024 * 1024
        self._ttl = ttl_seconds
        self._index: Dict[str, float] = {}

    def _path(self, key: str) -> Path:
        h = hashlib.md5(key.encode()).hexdigest()
        return self._dir / f"{h}.json"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value. Returns None if expired or missing."""
        path = self._path(key)
        if not path.exists():
            return None
        age = time.time() - path.stat().st_mtime
        if self._ttl > 0 and age > self._ttl:
            path.unlink(missing_ok=True)
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache."""
        path = self._path(key)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        self._evict_if_needed()

    def clear(self) -> None:
        """Remove all cache entries."""
        for f in self._dir.glob("*.json"):
            f.unlink(missing_ok=True)

    def invalidate(self, key: str) -> None:
        """Remove a specific cache entry."""
        self._path(key).unlink(missing_ok=True)

    def _evict_if_needed(self) -> None:
        """Remove oldest entries if over max_size_mb."""
        total = sum(f.stat().st_size for f in self._dir.glob("*.json"))
        if total <= self._max_size:
            return
        files = sorted(
            self._dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
        )
        for f in files:
            if total <= self._max_size * 0.8:
                break
            total -= f.stat().st_size
            f.unlink(missing_ok=True)

    def stats(self) -> Dict:
        """Return cache statistics."""
        files = list(self._dir.glob("*.json"))
        total_bytes = sum(f.stat().st_size for f in files)
        return {
            "entries": len(files),
            "size_bytes": total_bytes,
            "size_mb": round(total_bytes / (1024 * 1024), 2),
            "max_mb": round(self._max_size / (1024 * 1024), 2),
        }