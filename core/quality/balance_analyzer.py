from __future__ import annotations

from collections import Counter
from typing import Any, Dict


class BalanceAnalyzer:
    def analyze(self, world_model: Any) -> Dict[str, object]:
        spawns = getattr(world_model, "spawns", []) or []
        monster_names = [
            spawn.get("monster") for spawn in spawns if spawn.get("monster")
        ]
        frequency = Counter(monster_names)
        distinct = len(frequency)
        top_share = max(frequency.values(), default=0) / max(len(monster_names), 1)

        return {
            "spawn_count": len(spawns),
            "distinct_monsters": distinct,
            "top_monster_share": round(top_share, 2),
            "monster_balance": "good" if top_share < 0.35 else "poor",
        }
