from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Road:
    name: str
    path: List[Tuple[int, int]]


class RoadGenerator:
    @staticmethod
    def path_between(a: Tuple[int, int], b: Tuple[int, int]) -> List[Tuple[int, int]]:
        points = []
        x1, y1 = a
        x2, y2 = b
        dx = 1 if x2 >= x1 else -1
        dy = 1 if y2 >= y1 else -1

        for x in range(x1, x2 + dx, dx):
            points.append((x, y1))
        for y in range(y1 + dy, y2 + dy, dy):
            points.append((x2, y))
        return points

    @staticmethod
    def connect_districts(districts: List["District"], center: Tuple[int, int]) -> List[Road]:
        roads: List[Road] = []
        plaza_points = []
        for district in districts:
            if district.type == "Market":
                continue
            road_name = f"Road to {district.name}"
            path = RoadGenerator.path_between(center, district.center())
            roads.append(Road(name=road_name, path=path))
            plaza_points.extend(path)

        # add an outer loop between the main districts to avoid dead ends
        sorted_districts = sorted(districts, key=lambda d: (d.x, d.y))
        for first, second in zip(sorted_districts, sorted_districts[1:]):
            path = RoadGenerator.path_between(first.center(), second.center())
            roads.append(Road(name=f"Connector {first.name} -> {second.name}", path=path))

        return roads
