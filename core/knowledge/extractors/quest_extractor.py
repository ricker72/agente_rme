"""
QuestExtractor — extract quest entries from a world / campaign.

Quests are usually found in:
  - `quests` list in the world dict (from campaign generator);
  - region names containing 'quest' or 'mission';
  - structures of category 'quest', 'mission' or 'task'.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..models import EntryType, KnowledgeEntry
from .base_extractor import BaseExtractor, _as_int, _as_list, _as_str


class QuestExtractor(BaseExtractor):
    NAME = "quest"

    QUEST_KEYWORDS = ("quest", "mission", "task", "soul_war", "inquisition")
    QUEST_CATEGORIES = ("quest", "mission", "task")

    def extract(self, world: Dict[str, Any], source: str = "") -> List[KnowledgeEntry]:
        entries: List[KnowledgeEntry] = []
        seen: set = set()

        for q in _as_list(world.get("quests")):
            if not isinstance(q, dict):
                continue
            name = _as_str(q.get("name"))
            if not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.QUEST,
                    name=name,
                    source=source,
                    biome=_as_str(q.get("biome", "generic")),
                    min_level=_as_int(q.get("min_level", q.get("level_min", 1))),
                    max_level=_as_int(q.get("max_level", q.get("level_max", 9999))),
                    tags=_coerce_tags(q) + ["quest"],
                    attributes={
                        "theme": _as_str(q.get("theme", "generic")),
                        "difficulty": _as_str(q.get("difficulty", "medium")),
                        "style": _as_str(q.get("style", "linear")),
                        "bosses": _as_list(q.get("bosses", [])),
                        "steps": _as_list(q.get("steps", [])),
                        "monsters": _as_list(q.get("monsters", [])),
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
            if not any(kw in lname for kw in self.QUEST_KEYWORDS):
                continue
            seen.add(lname)
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.QUEST,
                    name=rname,
                    source=source,
                    biome=_as_str(r.get("theme", "generic")),
                    min_level=_as_int(r.get("min_level", 1)),
                    max_level=_as_int(r.get("max_level", 9999)),
                    tags=_coerce_tags(r) + ["quest"],
                    attributes={
                        "theme": _as_str(r.get("theme", "generic")),
                        "difficulty": _as_str(r.get("difficulty", "medium")),
                        "style": "linear",
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
            if cat not in self.QUEST_CATEGORIES:
                continue
            seen.add(lname)
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.QUEST,
                    name=name,
                    source=source,
                    biome=_as_str(s.get("biome", "generic")),
                    min_level=_as_int(s.get("min_level", 1)),
                    max_level=_as_int(s.get("max_level", 9999)),
                    tags=_coerce_tags(s) + ["quest"],
                    attributes={
                        "theme": _as_str(s.get("theme", "generic")),
                        "difficulty": _as_str(s.get("difficulty", "medium")),
                        "style": cat,
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
