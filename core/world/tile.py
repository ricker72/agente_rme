from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Tile:
    """
    A single tile in the world.

    This is the fundamental unit of the map. Every coordinate (x, y, z)
    has at most one Tile instance.

    Architecture:
      - ground: The floor item ID (int) or None if no ground.
      - items: List of Item dicts or Item objects placed on this tile.
      - spawn: Optional Spawn dict or Spawn object for monster spawns.
      - zone: Named zone this tile belongs to (e.g. "temple", "market").
    """

    x: int
    y: int
    z: int

    ground: Optional[int] = None
    items: List[Any] = field(default_factory=list)
    spawn: Optional[Any] = None
    zone: Optional[str] = None

    # ------------------------------------------------------------------
    # Key
    # ------------------------------------------------------------------

    @property
    def key(self) -> str:
        """Unique key for this tile: 'x:y:z'."""
        return f"{self.x}:{self.y}:{self.z}"

    @staticmethod
    def make_key(x: int, y: int, z: int) -> str:
        """Static method to build a tile key without creating a Tile."""
        return f"{x}:{y}:{z}"

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary."""
        d: Dict[str, Any] = {
            "x": self.x,
            "y": self.y,
            "z": self.z,
        }
        if self.ground is not None:
            d["ground"] = self.ground
        if self.items:
            d["items"] = [
                item.to_dict() if hasattr(item, "to_dict") else item
                for item in self.items
            ]
        if self.spawn is not None:
            d["spawn"] = (
                self.spawn.to_dict() if hasattr(self.spawn, "to_dict") else self.spawn
            )
        if self.zone is not None:
            d["zone"] = self.zone
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Tile:
        """Deserialize from a dictionary."""
        from .item import Item
        from .spawn import Spawn

        items_raw = data.get("items", [])
        items = []
        for i in items_raw:
            if isinstance(i, dict):
                items.append(Item.from_dict(i))
            else:
                items.append(i)

        spawn_raw = data.get("spawn")
        spawn: Optional[Spawn] = None
        if spawn_raw is not None:
            spawn = (
                Spawn.from_dict(spawn_raw) if isinstance(spawn_raw, dict) else spawn_raw
            )

        return cls(
            x=data["x"],
            y=data["y"],
            z=data["z"],
            ground=data.get("ground"),
            items=items,
            spawn=spawn,
            zone=data.get("zone"),
        )

    def __repr__(self) -> str:
        return (
            f"Tile(x={self.x}, y={self.y}, z={self.z}, "
            f"ground={self.ground}, items={len(self.items)}, "
            f"spawn={'yes' if self.spawn else 'no'})"
        )
