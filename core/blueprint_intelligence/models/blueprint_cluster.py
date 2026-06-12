"""BlueprintCluster model — cluster of similar blueprints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class BlueprintCluster:
    """
    A cluster of similar blueprints discovered by the cluster engine.

    Each cluster has a centroid vector, member blueprints, and
    summary statistics.
    """

    name: str = ""
    member_blueprints: List[str] = field(default_factory=list)
    centroid: List[float] = field(default_factory=lambda: [0.0] * 12)
    size: int = 0

    # Cluster statistics
    avg_critic_score: float = 0.0
    avg_playtest_score: float = 0.0
    avg_tile_density: float = 0.0
    avg_room_count: float = 0.0
    dominant_category: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "member_blueprints": self.member_blueprints,
            "centroid": self.centroid,
            "size": self.size,
            "avg_critic_score": self.avg_critic_score,
            "avg_playtest_score": self.avg_playtest_score,
            "avg_tile_density": self.avg_tile_density,
            "avg_room_count": self.avg_room_count,
            "dominant_category": self.dominant_category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlueprintCluster:
        return cls(
            name=data.get("name", ""),
            member_blueprints=data.get("member_blueprints", []),
            centroid=data.get("centroid", [0.0] * 12),
            size=data.get("size", 0),
            avg_critic_score=data.get("avg_critic_score", 0.0),
            avg_playtest_score=data.get("avg_playtest_score", 0.0),
            avg_tile_density=data.get("avg_tile_density", 0.0),
            avg_room_count=data.get("avg_room_count", 0.0),
            dominant_category=data.get("dominant_category", ""),
        )
