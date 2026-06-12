from __future__ import annotations

from typing import Dict


class WorldSizeEstimator:
    def estimate(self, world_plan: Dict[str, object]) -> Dict[str, int]:
        cities = world_plan.get("cities", [])
        dungeons = world_plan.get("dungeons", [])
        width = max((city.get("population", 0) // 10 for city in cities), default=40)
        height = max((city.get("population", 0) // 12 for city in cities), default=40)
        floors = max((dungeon.get("floors", 1) for dungeon in dungeons), default=1)
        return {
            "required_width": max(width, 80),
            "required_height": max(height, 80),
            "required_floors": max(floors, 1),
        }
