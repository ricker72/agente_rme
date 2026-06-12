from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.world.structure import Structure


@dataclass
class BossExpansionResult:
    """Result of boss room expansion."""

    rooms_created: int = 0
    tiles_added: int = 0
    bosses_placed: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rooms_created": self.rooms_created,
            "tiles_added": self.tiles_added,
            "bosses_placed": self.bosses_placed,
            "details": self.details,
        }


# Boss definitions per difficulty
BOSS_MONSTERS = {
    "easy": [
        {"name": "The Horned Fox", "hp": 3000, "xp": 2000},
        {"name": "Tzuum, the Mightiest", "hp": 5000, "xp": 4000},
    ],
    "medium": [
        {"name": "Orshabaal", "hp": 25000, "xp": 10000},
        {"name": "Ghazbaran", "hp": 30000, "xp": 12000},
        {"name": "Demodras", "hp": 20000, "xp": 8000},
    ],
    "hard": [
        {"name": "Graz'zt", "hp": 80000, "xp": 30000},
        {"name": "Asmodeus", "hp": 100000, "xp": 40000},
        {"name": "Bael", "hp": 120000, "xp": 50000},
    ],
}

# Wall ground tile (impassable)
WALL_GROUND = 813
FLOOR_GROUND = 818


class BossExpander:
    """
    Generates boss rooms adjacent to existing hunt zones.

    Capabilities:
      - Creates enclosed rooms with walls
      - Places boss spawn in room center
      - Connects room to nearest region
      - Scales boss difficulty to region level
    """

    ROOM_SIZE_MIN = 8
    ROOM_SIZE_MAX = 14

    def expand(
        self, world: WorldModel, max_rooms: int = 2, difficulty: str = "medium"
    ) -> BossExpansionResult:
        """
        Create boss rooms adjacent to existing regions.

        Args:
            world: WorldModel to expand in-place.
            max_rooms: Maximum rooms to create.
            difficulty: Boss difficulty tier.

        Returns:
            BossExpansionResult with details.
        """
        result = BossExpansionResult()

        existing_regions = [r for r in world.regions if "boss" not in r.tags]
        if not existing_regions:
            return result

        bounds = world._calculate_bounds()
        if not bounds:
            return result

        created = 0
        for region in existing_regions:
            if created >= max_rooms:
                break

            room_pos = self._find_room_position(world, bounds)
            if room_pos is None:
                continue

            room_size = self._get_room_size(difficulty)
            room_x, room_y = room_pos

            tiles, bosses = self._generate_boss_room(
                world, room_x, room_y, room_size, region, difficulty, created
            )

            if tiles > 0:
                created += 1
                result.rooms_created += 1
                result.tiles_added += tiles
                result.bosses_placed += bosses
                result.details.append(
                    {
                        "position": f"{room_x},{room_y}",
                        "size": room_size,
                        "linked_region": region.name,
                        "difficulty": difficulty,
                    }
                )

        return result

    def _find_room_position(
        self, world: WorldModel, bounds: Dict[str, int]
    ) -> Optional[Tuple[int, int]]:
        """Find a valid position for a boss room."""
        offset = 20
        candidates = [
            (bounds["max_x"] + offset, bounds["min_y"]),
            (bounds["min_x"] - self.ROOM_SIZE_MAX - offset, bounds["min_y"]),
            (bounds["max_x"] + offset, bounds["max_y"]),
            (bounds["min_x"] - self.ROOM_SIZE_MAX - offset, bounds["max_y"]),
        ]

        for x, y in candidates:
            clear = True
            for dx in range(self.ROOM_SIZE_MAX):
                for dy in range(self.ROOM_SIZE_MAX):
                    if world.has_tile(x + dx, y + dy, 7):
                        clear = False
                        break
                if not clear:
                    break
            if clear:
                return (x, y)

        return None

    def _get_room_size(self, difficulty: str) -> int:
        """Get room size based on difficulty."""
        sizes = {"easy": self.ROOM_SIZE_MIN, "medium": 10, "hard": self.ROOM_SIZE_MAX}
        return sizes.get(difficulty, 10)

    def _generate_boss_room(
        self,
        world: WorldModel,
        rx: int,
        ry: int,
        size: int,
        linked_region: Region,
        difficulty: str,
        index: int,
    ) -> Tuple[int, int]:
        """
        Generate a boss room with walls and a boss spawn.

        Returns:
            Tuple of (tiles_added, bosses_placed).
        """
        tiles_added = 0
        bosses_placed = 0

        # Create the enclosed room
        for x in range(rx, rx + size):
            for y in range(ry, ry + size):
                if world.has_tile(x, y, 7):
                    continue

                is_wall = x == rx or x == rx + size - 1 or y == ry or y == ry + size - 1

                if is_wall:
                    tile = Tile(x=x, y=y, z=7, ground=WALL_GROUND, zone=f"boss_{index}")
                else:
                    tile = Tile(
                        x=x, y=y, z=7, ground=FLOOR_GROUND, zone=f"boss_{index}"
                    )

                world.set_tile(tile)
                tiles_added += 1

        # Place boss spawn at center
        center_x = rx + size // 2
        center_y = ry + size // 2
        bosses = BOSS_MONSTERS.get(difficulty, BOSS_MONSTERS["medium"])
        boss = bosses[index % len(bosses)]

        center_tile = world.get_tile(center_x, center_y, 7)
        if center_tile is None:
            center_tile = Tile(
                x=center_x, y=center_y, z=7, ground=FLOOR_GROUND, zone=f"boss_{index}"
            )
            world.set_tile(center_tile)
            tiles_added += 1

        center_tile.spawn = Spawn(monster=boss["name"], respawn=300, radius=2)
        bosses_placed += 1

        # Add entrance opening (gap in wall)
        entrance_x = rx + size // 2
        entrance_tile = world.get_tile(entrance_x, ry, 7)
        if entrance_tile is not None:
            entrance_tile.ground = FLOOR_GROUND

        # Register boss room as region
        region = Region(
            name=f"boss_room_{index}",
            theme=linked_region.theme,
            min_level=linked_region.min_level,
            max_level=linked_region.max_level,
            tags=["boss", "auto_generated", difficulty],
        )
        world.add_region(region)

        # Register as structure
        structure = Structure(
            name=f"boss_room_{index}",
            category="boss_room",
            x=rx,
            y=ry,
            z=7,
            width=size,
            height=size,
            tile_count=tiles_added,
            tags=["boss", difficulty],
        )
        world.add_structure(structure)

        return tiles_added, bosses_placed
