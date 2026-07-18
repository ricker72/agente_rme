from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class RoutePlan:
    start: str
    end: str
    route_type: str
    path: List[Dict[str, int]]
    length: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "start": self.start,
            "end": self.end,
            "route_type": self.route_type,
            "path": self.path,
            "length": self.length,
        }


class RoutePlanner:
    def plan_route(
        self,
        start: str,
        end: str,
        start_xy: Dict[str, int],
        end_xy: Dict[str, int],
        route_type: str = "road",
    ) -> RoutePlan:
        dx = abs(end_xy["x"] - start_xy["x"])
        dy = abs(end_xy["y"] - start_xy["y"])
        length = dx + dy
        path = []
        x, y = start_xy["x"], start_xy["y"]
        step_x = 1 if end_xy["x"] >= x else -1
        step_y = 1 if end_xy["y"] >= y else -1
        for _ in range(dx):
            path.append({"x": x, "y": y})
            x += step_x
        for _ in range(dy):
            path.append({"x": x, "y": y})
            y += step_y
        path.append({"x": end_xy["x"], "y": end_xy["y"]})
        return RoutePlan(
            start=start, end=end, route_type=route_type, path=path, length=length
        )
