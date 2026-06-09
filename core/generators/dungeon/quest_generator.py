from typing import List

from .room_generator import Room


class QuestGenerator:
    def place_quest_room(self, floor: "Floor", theme: dict) -> List[Room]:
        if len(floor.rooms) < 4:
            return []
        quest_room = floor.rooms[len(floor.rooms) // 3]
        quest_room.type = "QuestRoom"
        quest_room.name = "Quest Chamber"
        return [quest_room]
