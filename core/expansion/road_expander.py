from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.region import Region
from core.world.structure import Structure


@dataclass
class RoadExpansionResult:
    """Result of road expansion operation."""

    roads_created: int = 0
    tiles_added: int = 0
    shortcuts_created: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "roads_created": self.roads_created,
            "tiles_added": self.tiles_added,
            "shortcuts_created": self.shortcuts_created,
            "details": self.details,
        }


# Ground IDs for roads
ROAD_GROUND = 816  # Sand/road tile
PATH_GROUND = 814  # Dirt path


class RoadExpander:
    """
    Creates roads and shortcuts between regions.

    Capabilities:
      - Detects region pairs that need connections
      - Creates road paths between regions
      - Generates shortcuts through empty areas
      - Adds road structures (bridges, crossings)
    """

    ROAD_WIDTH = 3
    MIN_DISTANCE_FOR_ROAD = 30

    def expand(
        self, world: WorldModel, create_shortcuts: bool = True
    ) -> RoadExpansionResult:
        """
        Create roads and shortcuts between regions.

        Args:
            world: WorldModel to expand in-place.
            create_shortcuts: Whether to create shortcut paths.

        Returns:
            RoadExpansionResult with details.
        """
        result = RoadExpansionResult()

        regions = world.regions
        if len(regions) < 2:
            return result

        # Create roads between region pairs
        for i in range(len(regions)):
            for j in range(i + 1, len(regions)):
                r1 = regions[i]
                r2 = regions[j]

                center1 = self._region_center(world, r1)
                center2 = self._region_center(world, r2)

                if center1 is None or center2 is None:
                    continue

                dist = (
                    (center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2
                ) ** 0.5

                if dist < self.MIN_DISTANCE_FOR_ROAD:
                    continue

                tiles = self._create_road(world, center1, center2)
                if tiles > 0:
                    result.roads_created += 1
                    result.tiles_added += tiles
                    result.details.append(
                        {
                            "from": r1.name,
                            "to": r2.name,
                            "tiles": tiles,
                            "distance": round(dist, 1),
                        }
                    )

        # Create shortcuts through empty areas
        if create_shortcuts and len(regions) >= 2:
            self._create_shortcuts(world, result)

        return result

    def _region_center(
        self, world: WorldModel, region: Region
    ) -> Optional[Tuple[int, int]]:
        """Calculate the center of a region."""
        tiles = [t for t in world.tiles.values() if t.zone == region.name]
        if not tiles:
            return None
        cx = sum(t.x for t in tiles) // len(tiles)
        cy = sum(t.y for t in tiles) // len(tiles)
        return (cx, cy)

    def _create_road(
        self, world: WorldModel, start: Tuple[int, int], end: Tuple[int, int]
    ) -> int:
        """Create a road (multi-tile wide path) between two points."""
        tiles_added = 0
        x, y = start
        ex, ey = end

        # Horizontal segment
        step_x = 1 if ex > x else -1
        while x != ex:
            for w in range(-1, 2):  # 3-wide road
                if not world.has_tile(x, y + w, 7):
                    tile = Tile(x=x, y=y + w, z=7, ground=ROAD_GROUND)
                    world.set_tile(tile)
                    tiles_added += 1
            x += step_x

        # Vertical segment
        step_y = 1 if ey > y else -1
        while y != ey:
            for w in range(-1, 2):
                if not world.has_tile(x + w, y, 7):
                    tile = Tile(x=x + w, y=y, z=7, ground=ROAD_GROUND)
                    world.set_tile(tile)
                    tiles_added += 1
            y += step_y

        return tiles_added

    def _create_shortcuts(self, world: WorldModel, result: RoadExpansionResult) -> None:
        """Create shortcut paths through empty areas."""
        regions = world.regions
        if len(regions) < 2:
            return

        # Find two distant regions
        max_dist = 0
        best_pair = None

        for i in range(len(regions)):
            for j in range(i + 1, len(regions)):
                c1 = self._region_center(world, regions[i])
                c2 = self._region_center(world, regions[j])
                if c1 is None or c2 is None:
                    continue
                dist = ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5
                if dist > max_dist:
                    max_dist = dist
                    best_pair = (c1, c2, regions[i].name, regions[j].name)

        if best_pair is None or max_dist < 50:
            return

        c1, c2, name1, name2 = best_pair
        mid_x = (c1[0] + c2[0]) // 2
        mid_y = (c1[1] + c2[1]) // 2

        # Create a small waypoint at the midpoint
        shortcut_tiles = 0
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                x, y = mid_x + dx, mid_y + dy
                if not world.has_tile(x, y, 7):
                    tile = Tile(x=x, y=y, z=7, ground=PATH_GROUND)
                    world.set_tile(tile)
                    shortcut_tiles += 1

        if shortcut_tiles > 0:
            result.shortcuts_created += 1
            result.tiles_added += shortcut_tiles
            result.details.append(
                {
                    "action": "shortcut",
                    "from": name1,
                    "to": name2,
                    "midpoint": f"{mid_x},{mid_y}",
                    "tiles": shortcut_tiles,
                }
            )

            # Register as structure
            structure = Structure(
                name=f"shortcut_{result.shortcuts_created}",
                category="shortcut",
                x=mid_x - 2,
                y=mid_y - 2,
                z=7,
                width=5,
                height=5,
                tile_count=shortcut_tiles,
                tags=["road", "shortcut"],
            )
            world.add_structure(structure)
