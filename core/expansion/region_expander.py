from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.region import Region


@dataclass
class RegionExpansionResult:
    """Result of region expansion operation."""

    regions_expanded: int = 0
    tiles_added: int = 0
    connections_made: int = 0
    details: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "regions_expanded": self.regions_expanded,
            "tiles_added": self.tiles_added,
            "connections_made": self.connections_made,
            "details": self.details,
        }


class RegionExpander:
    """
    Fills gaps between existing regions with transitional tiles.

    Capabilities:
      - Detects gaps between regions
      - Creates transitional zones
      - Adds connection paths between disconnected regions
      - Fills incomplete regions to rectangular bounds
    """

    GAP_FILL_GROUND = 814
    MAX_GAP_SIZE = 30

    def expand(
        self, world: WorldModel, fill_gaps: bool = True, connect_regions: bool = True
    ) -> RegionExpansionResult:
        """
        Expand and connect existing regions.

        Args:
            world: WorldModel to expand in-place.
            fill_gaps: Whether to fill gaps within regions.
            connect_regions: Whether to connect disconnected regions.

        Returns:
            RegionExpansionResult with details.
        """
        result = RegionExpansionResult()

        if fill_gaps:
            self._fill_incomplete_regions(world, result)

        if connect_regions and len(world.regions) >= 2:
            self._connect_regions(world, result)

        return result

    def _fill_incomplete_regions(
        self, world: WorldModel, result: RegionExpansionResult
    ) -> None:
        """Fill gaps within existing regions to make them more rectangular."""
        for region in world.regions:
            region_tiles = [t for t in world.tiles.values() if t.zone == region.name]

            if len(region_tiles) < 10:
                continue

            # Find bounds of region
            min_x = min(t.x for t in region_tiles)
            max_x = max(t.x for t in region_tiles)
            min_y = min(t.y for t in region_tiles)
            max_y = max(t.y for t in region_tiles)

            tiles_added = 0
            for x in range(min_x, max_x + 1):
                for y in range(min_y, max_y + 1):
                    if not world.has_tile(x, y, 7):
                        tile = Tile(
                            x=x, y=y, z=7, ground=self.GAP_FILL_GROUND, zone=region.name
                        )
                        world.set_tile(tile)
                        tiles_added += 1

            if tiles_added > 0:
                result.regions_expanded += 1
                result.tiles_added += tiles_added
                result.details.append(
                    {
                        "region": region.name,
                        "action": "fill_gaps",
                        "tiles_added": tiles_added,
                    }
                )

    def _connect_regions(
        self, world: WorldModel, result: RegionExpansionResult
    ) -> None:
        """Create paths between disconnected regions."""
        regions = world.regions
        if len(regions) < 2:
            return

        for i in range(len(regions)):
            for j in range(i + 1, len(regions)):
                r1 = regions[i]
                r2 = regions[j]

                center1 = self._region_center(world, r1)
                center2 = self._region_center(world, r2)

                if center1 is None or center2 is None:
                    continue

                # Skip if already close enough
                dist = (
                    (center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2
                ) ** 0.5
                if dist < 20:
                    continue

                # Check if already connected by tile proximity
                if self._regions_connected(world, r1, r2, threshold=5):
                    continue

                path_tiles = self._create_path(world, center1, center2, r1.name)
                if path_tiles > 0:
                    result.connections_made += 1
                    result.tiles_added += path_tiles
                    result.details.append(
                        {
                            "from": r1.name,
                            "to": r2.name,
                            "action": "connect",
                            "path_tiles": path_tiles,
                        }
                    )

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

    def _regions_connected(
        self, world: WorldModel, r1: Region, r2: Region, threshold: int = 5
    ) -> bool:
        """Check if two regions are close to each other."""
        tiles1 = [t for t in world.tiles.values() if t.zone == r1.name]
        tiles2 = [t for t in world.tiles.values() if t.zone == r2.name]

        for t1 in tiles1[:50]:
            for t2 in tiles2[:50]:
                if abs(t1.x - t2.x) <= threshold and abs(t1.y - t2.y) <= threshold:
                    return True
        return False

    def _create_path(
        self,
        world: WorldModel,
        start: Tuple[int, int],
        end: Tuple[int, int],
        zone_name: str,
    ) -> int:
        """Create a simple L-shaped path between two points."""
        tiles_added = 0
        x, y = start
        ex, ey = end

        # Horizontal then vertical
        step_x = 1 if ex > x else -1
        while x != ex:
            if not world.has_tile(x, y, 7):
                tile = Tile(x=x, y=y, z=7, ground=self.GAP_FILL_GROUND, zone=zone_name)
                world.set_tile(tile)
                tiles_added += 1
            x += step_x

        step_y = 1 if ey > y else -1
        while y != ey:
            if not world.has_tile(x, y, 7):
                tile = Tile(x=x, y=y, z=7, ground=self.GAP_FILL_GROUND, zone=zone_name)
                world.set_tile(tile)
                tiles_added += 1
            y += step_y

        return tiles_added
