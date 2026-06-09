from __future__ import annotations

from typing import Dict, List


class QuestBuilder:
    def build(self, zone_plan: Dict[str, object]) -> Dict[str, object]:
        return {
            "name": f"Explore {zone_plan.get('name')}",
            "type": "exploration",
            "objective": zone_plan.get("purpose", "explore"),
            "area": {
                "x": zone_plan.get("x"),
                "y": zone_plan.get("y"),
                "width": zone_plan.get("width"),
                "height": zone_plan.get("height"),
            },
            "reward": "experience",
        }

    def build_boss_quest(self, boss_plan: Dict[str, object]) -> Dict[str, object]:
        return {
            "name": f"Defeat the {boss_plan.get('name')}",
            "type": "boss",
            "target": boss_plan.get("name"),
            "reward": "loot",
        }
