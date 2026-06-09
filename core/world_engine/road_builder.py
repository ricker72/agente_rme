from __future__ import annotations

from typing import Dict, List


class RoadBuilder:
    def build(self, road_plan: Dict[str, object]) -> Dict[str, object]:
        return {
            "from": road_plan.get("from"),
            "to": road_plan.get("to"),
            "type": road_plan.get("type", "road"),
            "path": road_plan.get("path", []),
        }

    def connect(self, start: Dict[str, int], end: Dict[str, int]) -> Dict[str, object]:
        points = []
        x = start["x"]
        y = start["y"]
        while x != end["x"]:
            points.append({"x": x, "y": y})
            x += 1 if end["x"] > x else -1
        while y != end["y"]:
            points.append({"x": x, "y": y})
            y += 1 if end["y"] > y else -1
        points.append({"x": end["x"], "y": end["y"]})
        return {"path": points, "type": "road"}
