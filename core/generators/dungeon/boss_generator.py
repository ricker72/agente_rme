from typing import List

from .room_generator import Room


class BossGenerator:
    def place_boss_room(self, floor: "Floor", theme: dict) -> List[Room]:
        if not floor.rooms:
            return []
        boss_room = floor.rooms[-1]
        boss_room.type = "BossRoom"
        boss_room.name = "Boss Arena"
        return [boss_room]
