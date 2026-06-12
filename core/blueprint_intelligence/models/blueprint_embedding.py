"""BlueprintEmbedding model — vector representation of a blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class BlueprintEmbedding:
    """
    Numerical embedding of a blueprint's structural features.

    Each feature is a float in [0, 1] representing the normalized value.
    The full vector is the concatenation of all feature groups.
    """

    # Blueprint identity
    blueprint_name: str = ""
    blueprint_category: str = ""

    # Tile-level features
    tile_density: float = 0.0
    room_count: float = 0.0
    corridor_count: float = 0.0
    branch_factor: float = 0.0
    connectivity: float = 0.0

    # Spawn features
    spawn_density: float = 0.0
    boss_count: float = 0.0

    # City features
    city_services: float = 0.0

    # Topology features
    waypoint_count: float = 0.0
    hunt_flow: float = 0.0

    # Quality scores (from critic / playtest)
    critic_score: float = 0.0
    playtest_score: float = 0.0

    # Internal
    _vector: Optional[List[float]] = None

    def __post_init__(self) -> None:
        self._clamp_values()

    def _clamp_values(self) -> None:
        for field_name in (
            "tile_density",
            "room_count",
            "corridor_count",
            "branch_factor",
            "connectivity",
            "spawn_density",
            "boss_count",
            "city_services",
            "waypoint_count",
            "hunt_flow",
            "critic_score",
            "playtest_score",
        ):
            val = getattr(self, field_name, 0.0)
            setattr(self, field_name, max(0.0, min(1.0, float(val))))

    @property
    def vector(self) -> List[float]:
        """Return the feature vector (cached)."""
        if self._vector is None:
            self._vector = [
                self.tile_density,
                self.room_count,
                self.corridor_count,
                self.branch_factor,
                self.connectivity,
                self.spawn_density,
                self.boss_count,
                self.city_services,
                self.waypoint_count,
                self.hunt_flow,
                self.critic_score,
                self.playtest_score,
            ]
        return self._vector

    @property
    def dimension(self) -> int:
        return len(self.vector)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blueprint_name": self.blueprint_name,
            "blueprint_category": self.blueprint_category,
            "tile_density": self.tile_density,
            "room_count": self.room_count,
            "corridor_count": self.corridor_count,
            "branch_factor": self.branch_factor,
            "connectivity": self.connectivity,
            "spawn_density": self.spawn_density,
            "boss_count": self.boss_count,
            "city_services": self.city_services,
            "waypoint_count": self.waypoint_count,
            "hunt_flow": self.hunt_flow,
            "critic_score": self.critic_score,
            "playtest_score": self.playtest_score,
            "vector": self.vector,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlueprintEmbedding:
        return cls(
            blueprint_name=data.get("blueprint_name", ""),
            blueprint_category=data.get("blueprint_category", ""),
            tile_density=data.get("tile_density", 0.0),
            room_count=data.get("room_count", 0.0),
            corridor_count=data.get("corridor_count", 0.0),
            branch_factor=data.get("branch_factor", 0.0),
            connectivity=data.get("connectivity", 0.0),
            spawn_density=data.get("spawn_density", 0.0),
            boss_count=data.get("boss_count", 0.0),
            city_services=data.get("city_services", 0.0),
            waypoint_count=data.get("waypoint_count", 0.0),
            hunt_flow=data.get("hunt_flow", 0.0),
            critic_score=data.get("critic_score", 0.0),
            playtest_score=data.get("playtest_score", 0.0),
        )

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Cosine similarity between two vectors."""
        import math

        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(ai * bi for ai, bi in zip(a, b))
        norm_a = math.sqrt(sum(ai * ai for ai in a))
        norm_b = math.sqrt(sum(bi * bi for bi in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def similarity_to(self, other: BlueprintEmbedding) -> float:
        """Cosine similarity to another embedding."""
        return self.cosine_similarity(self.vector, other.vector)
