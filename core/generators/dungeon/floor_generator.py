from dataclasses import dataclass, field
from typing import List, Dict

from .room_generator import Room, RoomType, RoomGenerator
from .corridor_generator import CorridorGenerator
from .boss_generator import BossGenerator
from .quest_generator import QuestGenerator
from .shortcut_generator import ShortcutGenerator
from .respawn_generator import RespawnGenerator
from .cave_generator import CaveGenerator


@dataclass
class Floor:
    level: int
    width: int
    height: int
    rooms: List[Room] = field(default_factory=list)
    corridors: List[List[tuple[int, int]]] = field(default_factory=list)
    boss_rooms: List[Room] = field(default_factory=list)
    quest_rooms: List[Room] = field(default_factory=list)
    shortcuts: List[Dict[str, object]] = field(default_factory=list)
    spawns: List[Dict[str, object]] = field(default_factory=list)
    cave_tiles: List[tuple[int, int]] = field(default_factory=list)
    room_map: List[List[int]] = field(default_factory=list)


class FloorGenerator:
    def __init__(self, theme: Dict[str, List[int]], style: str):
        self.theme = theme
        self.style = style

    def create_floors(self, floor_count: int) -> List[Floor]:
        floors = []
        for level in range(floor_count):
            floor = Floor(level=-level, width=40, height=40)
            if self.style in ("roshamuul", "ice", "dragon", "ancient"):
                CaveGenerator().carve_cave(floor)
                floor.rooms = [Room(name="Cave Vault", type="CombatRoom", x=2, y=2, width=36, height=36)]
            else:
                self._build_rooms_and_corridors(floor)
            floor.boss_rooms = BossGenerator().place_boss_room(floor, self.theme)
            floor.quest_rooms = QuestGenerator().place_quest_room(floor, self.theme)
            floor.shortcuts = ShortcutGenerator().create_shortcuts(floor)
            floor.spawns = RespawnGenerator().create_respawn_points(floor)
            floors.append(floor)
        return floors

    def _build_rooms_and_corridors(self, floor: Floor) -> None:
        floor.rooms = RoomGenerator().generate_rooms(floor.width, floor.height)
        floor.corridors = CorridorGenerator().connect_rooms(floor.rooms)
