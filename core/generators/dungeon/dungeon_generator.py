from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict

from .floor_generator import FloorGenerator, Floor
from .room_generator import Room


@dataclass
class Shortcut:
    type: str
    from_coord: tuple[int, int]
    to_coord: tuple[int, int]
    description: str


@dataclass
class RespawnPoint:
    x: int
    y: int
    z: int
    radius: int
    type: str = "Spawn"


@dataclass
class Dungeon:
    name: str
    theme: str
    floors: List[Floor] = field(default_factory=list)
    rooms: List[Room] = field(default_factory=list)
    corridors: List[List[tuple[int, int]]] = field(default_factory=list)
    bosses: List[Room] = field(default_factory=list)
    quests: List[Room] = field(default_factory=list)
    spawns: List[Dict[str, object]] = field(default_factory=list)
    shortcuts: List[Shortcut] = field(default_factory=list)


class DungeonGenerator:
    DUNGEON_STYLES = [
        "issavi",
        "roshamuul",
        "library",
        "cobra",
        "falcon",
        "soulwar",
        "ice",
        "dragon",
    ]

    def __init__(self, style: str = "issavi", min_level: int = 50, max_level: int = 150):
        self.style = style.lower()
        self.min_level = min_level
        self.max_level = max_level
        self.template = self._load_theme_template(self.style)
        self.dungeon = self._build_dungeon()

    @classmethod
    def from_prompt(cls, prompt: str) -> "DungeonGenerator":
        style = cls._parse_style(prompt)
        min_level, max_level = cls._parse_level_range(prompt)
        return cls(style=style, min_level=min_level, max_level=max_level)

    @staticmethod
    def _parse_style(prompt: str) -> str:
        lower = prompt.lower()
        for style in DungeonGenerator.DUNGEON_STYLES:
            if style in lower:
                return style
        if "ros" in lower:
            return "roshamuul"
        if "library" in lower:
            return "library"
        return "issavi"

    @staticmethod
    def _parse_level_range(prompt: str) -> tuple[int, int]:
        numbers = re.findall(r"\d+", prompt)
        if len(numbers) >= 2:
            return int(numbers[0]), int(numbers[1])
        if len(numbers) == 1:
            value = int(numbers[0])
            return value, value + 50
        return 300, 500

    def _load_theme_template(self, style: str) -> Dict[str, List[int]]:
        template_path = Path(__file__).resolve().parents[2] / "templates" / "dungeons" / f"{style}.json"
        if template_path.exists():
            try:
                return json.loads(template_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        return {
            "floors": [415, 416],
            "walls": [1495, 1496],
            "decorations": [2150, 2151],
            "monsters": ["Demon", "Vampire"],
            "bosses": ["Dragon", "Hydra"],
        }

    def _build_dungeon(self) -> Dungeon:
        floors = self._choose_floor_count()
        floor_generator = FloorGenerator(self.template, self.style)
        built_floors = floor_generator.create_floors(floors)
        dungeon = Dungeon(
            name=f"{self.style.capitalize()} Dungeon",
            theme=self.style,
            floors=built_floors,
        )
        dungeon.rooms = [room for floor in built_floors for room in floor.rooms if isinstance(room, Room)]
        dungeon.corridors = [corridor for floor in built_floors for corridor in floor.corridors]
        dungeon.bosses = [boss for floor in built_floors for boss in floor.boss_rooms]
        dungeon.quests = [quest for floor in built_floors for quest in floor.quest_rooms]
        dungeon.shortcuts = [Shortcut(
            type=shortcut["type"],
            from_coord=shortcut["from"],
            to_coord=shortcut["to"],
            description=shortcut["description"],
        ) for floor in built_floors for shortcut in floor.shortcuts]
        dungeon.spawns = [spawn for floor in built_floors for spawn in floor.spawns]
        return dungeon

    def _choose_floor_count(self) -> int:
        if self.max_level >= 500:
            return 4
        if self.max_level >= 400:
            return 3
        return 2

    def generate_lua(self, description: str) -> str:
        lines: List[str] = [
            "if not app.hasMap() then",
            "  return",
            "end",
            "\napp.transaction(function(map)",
            "  local z = 7",
            "  local function tileAt(x, y, z)",
            "    return map:getOrCreateTile(x, y, z)",
            "  end",
        ]

        floor_index = 0
        for floor in self.dungeon.floors:
            z_level = floor.level
            floor_ground = self.template.get("floors", [415])[0]
            wall_id = self.template.get("walls", [1495])[0]
            deco_id = self.template.get("decorations", [2150])[0]
            boss_monster = self.template.get("bosses", ["Dragon"])[0]

            lines.append(f"  -- Floor {z_level}")
            for room in floor.rooms:
                lines.append(f"  -- {room.name} [{room.type}]")
                for dx in range(room.width):
                    for dy in range(room.height):
                        x = room.x + dx
                        y = room.y + dy
                        lines.append(f"  tileAt({x}, {y}, z + {z_level}).ground = {floor_ground}")
                lines.append(f"  for ix = {room.x}, {room.x + room.width - 1} do")
                lines.append(f"    tileAt(ix, {room.y}, z + {z_level}):borderize()")
                lines.append(f"    tileAt(ix, {room.y + room.height - 1}, z + {z_level}):borderize()")
                lines.append("  end")
                lines.append(f"  for iy = {room.y}, {room.y + room.height - 1} do")
                lines.append(f"    tileAt({room.x}, iy, z + {z_level}):borderize()")
                lines.append(f"    tileAt({room.x + room.width - 1}, iy, z + {z_level}):borderize()")
                lines.append("  end")
                if room.type == "BossRoom":
                    cx, cy = room.center()
                    lines.append(f"  tileAt({cx}, {cy}, z + {z_level}):setCreature(\"{boss_monster}\", 120, Direction.SOUTH)")
                    lines.append(f"  tileAt({cx}, {cy - 1}, z + {z_level}):addItem({deco_id})")
                if room.type == "TreasureRoom":
                    lines.append(f"  tileAt({room.x + 1}, {room.y + 1}, z + {z_level}):addItem({deco_id})")
                if room.type == "QuestRoom":
                    lines.append(f"  tileAt({room.x + 2}, {room.y + 2}, z + {z_level}):addItem({wall_id})")

            if getattr(floor, 'cave_tiles', None):
                for x, y in floor.cave_tiles:
                    lines.append(f"  tileAt({x}, {y}, z + {z_level}).ground = {floor_ground}")
                lines.append(f"  -- Cave floor with cellular layout ({len(floor.cave_tiles)} tiles)")
            else:
                for corridor in floor.corridors:
                    for (x, y) in corridor:
                        lines.append(f"  tileAt({x}, {y}, z + {z_level}).ground = {floor_ground}")
                        lines.append(f"  tileAt({x}, {y}, z + {z_level}):borderize()")

            for spawn in floor.spawns:
                lines.append(f"  tileAt({spawn['x']}, {spawn['y']}, z + {spawn['z']}):setSpawn({spawn['radius']})")

            floor_index += 1

        lines.append("end)")
        return "\n".join(lines)

    def supports_prompt(self, prompt: str) -> bool:
        lower = prompt.lower()
        return "dungeon" in lower or any(style in lower for style in self.DUNGEON_STYLES)
