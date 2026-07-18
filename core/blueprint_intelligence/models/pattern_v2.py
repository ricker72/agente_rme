# mypy: ignore-errors
"""
Blueprint Intelligence 2.0 — Pattern model (v2).

A reusable structural pattern extracted from blueprints.
Patterns are the heart of the system — they encode reusable
structural knowledge from real maps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class PatternV2:
    """
    A reusable structural pattern mined from blueprints.

    Examples:
      - Issavi → Plaza Pattern, Market Pattern, District Pattern, Road Pattern
      - Roshamuul → Hunt Pattern, Spawn Cluster Pattern, Loop Pattern
    """

    name: str = ""
    pattern_type: str = (
        "unknown"  # plaza, market, district, road, hunt, spawn_cluster, loop, etc.
    )
    source_blueprint: str = ""  # Original blueprint this was mined from
    confidence: float = 0.0

    # Structural signature (feature vector for similarity matching)
    feature_vector: List[float] = field(default_factory=lambda: [0.0] * 16)

    # Dimensions
    width: int = 0
    height: int = 0

    # Pattern components (sub-patterns / elements)
    elements: List[str] = field(default_factory=list)  # element names

    # Connections to other patterns
    connections: List[str] = field(default_factory=list)

    # Usage statistics
    reuse_count: int = 0
    avg_critic_score: float = 0.0

    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "pattern_type": self.pattern_type,
            "source_blueprint": self.source_blueprint,
            "confidence": self.confidence,
            "feature_vector": self.feature_vector,
            "width": self.width,
            "height": self.height,
            "elements": self.elements,
            "connections": self.connections,
            "reuse_count": self.reuse_count,
            "avg_critic_score": self.avg_critic_score,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PatternV2:
        return cls(
            name=data.get("name", ""),
            pattern_type=data.get("pattern_type", "unknown"),
            source_blueprint=data.get("source_blueprint", ""),
            confidence=data.get("confidence", 0.0),
            feature_vector=data.get("feature_vector", [0.0] * 16),
            width=data.get("width", 0),
            height=data.get("height", 0),
            elements=data.get("elements", []),
            connections=data.get("connections", []),
            reuse_count=data.get("reuse_count", 0),
            avg_critic_score=data.get("avg_critic_score", 0.0),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
