from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.world.structure import Structure


@dataclass
class HuntExpansionResult:
    """Result of hunt expansion operation."""
    zones_created: List[str] = field(default_factory=list)
    tiles_added: int = 0
    spawns_added: int = 0
    regions_added: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zones_created": self.zones_created,
            "tiles_added": self.tiles_added,
            "spawns_added": self.spawns_added,
            "regions_added": self.regions_added,
            "details": self.details,
        }


# Monster pools by difficulty tier
HUNT_MONSTERS = {
    "easy": ["Rat", "Spider", "Troll", "Orc", "Skeleton"],
    "medium": ["Cyclops", "Vampire", "Banshee", "Lizard", "Dwarf"],
    "hard": ["Dragon", "Hydra", "Giant Spider", "Warlock", "Sea Serpent"],
    "very_hard": ["Dragon Lord", "Demon", "Serpent Spawn", "Medusa", "Behemoth"],
}

# Ground item IDs for different themes
GROUND_IDS = {
    "grass": 817,
    "cave": 818,
    "dirt": 814,
    "stone": 813,
    "hell": 820,
    "jungle": 819,
    "sand": 816,
    "snow": 821,
}


class HuntExpander:
    """
    Detects empty zones and generates new hunt areas.

    Capabilities:
      - Finds empty regions in the world with no spawns
      - Creates hunt zones with appropriate monsters
      - Adds ground tiles, spawn points, and region markers
      - Respects level-appropriate monster selection
    """

    MIN_EMPTY_TILES = 20
    DEFAULT_HUNT_SIZE = 15
    SPAWN_DENSITY = 0.15  # 15% of tiles get spawns
    MIN_LEVEL_TIERS = {
        "easy": 1, "medium": 80, "hard": 200, "very_hard": 400,
    }

    def expand(self, world: WorldModel,
               max_hunts: int = 3,
               theme: str = "cave") -> HuntExpansionResult:
        """
        Find empty areas and create new hunt zones.

        Args:
            world: WorldModel to expand in-place.
            max_hunts: Maximum number of hunt zones to create.
            theme: Theme for ground tiles.

        Returns:
            HuntExpansionResult with expansion details.
        """
        result = HuntExpansionResult()
        empty_areas = self._find_empty_areas(world)

        created = 0
        for area in empty_areas:
            if created >= max_hunts:
                break

            zone_name = f"auto_hunt_{created + 1}"
            level_tier = self._classify_area_size(area)

            tiles, spawns = self._generate_hunt_zone(
                world, area, zone_name, level_tier, theme
            )

            if tiles > 0:
                region = Region(
                    name=zone_name,
                    theme=theme,
                    min_level=self.MIN_LEVEL_TIERS.get(level_tier, 1),
                    max_level=self.MIN_LEVEL_TIERS.get(level_tier, 1) + 150,
                    tags=["hunt", "auto_generated", level_tier],
                )
                world.add_region(region)

                result.zones_created.append(zone_name)
                result.tiles_added += tiles
                result.spawns_added += spawns
                result.regions_added += 1
                result.details.append({
                    "name": zone_name,
                    "tier": level_tier,
                    "tiles": tiles,
                    "spawns": spawns,
                    "position": f"{area[0]},{area[1]}",
                })
                created += 1

        return result

    def _find_empty_areas(self, world: WorldModel) -> List[Tuple[int, int, int, int]]:
        """
        Find rectangular empty areas in the world.

        Returns:
            List of (x1, y1, x2, y2) bounding boxes of empty areas.
        """
        bounds = world._calculate_bounds()
        if not bounds:
            return []

        # Scan for large empty rectangles
        areas: List[Tuple[int, int, int, int]] = []
        step = self.DEFAULT_HUNT_SIZE
        min_x = bounds["min_x"]
        max_x = bounds["max_x"]
        min_y = bounds["min_y"]
        max_y = bounds["max_y"]

        # Look beyond current bounds for expansion space
        search_ranges = [
            (max_x + 5, max_x + 5 + step * 3, min_y, min_y + step * 3),
            (min_x - step * 3 - 5, min_x - 5, min_y, min_y + step * 3),
            (min_x, min_x + step * 3, max_y + 5, max_y + 5 + step * 3),
            (min_x, min_x + step * 3, min_y - step * 3 - 5, min_y - 5),
        ]

        for sx1, sx2, sy1, sy2 in search_ranges:
            empty_count = 0
            total = 0
            for x in range(sx1, sx2):
                for y in range(sy1, sy2):
                    total += 1
                    if not world.has_tile(x, y, 7):
                        empty_count += 1

            if total > 0 and empty_count / total > 0.8:
                areas.append((sx1, sy1, sx2, sy2))

        return areas[:5]

    def _classify_area_size(self, area: Tuple[int, int, int, int]) -> str:
        """Classify an area into a difficulty tier based on size."""
        width = area[2] - area[0]
        height = area[3] - area[1]
        area_size = width * height

        if area_size < 100:
            return "easy"
        elif area_size < 400:
            return "medium"
        elif area_size < 900:
            return "hard"
        return "very_hard"

    def _generate_hunt_zone(self, world: WorldModel,
                            area: Tuple[int, int, int, int],
                            zone_name: str,
                            tier: str,
                            theme: str) -> Tuple[int, int]:
        """
        Generate tiles and spawns for a hunt zone.

        Returns:
            Tuple of (tiles_added, spawns_added).
        """
        x1, y1, x2, y2 = area
        ground_id = GROUND_IDS.get(theme, GROUND_IDS["cave"])
        monsters = HUNT_MONSTERS.get(tier, HUNT_MONSTERS["medium"])

        tiles_added = 0
        spawns_added = 0
        spawn_idx = 0

        for x in range(x1, x2):
            for y in range(y1, y2):
                if not world.has_tile(x, y, 7):
                    tile = Tile(x=x, y=y, z=7, ground=ground_id, zone=zone_name)

                    # Add spawns at random-looking positions (deterministic)
                    if (x * 7 + y * 13) % max(1, int(1.0 / self.SPAWN_DENSITY)) == 0:
                        monster = monsters[spawn_idx % len(monsters)]
                        tile.spawn = Spawn(
                            monster=monster,
                            respawn=60,
                            radius=5,
                        )
                        spawn_idx += 1
                        spawns_added += 1

                    world.set_tile(tile)
                    tiles_added += 1

        # Add structure marker for the entrance
        entrance = Structure(
            name=f"{zone_name}_entrance",
            category="entrance",
            x=x1,
            y=y1,
            z=7,
            width=3,
            height=3,
            tile_count=9,
            tags=["hunt", "entrance", tier],
        )
        world.add_structure(entrance)

        return tiles_added, spawns_added