from typing import List, Tuple

from .room_generator import Room


class CorridorGenerator:
    @staticmethod
    def connect_rooms(rooms: List[Room]) -> List[List[Tuple[int, int]]]:
        corridors: List[List[Tuple[int, int]]] = []
        sorted_rooms = sorted(rooms, key=lambda room: room.center())
        for first, second in zip(sorted_rooms, sorted_rooms[1:]):
            corridors.append(CorridorGenerator._create_corridor(first.center(), second.center()))
        return corridors

    @staticmethod
    def _create_corridor(a: Tuple[int, int], b: Tuple[int, int]) -> List[Tuple[int, int]]:
        path: List[Tuple[int, int]] = []
        x1, y1 = a
        x2, y2 = b
        x, y = x1, y1
        while x != x2:
            path.append((x, y))
            x += 1 if x2 > x else -1
        while y != y2:
            path.append((x, y))
            y += 1 if y2 > y else -1
        path.append((x2, y2))
        return path
