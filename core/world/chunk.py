from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .tile import Tile


# Default chunk size (64x64 tiles)
DEFAULT_CHUNK_SIZE = 64


@dataclass
class Chunk:
    """
    A chunk is a fixed-size grid of tiles used to partition large maps.

    Default chunk size is 64x64 tiles. Each chunk can be serialized,
    cached, or processed independently, enabling lazy loading and
    efficient memory usage for maps with 500,000+ tiles.

    Architecture:
      - chunk_x, chunk_y: Chunk indices (world_x // chunk_size).
      - chunk_size: Tile dimensions of this chunk (same for all chunks).
      - tiles: Dict of (local_x, local_y) -> Tile (local coords within chunk).
    """
    chunk_x: int
    chunk_y: int
    chunk_size: int = DEFAULT_CHUNK_SIZE
    tiles: Dict[str, Tile] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def world_offset_x(self) -> int:
        """World X coordinate of the chunk's origin."""
        return self.chunk_x * self.chunk_size

    @property
    def world_offset_y(self) -> int:
        """World Y coordinate of the chunk's origin."""
        return self.chunk_y * self.chunk_size

    @property
    def bounds_world(self) -> Tuple[int, int, int, int]:
        """World-space bounds: (min_x, min_y, max_x, max_y)."""
        ox = self.world_offset_x
        oy = self.world_offset_y
        return (ox, oy, ox + self.chunk_size, oy + self.chunk_size)

    # ------------------------------------------------------------------
    # Coordinate conversion
    # ------------------------------------------------------------------

    @staticmethod
    def world_to_chunk(wx: int, wy: int, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Tuple[int, int]:
        """Convert world coordinates to chunk indices."""
        return (wx // chunk_size, wy // chunk_size)

    @staticmethod
    def world_to_local(wx: int, wy: int, chunk_size: int = DEFAULT_CHUNK_SIZE) -> Tuple[int, int]:
        """Convert world coordinates to local coordinates within a chunk."""
        return (wx % chunk_size, wy % chunk_size)

    def to_local(self, wx: int, wy: int) -> Tuple[int, int]:
        """Convert world (wx, wy) to local (lx, ly) within this chunk."""
        return (wx - self.world_offset_x, wy - self.world_offset_y)

    def local_key(self, lx: int, ly: int) -> str:
        """Create a local key for the tile dict."""
        return f"{lx}:{ly}"

    # ------------------------------------------------------------------
    # Tile operations
    # ------------------------------------------------------------------

    def set_tile(self, tile: Tile) -> None:
        """Add or update a tile. Tile.x/y are treated as world coords."""
        lx, ly = self.to_local(tile.x, tile.y)
        key = self.local_key(lx, ly)
        self.tiles[key] = tile

    def get_tile(self, wx: int, wy: int) -> Optional[Tile]:
        """Get a tile by world coordinates."""
        lx, ly = self.to_local(wx, wy)
        key = self.local_key(lx, ly)
        return self.tiles.get(key)

    def has_tile(self, wx: int, wy: int) -> bool:
        """Check if a tile exists at the given world coordinates."""
        lx, ly = self.to_local(wx, wy)
        key = self.local_key(lx, ly)
        return key in self.tiles

    def tile_count(self) -> int:
        """Number of tiles in this chunk."""
        return len(self.tiles)

    def clear(self) -> None:
        """Remove all tiles from this chunk."""
        self.tiles.clear()

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_x": self.chunk_x,
            "chunk_y": self.chunk_y,
            "chunk_size": self.chunk_size,
            "tile_count": self.tile_count(),
            "tiles": [tile.to_dict() for tile in self.tiles.values()],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Chunk:
        tiles_raw = data.get("tiles", [])
        tiles = {}
        for td in tiles_raw:
            tile = Tile.from_dict(td)
            lx, ly = cls.world_to_local(tile.x, tile.y, data.get("chunk_size", DEFAULT_CHUNK_SIZE))
            key = f"{lx}:{ly}"
            tiles[key] = tile

        return cls(
            chunk_x=data.get("chunk_x", 0),
            chunk_y=data.get("chunk_y", 0),
            chunk_size=data.get("chunk_size", DEFAULT_CHUNK_SIZE),
            tiles=tiles,
        )

    def __repr__(self) -> str:
        return (
            f"Chunk({self.chunk_x},{self.chunk_y}) "
            f"[{self.world_offset_x},{self.world_offset_y}] "
            f"size={self.chunk_size}x{self.chunk_size}, "
            f"tiles={self.tile_count()}"
        )