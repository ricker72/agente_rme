"""
HuntExtractor — extract hunt entries from a world.

A "hunt" is a region/zone whose name contains 'hunt', 'spawn', 'farm',
'cave', or 'sewers' — and that contains at least one spawn.
"""

from __future__ import annotations

from typing import Any, Dict, List

from ..models import EntryType, KnowledgeEntry
from .base_extractor import BaseExtractor, _as_int, _as_list, _as_str


class HuntExtractor(BaseExtractor):
    NAME = "hunt"

    HUNT_KEYWORDS = ("hunt", "spawn", "farm", "cave", "sewer", "dungeon", "lair", "-")
    CIRCULAR_HINTS = ("circular", "ring", "loop", "roshamuul", "arena")

    def extract(self, world: Dict[str, Any], source: str = "") -> List[KnowledgeEntry]:
        entries: List[KnowledgeEntry] = []
        seen: set = set()

        regions = _as_list(world.get("regions"))
        spawns = _as_list(world.get("spawns"))
        spawn_index = self._index_spawns(spawns)

        for r in regions:
            if not isinstance(r, dict):
                continue
            name = _as_str(r.get("name"))
            lname = name.lower()
            if not name or lname in seen:
                continue
            if not any(kw in lname for kw in self.HUNT_KEYWORDS):
                continue
            seen.add(lname)

            monsters = spawn_index.get(lname, []) or spawn_index.get(name, [])
            monster_names = sorted({_as_str(m) for m in monsters if m})
            tile_count = _count_tiles_in_region(world, lname)
            route = self._infer_route(lname, name, tile_count, monster_names)
            circular = (
                any(h in lname for h in self.CIRCULAR_HINTS) or route == "circular"
            )
            difficulty = self._infer_difficulty(
                int(r.get("max_level", 0)), int(r.get("min_level", 0))
            )
            entry = KnowledgeEntry.build(
                entry_type=EntryType.HUNT,
                name=name,
                source=source,
                biome=_as_str(
                    r.get("theme", world.get("meta", {}).get("theme", "generic"))
                ),
                min_level=_as_int(r.get("min_level", 1)),
                max_level=_as_int(r.get("max_level", 9999)),
                tags=_coerce_tags(r) + (["circular_route"] if circular else []),
                attributes={
                    "theme": _as_str(r.get("theme", "generic")),
                    "monsters": monster_names,
                    "spawn_density": _spawn_density(len(monsters), tile_count),
                    "route": route,
                    "circular": circular,
                    "layout": "circular" if circular else "linear",
                    "difficulty": difficulty,
                    "tile_count": tile_count,
                    "spawns": len(monsters),
                },
            )
            entries.append(entry)
        return entries

    def _index_spawns(self, spawns: List[Any]) -> Dict[str, List[str]]:
        out: Dict[str, List[str]] = {}
        for s in spawns:
            if not isinstance(s, dict):
                continue
            zone = _as_str(s.get("zone") or s.get("region") or s.get("area"))
            monster = _as_str(s.get("monster") or s.get("name") or s.get("type"))
            if not zone or not monster:
                continue
            out.setdefault(zone.lower(), []).append(monster)
        return out

    def _infer_route(
        self, lname: str, name: str, tile_count: int, monsters: List[str]
    ) -> str:
        if any(h in lname for h in self.CIRCULAR_HINTS):
            return "circular"
        if tile_count > 0 and len(monsters) >= max(3, tile_count // 4):
            return "circular"
        if any(s in lname for s in ("sewer", "lair", "cave")):
            return "branching"
        return "linear"

    def _infer_difficulty(self, max_level: int, min_level: int) -> str:
        # Use the average of the level band as the difficulty signal.
        avg = (max_level + min_level) / 2.0 if (max_level + min_level) else 0
        if avg >= 400:
            return "extreme"
        if avg >= 300:
            return "hard"
        if avg >= 200:
            return "medium"
        if avg >= 50:
            return "easy"
        return "trivial"


def _count_tiles_in_region(world: Dict[str, Any], region_lname: str) -> int:
    count = 0
    for t in _as_list(world.get("tiles")):
        if not isinstance(t, dict):
            continue
        zone = _as_str(t.get("zone") or t.get("region"))
        if zone and zone.lower() == region_lname:
            count += 1
    return count


def _spawn_density(spawns: int, tiles: int) -> float:
    if tiles <= 0:
        return 0.0
    return round(spawns / tiles, 4)


def _coerce_tags(obj: Dict[str, Any]) -> List[str]:
    raw = obj.get("tags") if isinstance(obj, dict) else None
    if isinstance(raw, list):
        return [str(t) for t in raw]
    if isinstance(raw, str):
        return [t.strip() for t in raw.split(",") if t.strip()]
    return []
