from collections import deque
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class RoomAnalysis:
    width: int
    height: int
    area: int
    connectivity: int
    type: str
    bounds: Tuple[int, int, int, int]


class RoomAnalyzer:
    def detect_rooms(
        self, grid: List[List[int]], passable_ids: List[int]
    ) -> List[RoomAnalysis]:
        height = len(grid)
        width = len(grid[0]) if height > 0 else 0
        visited = [[False] * width for _ in range(height)]
        rooms: List[RoomAnalysis] = []

        for y in range(height):
            for x in range(width):
                if visited[y][x] or grid[y][x] not in passable_ids:
                    continue
                bounds = self._flood_fill(grid, visited, x, y, passable_ids)
                room = self._measure_room(bounds)
                if room.area > 8:
                    rooms.append(room)
        return rooms

    def _flood_fill(
        self,
        grid: List[List[int]],
        visited: List[List[bool]],
        start_x: int,
        start_y: int,
        passable_ids: List[int],
    ) -> Tuple[int, int, int, int]:
        width = len(grid[0])
        height = len(grid)
        q = deque([(start_x, start_y)])
        visited[start_y][start_x] = True
        x_min = x_max = start_x
        y_min = y_max = start_y
        area = 0

        while q:
            x, y = q.popleft()
            area += 1
            x_min = min(x_min, x)
            x_max = max(x_max, x)
            y_min = min(y_min, y)
            y_max = max(y_max, y)
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if (
                    0 <= nx < width
                    and 0 <= ny < height
                    and not visited[ny][nx]
                    and grid[ny][nx] in passable_ids
                ):
                    visited[ny][nx] = True
                    q.append((nx, ny))
        return x_min, y_min, x_max, y_max

    def _measure_room(self, bounds: Tuple[int, int, int, int]) -> RoomAnalysis:
        x_min, y_min, x_max, y_max = bounds
        width = x_max - x_min + 1
        height = y_max - y_min + 1
        area = width * height
        connectivity = (width + height) // 2
        room_type = self._classify_room(width, height)
        return RoomAnalysis(
            width=width,
            height=height,
            area=area,
            connectivity=connectivity,
            type=room_type,
            bounds=bounds,
        )

    def _classify_room(self, width: int, height: int) -> str:
        if width * height >= 200:
            return "Arena"
        if width * height >= 80:
            return "CombatRoom"
        if width * height >= 40:
            return "HallwayRoom"
        return "SmallRoom"
