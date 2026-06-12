"""
CityExtractor — extract city entries from a world.

A "city" is identified by either:
  - a `cities` list in the world dict (from OTBM towns/blueprint houses);
  - a region whose name contains 'city', 'town', 'village', 'hub', 'market';
  - a structure of category 'city', 'temple', 'depot', 'bank' or 'market'.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..models import EntryType, KnowledgeEntry
from .base_extractor import BaseExtractor, _as_int, _as_list, _as_str


class CityExtractor(BaseExtractor):
    NAME = "city"

    CITY_KEYWORDS = ("city", "town", "village", "hub", "market", "outpost")
    CITY_CATEGORIES = (
        "city",
        "town",
        "village",
        "hub",
        "market",
        "temple",
        "depot",
        "bank",
    )

    def extract(self, world: Dict[str, Any], source: str = "") -> List[KnowledgeEntry]:
        entries: List[KnowledgeEntry] = []
        seen: set = set()

        # 1) explicit cities list
        for c in _as_list(world.get("cities")):
            name = _as_str(c.get("name")) if isinstance(c, dict) else _as_str(c)
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            entry = KnowledgeEntry.build(
                entry_type=EntryType.CITY,
                name=name,
                source=_as_str(c.get("source", source)),
                biome=_as_str(
                    c.get("biome", world.get("meta", {}).get("theme", "generic"))
                ),
                min_level=_as_int(c.get("min_level", c.get("level_min", 1))),
                max_level=_as_int(c.get("max_level", c.get("level_max", 9999))),
                tags=_coerce_tags(c),
                attributes={
                    "theme": _as_str(
                        c.get("theme", world.get("meta", {}).get("theme", "generic"))
                    ),
                    "style": _as_str(c.get("style", "medieval")),
                    "size": _as_int(c.get("size", 0)),
                    "has_depot": bool(c.get("has_depot", "depot" in name.lower())),
                    "has_temple": bool(c.get("has_temple", "temple" in name.lower())),
                    "layout": _as_str(c.get("layout", "dense")),
                    "services": _as_list(c.get("services", [])),
                    "roads": _as_list(c.get("roads", [])),
                    "walls": _as_list(c.get("walls", [])),
                },
            )
            entries.append(entry)

        # 2) regions with city-like names
        for r in _as_list(world.get("regions")):
            if not isinstance(r, dict):
                continue
            rname = _as_str(r.get("name"))
            lname = rname.lower()
            if not rname or lname in seen:
                continue
            if any(kw in lname for kw in self.CITY_KEYWORDS) and not any(
                svc in lname for svc in ("depot", "temple", "npc_hub")
            ):
                seen.add(lname)
                entries.append(
                    KnowledgeEntry.build(
                        entry_type=EntryType.CITY,
                        name=rname,
                        source=source,
                        biome=_as_str(r.get("theme", "generic")),
                        min_level=_as_int(r.get("min_level", 1)),
                        max_level=_as_int(r.get("max_level", 9999)),
                        tags=_coerce_tags(r),
                        attributes={
                            "theme": _as_str(r.get("theme", "generic")),
                            "style": "region",
                            "layout": "open",
                            "tags": _as_list(r.get("tags", [])),
                        },
                    )
                )

        # 3) structures of city category
        for s in _as_list(world.get("structures")):
            if not isinstance(s, dict):
                continue
            cat = _as_str(s.get("category", "")).lower()
            name = _as_str(s.get("name"))
            if not name or cat not in self.CITY_CATEGORIES or name.lower() in seen:
                continue
            seen.add(name.lower())
            # Use 'biome' if present, else 'theme', else world meta theme.
            biome = (
                _as_str(s.get("biome"))
                or _as_str(s.get("theme"))
                or _as_str(world.get("meta", {}).get("theme", "generic"))
            )
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.CITY,
                    name=name,
                    source=source,
                    biome=biome,
                    min_level=_as_int(s.get("min_level", 1)),
                    max_level=_as_int(s.get("max_level", 9999)),
                    tags=_coerce_tags(s),
                    attributes={
                        "theme": _as_str(s.get("theme", "generic")),
                        "style": cat,
                        "size": _as_int(s.get("width", 0))
                        * _as_int(s.get("height", 0)),
                        "layout": _as_str(s.get("layout", "open")),
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
