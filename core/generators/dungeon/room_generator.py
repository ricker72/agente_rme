from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class Room:
    name: str
    type: str
    x: int
    y: int
    width: int
    height: int

    def center(self) -> Tuple[int, int]:
        return (self.x + self.width // 2, self.y + self.height // 2)


class RoomType:
    EntranceRoom = "EntranceRoom"
    HallwayRoom = "HallwayRoom"
    CombatRoom = "CombatRoom"
    EliteRoom = "EliteRoom"
    BossRoom = "BossRoom"
    TreasureRoom = "TreasureRoom"
    PuzzleRoom = "PuzzleRoom"
    QuestRoom = "QuestRoom"
    SecretRoom = "SecretRoom"
    RespawnRoom = "RespawnRoom"


class RoomGenerator:
    MIN_ROOM = 6
    MIN_SPLIT = 16

    def generate_rooms(self, width: int, height: int) -> List[Room]:
        leafs = self._bsp_split(0, 0, width, height)
        rooms: List[Room] = []
        for index, leaf in enumerate(leafs):
            x, y, w, h = leaf
            room_w = max(self.MIN_ROOM, w - 4)
            room_h = max(self.MIN_ROOM, h - 4)
            room_x = x + 2
            room_y = y + 2
            room_type = self._select_room_type(index, len(leafs))
            rooms.append(Room(
                name=f"Room {index + 1}",
                type=room_type,
                x=room_x,
                y=room_y,
                width=room_w,
                height=room_h,
            ))
        return rooms

    def _bsp_split(self, x: int, y: int, w: int, h: int) -> List[tuple[int, int, int, int]]:
        if w <= self.MIN_SPLIT or h <= self.MIN_SPLIT:
            return [(x, y, w, h)]

        if w > h:
            split = x + w // 2
            left = self._bsp_split(x, y, split - x, h)
            right = self._bsp_split(split, y, x + w - split, h)
        else:
            split = y + h // 2
            left = self._bsp_split(x, y, w, split - y)
            right = self._bsp_split(x, split, w, y + h - split)
        return left + right

    def _select_room_type(self, index: int, total: int) -> str:
        if index == 0:
            return RoomType.EntranceRoom
        if index == total - 1:
            return RoomType.BossRoom
        if index % 5 == 0:
            return RoomType.TreasureRoom
        if index % 4 == 0:
            return RoomType.EliteRoom
        return RoomType.CombatRoom
