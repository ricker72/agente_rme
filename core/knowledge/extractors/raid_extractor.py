"""
RaidExtractor — extract raid entries from a world.

A "raid" is a region/structure whose name contains 'raid', 'inquisition',
'ferumbras', 'bossrush' or 'encounter'.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..models import EntryType, KnowledgeEntry
from .base_extractor import BaseExtractor, _as_int, _as_list, _as_str


class RaidExtractor(BaseExtractor):
    NAME = "raid"

    RAID_KEYWORDS = (
        "raid",
        "inquisition",
        "ferumbras",
        "bossrush",
        "encounter",
        "ordeal",
    )
    RAID_CATEGORIES = ("raid", "encounter", "ordeal")

    def extract(self, world: Dict[str, Any], source: str = "") -> List[KnowledgeEntry]:
        entries: List[KnowledgeEntry] = []
        seen: set = set()

        # 0) Explicit "raids" list
        for r in _as_list(world.get("raids")):
            if not isinstance(r, dict):
                continue
            rname = _as_str(r.get("name"))
            if not rname or rname.lower() in seen:
                continue
            seen.add(rname.lower())
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.RAID,
                    name=rname,
                    source=source,
                    biome=_as_str(r.get("theme", "generic")),
                    min_level=_as_int(r.get("min_level", 200)),
                    max_level=_as_int(r.get("max_level", 9999)),
                    tags=_coerce_tags(r) + ["raid"],
                    attributes={
                        "theme": _as_str(r.get("theme", "generic")),
                        "difficulty": _as_str(r.get("difficulty", "extreme")),
                        "style": "raid",
                        "bosses": _as_list(r.get("bosses", [])),
                        "monsters": _as_list(r.get("monsters", [])),
                        "size": _as_int(r.get("size", 0)),
                    },
                )
            )

        for r in _as_list(world.get("regions")):
            if not isinstance(r, dict):
                continue
            rname = _as_str(r.get("name"))
            lname = rname.lower()
            if not rname or lname in seen:
                continue
            if not any(kw in lname for kw in self.RAID_KEYWORDS):
                continue
            seen.add(lname)
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.RAID,
                    name=rname,
                    source=source,
                    biome=_as_str(r.get("theme", "generic")),
                    min_level=_as_int(r.get("min_level", 200)),
                    max_level=_as_int(r.get("max_level", 9999)),
                    tags=_coerce_tags(r) + ["raid"],
                    attributes={
                        "theme": _as_str(r.get("theme", "generic")),
                        "difficulty": "extreme",
                        "style": "raid",
                        "bosses": _as_list(r.get("bosses", [])),
                        "monsters": _as_list(r.get("monsters", [])),
                        "size": _as_int(r.get("size", 0)),
                    },
                )
            )

        for s in _as_list(world.get("structures")):
            if not isinstance(s, dict):
                continue
            cat = _as_str(s.get("category", "")).lower()
            name = _as_str(s.get("name"))
            lname = name.lower()
            if not name or lname in seen:
                continue
            if cat not in self.RAID_CATEGORIES and not any(
                kw in lname for kw in self.RAID_KEYWORDS
            ):
                continue
            seen.add(lname)
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.RAID,
                    name=name,
                    source=source,
                    biome=_as_str(s.get("biome", "generic")),
                    min_level=_as_int(s.get("min_level", 200)),
                    max_level=_as_int(s.get("max_level", 9999)),
                    tags=_coerce_tags(s) + ["raid"],
                    attributes={
                        "theme": _as_str(s.get("theme", "generic")),
                        "difficulty": _as_str(s.get("difficulty", "extreme")),
                        "style": "raid",
                        "size": _as_int(s.get("width", 0))
                        * _as_int(s.get("height", 0)),
                    },
                )
            )
        return entries


def _coerce_tags(obj: Dict[str, Any]) -> List[str]:
    raw = obj.get("tags") if isinstance(obj, dict) else None
    if isinstance(raw, list):
        return [str(t) for t in raw]
    if isinstance(raw, str):
        return [t.strip() for t in raw.split(",") if t.strip()]
    return []
