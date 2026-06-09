from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.world.structure import Structure


@dataclass
class QuestZoneExpansionResult:
    """Result of quest zone expansion."""
    zones_created: int = 0
    tiles_added: int = 0
    npcs_placed: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zones_created": self.zones_created,
            "tiles_added": self.tiles_added,
            "npcs_placed": self.npcs_placed,
            "details": self.details,
        }


QUEST_THEMES = [
    {
        "name": "temple",
        "ground": 813,
        "monsters": ["Skeleton", "Ghoul", "Mummy"],
        "spawn_count": 4,
        "description": "Ancient temple with undead guardians",
    },
    {
        "name": "catacombs",
        "ground": 818,
        "monsters": ["Vampire", "Banshee", "Mummy"],
        "spawn_count": 5,
        "description": "Dark catacombs with powerful undead",
    },
    {
        "name": "tower",
        "ground": 813,
        "monsters": ["Warlock", "Nightmare", "Diabolic Imp"],
        "spawn_count": 3,
        "description": "Wizard tower with arcane guardians",
    },
    {
        "name": "fortress",
        "ground": 814,
        "monsters": ["Orc", "Orc", "Orc Shaman", "Orc Berserker"],
        "spawn_count": 6,
        "description": "Orc fortress to conquer",
    },
]


class QuestZoneExpander:
    """
    Creates quest zones and mini dungeons.

    Capabilities:
      - Generates themed quest areas
      - Creates mini dungeon layouts
      - Places quest-relevant NPCs and objects
      - Adds reward structures
    """

    ZONE_SIZE = 12
    MAX_ZONES = 3

    def expand(self, world: WorldModel,
               max_zones: int = 3) -> QuestZoneExpansionResult:
        """
        Create quest zones adjacent to existing content.

        Args:
            world: WorldModel to expand in-place.
            max_zones: Maximum quest zones to create.

        Returns:
            QuestZoneExpansionResult with details.
        """
        result = QuestZoneExpansionResult()

        bounds = world._calculate_bounds()
        if not bounds:
            return result

        created = 0
        for i in range(min(max_zones, self.MAX_ZONES)):
            theme = QUEST_THEMES[i % len(QUEST_THEMES)]
            position = self._find_quest_position(world, bounds, i)

            if position is None:
                continue

            tiles, npcs = self._generate_quest_zone(
                world, position[0], position[1], theme, i
            )

            if tiles > 0:
                created += 1
                result.zones_created += 1
                result.tiles_added += tiles
                result.npcs_placed += npcs
                result.details.append({
                    "theme": theme["name"],
                    "position": f"{position[0]},{position[1]}",
                    "description": theme["description"],
                    "tiles": tiles,
                })

        return result

    def _find_quest_position(self, world: WorldModel,
                             bounds: Dict[str, int],
                             index: int) -> Optional[Tuple[int, int]]:
        """Find a position for a quest zone."""
        offset = 15 + index * (self.ZONE_SIZE + 10)
        candidates = [
            (bounds["max_x"] + offset, bounds["min_y"] + index * 20),
            (bounds["min_x"] - self.ZONE_SIZE - offset,
             bounds["min_y"] + index * 20),
            (bounds["max_x"] + offset,
             bounds["max_y"] - self.ZONE_SIZE - index * 20),
        ]

        for x, y in candidates:
            clear = True
            for dx in range(self.ZONE_SIZE):
                for dy in range(self.ZONE_SIZE):
                    if world.has_tile(x + dx, y + dy, 7):
                        clear = False
                        break
                if not clear:
                    break
            if clear:
                return (x, y)

        return None

    def _generate_quest_zone(self, world: WorldModel,
                             qx: int, qy: int,
                             theme: Dict[str, Any],
                             index: int) -> Tuple[int, int]:
        """
        Generate a quest zone with themed tiles and encounters.

        Returns:
            Tuple of (tiles_added, npcs_placed).
        """
        size = self.ZONE_SIZE
        ground = theme["ground"]
        monsters = theme["monsters"]
        zone_name = f"quest_{theme['name']}_{index}"

        tiles_added = 0
        npcs_placed = 0
        spawn_idx = 0

        # Create outer walls and inner floor
        for x in range(qx, qx + size):
            for y in range(qy, qy + size):
                if world.has_tile(x, y, 7):
                    continue

                is_edge = (
                    x == qx or x == qx + size - 1 or
                    y == qy or y == qy + size - 1
                )

                tile = Tile(x=x, y=y, z=7, ground=ground, zone=zone_name)

                # Place monster spawns inside
                if not is_edge:
                    if (x + y * 3) % 7 == 0 and spawn_idx < theme["spawn_count"]:
                        monster = monsters[spawn_idx % len(monsters)]
                        tile.spawn = Spawn(
                            monster=monster, respawn=120, radius=3,
                        )
                        spawn_idx += 1

                world.set_tile(tile)
                tiles_added += 1

        # Create entrance
        entrance_x = qx + size // 2
        entrance_tile = world.get_tile(entrance_x, qy, 7)
        if entrance_tile is not None:
            entrance_tile.ground = ground

        # Place a reward structure at center
        center_x = qx + size // 2
        center_y = qy + size // 2
        reward = Structure(
            name=f"{zone_name}_reward",
            category="quest_reward",
            x=center_x - 1, y=center_y - 1, z=7,
            width=3, height=3,
            tile_count=9,
            tags=["quest", "reward", theme["name"]],
        )
        world.add_structure(reward)

        # Register quest region
        region = Region(
            name=zone_name,
            theme=theme["name"],
            min_level=50 + index * 100,
            max_level=200 + index * 100,
            tags=["quest", "auto_generated", theme["name"]],
        )
        world.add_region(region)

        return tiles_added, npcs_placed