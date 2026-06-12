"""
BossExtractor — extract boss room entries from a world.

Identifies boss rooms by:
  - regions whose name contains 'boss', 'arena', 'throne' or 'lair';
  - structures with category 'boss', 'boss_room' or 'arena';
  - structures tagged 'boss'.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..models import EntryType, KnowledgeEntry
from .base_extractor import BaseExtractor, _as_int, _as_list, _as_str


def _coerce_tags(obj: Dict[str, Any]) -> List[str]:
    raw = obj.get("tags") if isinstance(obj, dict) else None
    if isinstance(raw, list):
        return [str(t) for t in raw]
    if isinstance(raw, str):
        return [t.strip() for t in raw.split(",") if t.strip()]
    return []


class BossExtractor(BaseExtractor):
    NAME = "boss"

    BOSS_KEYWORDS = ("boss", "arena", "throne", "lair")
    ARENA_TYPES = ("throne", "pit", "coliseum", "circular", "open", "closed")
    CIRCULAR_ARENA_TYPES = ("throne", "coliseum", "circular")

    def extract(self, world: Dict[str, Any], source: str = "") -> List[KnowledgeEntry]:
        entries: List[KnowledgeEntry] = []
        seen: set = set()

        # 1) Structures with category/tags
        for s in _as_list(world.get("structures")):
            if not isinstance(s, dict):
                continue
            name = _as_str(s.get("name"))
            if not name:
                continue
            cat = _as_str(s.get("category", "")).lower()
            tags = {str(t).lower() for t in _as_list(s.get("tags", []))}
            if cat not in ("boss", "boss_room", "arena") and "boss" not in tags:
                continue
            key = name.lower()
            if key in seen:
                continue
            seen.add(key)
            width = _as_int(s.get("width", 0))
            height = _as_int(s.get("height", 0))
            area = width * height if width and height else 0
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.BOSS_ROOM,
                    name=name,
                    source=source,
                    biome=_as_str(
                        s.get("biome", world.get("meta", {}).get("theme", "generic"))
                    ),
                    min_level=_as_int(s.get("min_level", 1)),
                    max_level=_as_int(s.get("max_level", 9999)),
                    tags=_coerce_tags(s) + ["boss"],
                    attributes={
                        "theme": _as_str(s.get("theme", "generic")),
                        "arena_type": self._infer_arena_type(cat, tags, name),
                        "shape": (
                            "circular"
                            if any(t in tags for t in self.CIRCULAR_ARENA_TYPES)
                            else "rectangular"
                        ),
                        "size": area,
                        "escape_routes": _as_int(s.get("escape_routes", 1)),
                        "boss": _as_str(s.get("boss", "")),
                        "monsters": _as_list(s.get("monsters", [])),
                    },
                )
            )

        # 2) Regions with boss-like names
        for r in _as_list(world.get("regions")):
            if not isinstance(r, dict):
                continue
            rname = _as_str(r.get("name"))
            lname = rname.lower()
            if not rname or lname in seen:
                continue
            if not any(kw in lname for kw in self.BOSS_KEYWORDS):
                continue
            seen.add(lname)
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.BOSS_ROOM,
                    name=rname,
                    source=source,
                    biome=_as_str(r.get("theme", "generic")),
                    min_level=_as_int(r.get("min_level", 1)),
                    max_level=_as_int(r.get("max_level", 9999)),
                    tags=_coerce_tags(r) + ["boss"],
                    attributes={
                        "theme": _as_str(r.get("theme", "generic")),
                        "arena_type": self._infer_arena_type("", set(), rname),
                        "shape": (
                            "circular"
                            if any(
                                kw in lname for kw in ("arena", "throne", "coliseum")
                            )
                            else "rectangular"
                        ),
                        "size": _as_int(r.get("size", 0)),
                        "escape_routes": _as_int(r.get("escape_routes", 1)),
                        "monsters": _as_list(r.get("monsters", [])),
                    },
                )
            )
        return entries

    def _infer_arena_type(self, category: str, tags: set, name: str) -> str:
        for t in tags:
            if t in self.ARENA_TYPES:
                return t
        lname = name.lower()
        for t in self.ARENA_TYPES:
            if t in lname:
                return t
        if category in ("boss", "boss_room"):
            return "throne"
        return "open"
