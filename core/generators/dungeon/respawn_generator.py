from __future__ import annotations

from typing import List, Dict


class RespawnGenerator:
    def create_respawn_points(self, floor) -> List[Dict[str, object]]:
        points: List[Dict[str, object]] = []
        points.append({"x": 6, "y": 6, "z": 0, "radius": 3, "type": "Spawn"})
        points.append({"x": 32, "y": 32, "z": 0, "radius": 3, "type": "Spawn"})
        return points
