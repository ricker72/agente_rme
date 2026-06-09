from __future__ import annotations

from typing import Dict, List


class BossBuilder:
    def build(self, boss_zone: Dict[str, object]) -> Dict[str, object]:
        return {
            "name": boss_zone.get("name"),
            "arena": {
                "x": boss_zone.get("x"),
                "y": boss_zone.get("y"),
                "width": boss_zone.get("width"),
                "height": boss_zone.get("height"),
            },
            "access": {
                "from": boss_zone.get("name"),
                "teleport": f"tp_{boss_zone.get('name').lower().replace(' ', '_')}",
            },
            "reward_room": {
                "x": boss_zone.get("x", 0) + 2,
                "y": boss_zone.get("y", 0) + 2,
            },
        }
