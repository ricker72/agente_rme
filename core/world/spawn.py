from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Spawn:
    """
    A monster spawn on a tile.

    Architecture:
      - monster: The monster name (as defined in monsters.xml).
      - respawn: Respawn time in seconds (default 60).
      - radius: Spawn radius in tiles (default 5).
    """
    monster: str
    respawn: int = 60
    radius: int = 5

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "monster": self.monster,
            "respawn": self.respawn,
            "radius": self.radius,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Spawn:
        return cls(
            monster=data.get("monster", data.get("name", "Unknown")),
            respawn=data.get("respawn", 60),
            radius=data.get("radius", 5),
        )

    def __repr__(self) -> str:
        return f"Spawn(monster='{self.monster}', respawn={self.respawn}s, radius={self.radius})"