"""
WaypointExtractor — extract waypoint entries from a world.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..models import EntryType, KnowledgeEntry
from .base_extractor import BaseExtractor, _as_int, _as_list, _as_str


class WaypointExtractor(BaseExtractor):
    NAME = "waypoint"

    def extract(self, world: Dict[str, Any], source: str = "") -> List[KnowledgeEntry]:
        entries: List[KnowledgeEntry] = []
        seen: set = set()

        for w in _as_list(world.get("waypoints")):
            if not isinstance(w, dict):
                continue
            name = _as_str(w.get("name"))
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.WAYPOINT,
                    name=name,
                    source=source,
                    biome=_as_str(w.get("biome", "generic")),
                    min_level=_as_int(w.get("min_level", 1)),
                    max_level=_as_int(w.get("max_level", 9999)),
                    tags=_coerce_tags(w) + ["waypoint"],
                    attributes={
                        "theme": _as_str(w.get("theme", "generic")),
                        "x": _as_int(w.get("x", 0)),
                        "y": _as_int(w.get("y", 0)),
                        "z": _as_int(w.get("z", 7)),
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
