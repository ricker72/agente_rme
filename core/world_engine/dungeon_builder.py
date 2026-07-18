from __future__ import annotations

from typing import Dict, List


class DungeonBuilder:
    def build(self, dungeon_plan: Dict[str, object]) -> Dict[str, object]:
        return {
            "name": dungeon_plan.get("name"),
            "theme": dungeon_plan.get("theme"),
            "floors": dungeon_plan.get("floors"),
            "difficulty": dungeon_plan.get("difficulty"),
            "bosses": dungeon_plan.get("bosses", []),
            "quests": dungeon_plan.get("quests", []),
            "connections": dungeon_plan.get("connections", []),
        }

    def room_layout(self, dungeon_plan: Dict[str, object]) -> List[Dict[str, object]]:
        return [{"room_type": "boss_room", "size": [10, 10]}]
