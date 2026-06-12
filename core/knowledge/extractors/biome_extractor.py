"""
BiomeExtractor — extract biome entries from a world.

A biome is derived from:
  - the world `meta.theme` (one per world);
  - the distinct set of region themes found in the world;
  - explicit `biomes` list in the world dict.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..models import EntryType, KnowledgeEntry
from .base_extractor import BaseExtractor, _as_int, _as_list, _as_str


class BiomeExtractor(BaseExtractor):
    NAME = "biome"

    def extract(self, world: Dict[str, Any], source: str = "") -> List[KnowledgeEntry]:
        entries: List[KnowledgeEntry] = []
        seen: set = set()

        def _add(name: str, attrs: Dict[str, Any], level_min: int, level_max: int):
            if not name:
                return
            key = name.lower()
            if key in seen or key == "generic":
                return
            seen.add(key)
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.BIOME,
                    name=name,
                    source=source,
                    biome=name,
                    min_level=level_min,
                    max_level=level_max,
                    tags=[key, "biome"],
                    attributes=attrs,
                )
            )

        # 1) Explicit biomes list
        for b in _as_list(world.get("biomes")):
            if not isinstance(b, dict):
                continue
            name = _as_str(b.get("name"))
            if not name:
                continue
            _add(
                name,
                {
                    "theme": name,
                    "style": _as_str(b.get("style", "wilderness")),
                    "climate": _as_str(b.get("climate", "temperate")),
                },
                _as_int(b.get("min_level", 1)),
                _as_int(b.get("max_level", 9999)),
            )

        # 2) Distinct region themes
        for r in _as_list(world.get("regions")):
            if not isinstance(r, dict):
                continue
            theme = _as_str(r.get("theme"))
            if not theme or theme == "generic":
                continue
            _add(
                theme.title(),
                {
                    "theme": theme,
                    "style": "biome",
                    "climate": _as_str(r.get("climate", "temperate")),
                },
                _as_int(r.get("min_level", 1)),
                _as_int(r.get("max_level", 9999)),
            )

        # 3) World-level theme from meta
        meta = world.get("meta", {}) or {}
        wt = _as_str(meta.get("theme"))
        if wt and wt != "generic":
            _add(wt.title(), {"theme": wt, "style": "biome"}, 1, 9999)
        return entries


def _coerce_tags(obj: Dict[str, Any]) -> List[str]:
    raw = obj.get("tags") if isinstance(obj, dict) else None
    if isinstance(raw, list):
        return [str(t) for t in raw]
    if isinstance(raw, str):
        return [t.strip() for t in raw.split(",") if t.strip()]
    return []
