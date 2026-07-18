"""BI-4 Similarity Result model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

@dataclass(slots=True)
class SimilarityResult:
    """Deterministic similarity comparison result."""

    target_id: str
    candidate_id: str
    score: float
    category: str
    source: str
    reasons: list[str]

    def __post_init__(self) -> None:
        """Validate all fields."""
        _require_str("target_id", self.target_id)
        _require_str("candidate_id", self.candidate_id)
        if not isinstance(self.score, (int, float)) or isinstance(self.score, bool):
            raise TypeError("score must be a number")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")
        _require_str("category", self.category)
        _require_str("source", self.source, allow_empty=True)
        if not isinstance(self.reasons, list) or not all(isinstance(item, str) for item in self.reasons):
            raise TypeError("reasons must be a list[str]")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "target_id": self.target_id,
            "candidate_id": self.candidate_id,
            "score": self.score,
            "category": self.category,
            "source": self.source,
            "reasons": list(self.reasons),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SimilarityResult:
        """Create from dictionary."""
        return cls(
            target_id=data["target_id"],
            candidate_id=data["candidate_id"],
            score=data["score"],
            category=data["category"],
            source=data["source"],
            reasons=data["reasons"],
        )

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> SimilarityResult:
        """Create from JSON string."""
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise TypeError("SimilarityResult JSON must decode to an object")
        return cls.from_dict(data)

def _require_str(field_name: str, value: object, allow_empty: bool = False) -> None:
    """Validate string field."""

    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if not value and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")

__all__ = ["SimilarityResult"]
