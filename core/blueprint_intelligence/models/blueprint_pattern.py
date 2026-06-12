"""BlueprintPattern model — detected structural patterns."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class BlueprintPattern:
    """
    A detected structural pattern mined from blueprints.

    Patterns can be city patterns, hunt patterns, boss patterns,
    raid patterns, or quest patterns.
    """

    name: str = ""
    pattern_type: str = "unknown"
    source_blueprints: List[str] = field(default_factory=list)
    confidence: float = 0.0

    # Structural signature (feature vector)
    feature_vector: List[float] = field(default_factory=lambda: [0.0] * 12)

    # Pattern-specific data
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Usage statistics
    reuse_count: int = 0
    avg_critic_score: float = 0.0
    avg_playtest_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "pattern_type": self.pattern_type,
            "source_blueprints": self.source_blueprints,
            "confidence": self.confidence,
            "feature_vector": self.feature_vector,
            "metadata": self.metadata,
            "reuse_count": self.reuse_count,
            "avg_critic_score": self.avg_critic_score,
            "avg_playtest_score": self.avg_playtest_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlueprintPattern:
        return cls(
            name=data.get("name", ""),
            pattern_type=data.get("pattern_type", "unknown"),
            source_blueprints=data.get("source_blueprints", []),
            confidence=data.get("confidence", 0.0),
            feature_vector=data.get("feature_vector", [0.0] * 12),
            metadata=data.get("metadata", {}),
            reuse_count=data.get("reuse_count", 0),
            avg_critic_score=data.get("avg_critic_score", 0.0),
            avg_playtest_score=data.get("avg_playtest_score", 0.0),
        )
