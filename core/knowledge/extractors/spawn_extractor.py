"""
SpawnExtractor — extract monster spawn entries from a world.

Groups individual spawns by monster family when no zone is given, and by
zone when a zone is present.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List

from ..models import EntryType, KnowledgeEntry
from .base_extractor import BaseExtractor, _as_int, _as_list, _as_str


class SpawnExtractor(BaseExtractor):
    NAME = "spawn"

    def extract(self, world: Dict[str, Any], source: str = "") -> List[KnowledgeEntry]:
        entries: List[KnowledgeEntry] = []
        seen: set = set()

        # 1) Group by (zone, monster) pair -> a stable spawn entry
        pair_index: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "count": 0,
                "level_min": 9999,
                "level_max": 0,
                "x_sum": 0,
                "y_sum": 0,
                "n_pos": 0,
                "biome": "generic",
            }
        )
        # 2) Group by monster alone (no zone info)
        monster_index: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"count": 0, "level_min": 9999, "level_max": 0, "zones": set()}
        )

        spawns = _as_list(world.get("spawns"))
        if not spawns:
            return entries

        for s in spawns:
            if not isinstance(s, dict):
                continue
            monster = _as_str(s.get("monster") or s.get("name") or s.get("type"))
            zone = _as_str(s.get("zone") or s.get("region") or s.get("area"))
            level = _as_int(s.get("level", s.get("monster_level", 0)))
            biome = _as_str(
                s.get("biome", world.get("meta", {}).get("theme", "generic"))
            )
            if not monster:
                continue
            monster_index[monster]["count"] += 1
            if level:
                m = monster_index[monster]
                m["level_min"] = min(m["level_min"], level) if m["level_min"] else level
                m["level_max"] = max(m["level_max"], level)
            if zone:
                monster_index[monster]["zones"].add(zone.lower())
            if zone:
                key = f"{zone.lower()}::{monster.lower()}"
                rec = pair_index[key]
                rec["count"] += 1
                rec["biome"] = biome
                if level:
                    rec["level_min"] = min(rec["level_min"] or level, level)
                    rec["level_max"] = max(rec["level_max"], level)
                if "x" in s and "y" in s:
                    try:
                        rec["x_sum"] += int(s.get("x", 0))
                        rec["y_sum"] += int(s.get("y", 0))
                        rec["n_pos"] += 1
                    except (TypeError, ValueError):
                        pass
            else:
                key = f"__nozone__{monster.lower()}"
                rec = pair_index[key]
                rec["count"] += 1
                rec["biome"] = biome
                if level:
                    rec["level_min"] = min(rec["level_min"] or level, level)
                    rec["level_max"] = max(rec["level_max"], level)

        for key, rec in pair_index.items():
            if "::" not in key:
                continue
            zone_lname, monster_lname = key.split("::", 1)
            monster = monster_lname.replace("_", " ").title()
            zone = zone_lname.replace("_", " ").title()
            name = f"{monster} @ {zone}"
            if name.lower() in seen:
                continue
            seen.add(name.lower())
            min_lv = rec["level_min"] if rec["level_min"] != 9999 else 0
            max_lv = rec["level_max"]
            attrs = {
                "monster": monster,
                "zone": zone,
                "count": rec["count"],
                "biome": rec["biome"],
                "difficulty": _difficulty_for(max_lv or min_lv),
            }
            if rec["n_pos"] > 0:
                attrs["centroid"] = (
                    int(rec["x_sum"] / rec["n_pos"]),
                    int(rec["y_sum"] / rec["n_pos"]),
                )
            entries.append(
                KnowledgeEntry.build(
                    entry_type=EntryType.SPAWN,
                    name=name,
                    source=source,
                    biome=rec["biome"],
                    min_level=min_lv or 1,
                    max_level=max_lv or 9999,
                    tags=[rec["biome"], "spawn"] + ([zone] if zone else []),
                    attributes=attrs,
                )
            )

        # Emit a "global" entry per monster family if no zoned entries exist
        if not entries and monster_index:
            for monster, rec in monster_index.items():
                name = f"{monster.title()} Spawns"
                if name.lower() in seen:
                    continue
                seen.add(name.lower())
                min_lv = rec["level_min"] if rec["level_min"] != 9999 else 0
                max_lv = rec["level_max"]
                entries.append(
                    KnowledgeEntry.build(
                        entry_type=EntryType.SPAWN,
                        name=name,
                        source=source,
                        biome="generic",
                        min_level=min_lv or 1,
                        max_level=max_lv or 9999,
                        tags=["spawn"],
                        attributes={
                            "monster": monster.title(),
                            "count": rec["count"],
                            "difficulty": _difficulty_for(max_lv or min_lv),
                            "zones": sorted(rec["zones"]),
                        },
                    )
                )
        return entries


def _difficulty_for(level: int) -> str:
    if level >= 400:
        return "extreme"
    if level >= 250:
        return "hard"
    if level >= 150:
        return "medium"
    if level >= 80:
        return "easy"
    return "trivial"
