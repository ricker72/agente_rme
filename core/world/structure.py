from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Structure:
    """
    Represents a blueprint that has been placed in the world.

    Architecture:
      - name: Blueprint name (e.g. "issavi_temple_small").
      - category: Blueprint category (e.g. "temple", "market", "bridge").
      - x, y, z: World position where the structure was placed.
      - width, height: Dimensions of the structure in tiles.
      - tiles: List of (x, y) offsets relative to the structure origin.
               Used for collision detection and removal.
    """

    name: str
    category: str
    x: int
    y: int
    z: int
    width: int
    height: int
    tile_count: int = 0
    tags: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def bounds(self) -> tuple:
        """Return (min_x, min_y, max_x, max_y) in world coordinates."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def contains(self, wx: int, wy: int) -> bool:
        """Check if a world coordinate falls within this structure."""
        return (
            self.x <= wx < self.x + self.width and self.y <= wy < self.y + self.height
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "width": self.width,
            "height": self.height,
            "tile_count": self.tile_count,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Structure:
        tags = data.get("tags", [])
        return cls(
            name=data.get("name", "unknown"),
            category=data.get("category", "unknown"),
            x=data.get("x", 0),
            y=data.get("y", 0),
            z=data.get("z", 7),
            width=data.get("width", 10),
            height=data.get("height", 10),
            tile_count=data.get("tile_count", 0),
            tags=list(tags) if tags else [],
        )

    def __repr__(self) -> str:
        return (
            f"Structure(name='{self.name}', cat='{self.category}', "
            f"pos=({self.x},{self.y},z={self.z}), "
            f"size={self.width}x{self.height}, tiles={self.tile_count})"
        )
