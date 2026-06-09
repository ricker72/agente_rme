from __future__ import annotations

import math
import logging
from typing import Any, Dict, List, Optional, Tuple

from .tile import Tile
from .item import Item
from .spawn import Spawn
from .structure import Structure
from .region import Region
from .chunk import Chunk, DEFAULT_CHUNK_SIZE

logger = logging.getLogger(__name__)


class WorldModel:
    """
    Unified World Model — the single source of truth for the entire map.

    This is the most important class in the architecture. Every subsystem
    (blueprints, export, preview, QA, playtest) works through this model.

    Architecture:
      - tiles: Dict[str, Tile] — all tiles keyed by "x:y:z".
      - structures: List[Structure] — all placed blueprints.
      - regions: List[Region] — named zones.
      - chunks: Dict[str, Chunk] — spatial partitioning for large maps.

    Usage:
        world = WorldModel()

        world.set_tile(Tile(x=100, y=100, z=7, ground=817))
        tile = world.get_tile(100, 100, 7)

        structure = Structure(name="temple", category="temple",
                              x=1000, y=1000, z=7, width=20, height=20)
        world.add_structure(structure)

        region = Region(name="issavi_city", theme="issavi")
        world.add_region(region)
    """

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE):
        self.tiles: Dict[str, Tile] = {}
        self.structures: List[Structure] = []
        self.regions: List[Region] = []
        self.chunks: Dict[str, Chunk] = {}
        self._chunk_size = chunk_size
        self._tile_count = 0

    # ------------------------------------------------------------------
    # Tile operations
    # ------------------------------------------------------------------

    def set_tile(self, tile: Tile) -> None:
        """Add or update a tile in the world."""
        key = tile.key
        was_present = key in self.tiles
        self.tiles[key] = tile
        if not was_present:
            self._tile_count += 1

        # Also update the chunk system
        chunk = self._get_or_create_chunk(tile.x, tile.y, tile.z)
        chunk.set_tile(tile)

    def get_tile(self, x: int, y: int, z: int = 7) -> Optional[Tile]:
        """Get a tile at the given world coordinates."""
        key = Tile.make_key(x, y, z)
        return self.tiles.get(key)

    def has_tile(self, x: int, y: int, z: int = 7) -> bool:
        """Check if a tile exists at the given coordinates."""
        key = Tile.make_key(x, y, z)
        return key in self.tiles

    def remove_tile(self, x: int, y: int, z: int = 7) -> bool:
        """Remove a tile from the world. Returns True if removed."""
        key = Tile.make_key(x, y, z)
        if key in self.tiles:
            del self.tiles[key]
            self._tile_count -= 1
            # Also remove from chunk
            chunk_key = self._chunk_key(x, y)
            if chunk_key in self.chunks:
                self.chunks[chunk_key].tiles.pop(key, None)
            return True
        return False

    def tile_count(self) -> int:
        """Total number of tiles in the world."""
        return self._tile_count

    def get_tiles_in_area(self, x1: int, y1: int, x2: int, y2: int,
                          z: int = 7) -> List[Tile]:
        """Get all tiles within a rectangular area (inclusive)."""
        result: List[Tile] = []
        for key, tile in self.tiles.items():
            if (tile.z == z and
                    x1 <= tile.x <= x2 and
                    y1 <= tile.y <= y2):
                result.append(tile)
        return result

    # ------------------------------------------------------------------
    # Structure operations
    # ------------------------------------------------------------------

    def add_structure(self, structure: Structure) -> None:
        """Register a placed structure (blueprint) in the world."""
        self.structures.append(structure)

    def get_structure(self, name: str) -> Optional[Structure]:
        """Find a structure by name."""
        for s in self.structures:
            if s.name == name:
                return s
        return None

    def get_structures_by_category(self, category: str) -> List[Structure]:
        """Get all structures of a given category."""
        return [s for s in self.structures if s.category == category]

    def get_structures_in_area(self, x1: int, y1: int, x2: int, y2: int) -> List[Structure]:
        """Get all structures whose bounds intersect the given area."""
        return [s for s in self.structures if self._bounds_intersect(s, x1, y1, x2, y2)]

    def structure_count(self) -> int:
        """Number of placed structures."""
        return len(self.structures)

    # ------------------------------------------------------------------
    # Region operations
    # ------------------------------------------------------------------

    def add_region(self, region: Region) -> None:
        """Add a region to the world."""
        self.regions.append(region)

    def get_region(self, name: str) -> Optional[Region]:
        """Find a region by name."""
        for r in self.regions:
            if r.name == name:
                return r
        return None

    def get_regions_by_theme(self, theme: str) -> List[Region]:
        """Get all regions matching a theme."""
        return [r for r in self.regions if r.theme == theme]

    def region_count(self) -> int:
        """Number of regions."""
        return len(self.regions)

    # ------------------------------------------------------------------
    # Chunk operations
    # ------------------------------------------------------------------

    def get_chunk(self, chunk_x: int, chunk_y: int) -> Optional[Chunk]:
        """Get a chunk by its indices."""
        key = self._chunk_key(chunk_x, chunk_y)
        return self.chunks.get(key)

    def get_chunk_for(self, wx: int, wy: int) -> Optional[Chunk]:
        """Get the chunk containing a given world coordinate."""
        cx, cy = Chunk.world_to_chunk(wx, wy, self._chunk_size)
        return self.get_chunk(cx, cy)

    def chunk_count(self) -> int:
        """Number of active chunks."""
        return len(self.chunks)

    def all_chunks(self) -> List[Chunk]:
        """Return all chunks."""
        return list(self.chunks.values())

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_ground_ids_in_area(self, x1: int, y1: int, x2: int, y2: int,
                               z: int = 7) -> List[int]:
        """Get all unique ground IDs in an area."""
        grounds: set = set()
        for tile in self.get_tiles_in_area(x1, y1, x2, y2, z):
            if tile.ground is not None and isinstance(tile.ground, int):
                grounds.add(tile.ground)
        return sorted(grounds)

    def get_spawns_in_area(self, x1: int, y1: int, x2: int, y2: int,
                           z: int = 7) -> List[Spawn]:
        """Get all spawns in an area."""
        spawns: List[Spawn] = []
        for tile in self.get_tiles_in_area(x1, y1, x2, y2, z):
            if tile.spawn is not None:
                spawns.append(tile.spawn)
        return spawns

    def clear(self) -> None:
        """Remove all tiles, structures, regions, and chunks."""
        self.tiles.clear()
        self.structures.clear()
        self.regions.clear()
        self.chunks.clear()
        self._tile_count = 0

    def summary(self) -> Dict[str, Any]:
        """Return a summary of the world's contents."""
        return {
            "tiles": self.tile_count(),
            "structures": self.structure_count(),
            "regions": self.region_count(),
            "chunks": self.chunk_count(),
            "bounds": self._calculate_bounds(),
        }

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire world model to a dictionary."""
        return {
            "tiles": [tile.to_dict() for tile in self.tiles.values()],
            "structures": [s.to_dict() for s in self.structures],
            "regions": [r.to_dict() for r in self.regions],
            "chunks": [c.to_dict() for c in self.chunks.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorldModel:
        """Deserialize a dictionary into a WorldModel."""
        world = cls()

        for td in data.get("tiles", []):
            tile = Tile.from_dict(td)
            world.set_tile(tile)

        for sd in data.get("structures", []):
            world.add_structure(Structure.from_dict(sd))

        for rd in data.get("regions", []):
            world.add_region(Region.from_dict(rd))

        return world

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_or_create_chunk(self, wx: int, wy: int, wz: int) -> Chunk:
        """Get or create the chunk for a given world tile."""
        cx, cy = Chunk.world_to_chunk(wx, wy, self._chunk_size)
        key = f"{cx}:{cy}"
        if key not in self.chunks:
            self.chunks[key] = Chunk(chunk_x=cx, chunk_y=cy,
                                     chunk_size=self._chunk_size)
        return self.chunks[key]

    @staticmethod
    def _chunk_key(cx: int, cy: int) -> str:
        return f"{cx}:{cy}"

    def _calculate_bounds(self) -> Optional[Dict[str, int]]:
        """Calculate world bounds from existing tiles."""
        if not self.tiles:
            return None
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')
        for tile in self.tiles.values():
            min_x = min(min_x, tile.x)
            max_x = max(max_x, tile.x)
            min_y = min(min_y, tile.y)
            max_y = max(max_y, tile.y)
            min_z = min(min_z, tile.z)
            max_z = max(max_z, tile.z)
        return {
            "min_x": int(min_x), "max_x": int(max_x),
            "min_y": int(min_y), "max_y": int(max_y),
            "min_z": int(min_z), "max_z": int(max_z),
        }

    @staticmethod
    def _bounds_intersect(s: Structure, x1: int, y1: int,
                          x2: int, y2: int) -> bool:
        """Check if a structure's bounds intersect a rectangle."""
        sx1, sy1, sx2, sy2 = s.bounds
        return not (sx2 <= x1 or sx1 >= x2 or sy2 <= y1 or sy1 >= y2)