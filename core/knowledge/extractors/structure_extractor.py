"""
StructureExtractor — extract generic structure / region entries from a world.

Used to populate the `regions` bucket with things like dungeons, theme
zones, expansion regions, and other generic structures.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..models import EntryType, KnowledgeEntry
from .base_extractor import BaseExtractor, _as_int, _as_list, _as_str


class StructureExtractor(BaseExtractor):
    NAME = "structure"

    DUNGEON_KEYWORDS = (
        "dungeon", "tomb", "crypt", "pyramid", "temple",
        "shrine", "catacomb", "lair",
    )

    def extract(self, world: Dict[str, Any], source: str = "") -> List[KnowledgeEntry]:
        entries: List[KnowledgeEntry] = []
        seen: set = set()

        # 1) Dungeons from regions
        for r in _as_list(world.get("regions")):
            if not isinstance(r, dict):
                continue
            rname = _as_str(r.get("name"))
            lname = rname.lower()
            if not rname or lname in seen:
                continue
            if not any(kw in lname for kw in self.DUNGEON_KEYWORDS):
                continue
            # Skip if it is already a city / boss / raid / quest (handled by other extractors)
            if any(kw in lname for kw in (
                "city", "town", "village", "hub", "market",
                "boss", "arena", "throne",
                "raid", "inquisition",
                "quest", "mission", "task",
            )):
                continue
            seen.add(lname)
            entries.append(KnowledgeEntry.build(
                entry_type=EntryType.DUNGEON,
                name=rname,
                source=source,
                biome=_as_str(r.get("theme", "generic")),
                min_level=_as_int(r.get("min_level", 1)),
                max_level=_as_int(r.get("max_level", 9999)),
                tags=_coerce_tags(r) + ["dungeon"],
                attributes={
                    "theme": _as_str(r.get("theme", "generic")),
                    "difficulty": _as_str(r.get("difficulty", "hard")),
                    "style": "dungeon",
                    "size": _as_int(r.get("size", 0)),
                },
            ))

        # 2) Catch-all regions that were not picked up by any other extractor
        for r in _as_list(world.get("regions")):
            if not isinstance(r, dict):
                continue
            rname = _as_str(r.get("name"))
            lname = rname.lower()
            if not rname or lname in seen:
                continue
            # Skip if it would be a city/hunt/boss/etc.
            if any(kw in lname for kw in (
                "city", "town", "village", "hub", "market",
                "hunt", "spawn", "farm", "cave", "sewer",
                "boss", "arena", "throne", "lair",
                "raid", "inquisition",
                "quest", "mission", "task",
            )):
                continue
            seen.add(lname)
            entries.append(KnowledgeEntry.build(
                entry_type=EntryType.REGION,
                name=rname,
                source=source,
                biome=_as_str(r.get("theme", "generic")),
                min_level=_as_int(r.get("min_level", 1)),
                max_level=_as_int(r.get("max_level", 9999)),
                tags=_coerce_tags(r),
                attributes={
                    "theme": _as_str(r.get("theme", "generic")),
                    "style": "region",
                },
            ))

        # 3) Catch-all structures that did not match a more specific category
        for s in _as_list(world.get("structures")):
            if not isinstance(s, dict):
                continue
            cat = _as_str(s.get("category", "")).lower()
            name = _as_str(s.get("name"))
            lname = name.lower()
            if not name or lname in seen:
                continue
            if cat in ("city", "town", "village", "hub", "market",
                       "boss", "boss_room", "arena",
                       "raid", "encounter",
                       "quest", "mission", "task"):
                continue
            seen.add(lname)
            entries.append(KnowledgeEntry.build(
                entry_type=EntryType.STRUCTURE,
                name=name,
                source=source,
                biome=_as_str(s.get("biome", "generic")),
                min_level=_as_int(s.get("min_level", 1)),
                max_level=_as_int(s.get("max_level", 9999)),
                tags=_coerce_tags(s),
                attributes={
                    "theme": _as_str(s.get("theme", "generic")),
                    "style": cat or "generic",
                    "size": _as_int(s.get("width", 0)) * _as_int(s.get("height", 0)),
                },
            ))
        return entries


def _coerce_tags(obj: Dict[str, Any]) -> List[str]:
    raw = obj.get("tags") if isinstance(obj, dict) else None
    if isinstance(raw, list):
        return [str(t) for t in raw]
    if isinstance(raw, str):
        return [t.strip() for t in raw.split(",") if t.strip()]
    return []
