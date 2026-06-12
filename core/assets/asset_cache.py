"""
AssetCache — Cachea datos indexados en disco para evitar reindexar cada ejecución.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class AssetCache:
    """
    Cache para datos de assets indexados.
    Guarda items.json, monsters.json, npcs.json en cache/.
    """

    def __init__(self, cache_dir: str = "cache"):
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def exists(self) -> bool:
        """Check if cache files exist."""
        return (self._cache_dir / "items.json").exists()

    # ---- Items ----

    def save_items(self, data: Dict[str, Any]) -> None:
        self._save("items.json", data)

    def load_items(self) -> Optional[Dict[str, Any]]:
        return self._load("items.json")

    # ---- Monsters ----

    def save_monsters(self, data: Dict[str, Any]) -> None:
        self._save("monsters.json", data)

    def load_monsters(self) -> Optional[Dict[str, Any]]:
        return self._load("monsters.json")

    # ---- NPCs ----

    def save_npcs(self, data: Dict[str, Any]) -> None:
        self._save("npcs.json", data)

    def load_npcs(self) -> Optional[Dict[str, Any]]:
        return self._load("npcs.json")

    # ---- Grounds, Walls, Decorations ----

    def save_grounds(self, data: List[int]) -> None:
        self._save("grounds.json", data)

    def load_grounds(self) -> Optional[List[int]]:
        return self._load("grounds.json")

    def save_walls(self, data: List[int]) -> None:
        self._save("walls.json", data)

    def load_walls(self) -> Optional[List[int]]:
        return self._load("walls.json")

    def save_decorations(self, data: List[int]) -> None:
        self._save("decorations.json", data)

    def load_decorations(self) -> Optional[List[int]]:
        return self._load("decorations.json")

    # ---- Internal ----

    def _save(self, filename: str, data: Any) -> None:
        path = self._cache_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self, filename: str) -> Optional[Any]:
        path = self._cache_dir / filename
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
