"""BI-1 canonical blueprint metrics model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class BlueprintMetrics:
    """Quality dimensions shared by Blueprint Intelligence and critics."""

    connectivity_score: float
    density_score: float
    navigation_score: float
    progression_score: float
    exploration_score: float

    def __post_init__(self) -> None:
        _require_number("connectivity_score", self.connectivity_score)
        _require_number("density_score", self.density_score)
        _require_number("navigation_score", self.navigation_score)
        _require_number("progression_score", self.progression_score)
        _require_number("exploration_score", self.exploration_score)

    def to_dict(self) -> dict[str, Any]:
        return {
            "connectivity_score": self.connectivity_score,
            "density_score": self.density_score,
            "navigation_score": self.navigation_score,
            "progression_score": self.progression_score,
            "exploration_score": self.exploration_score,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BlueprintMetrics:
        return cls(
            connectivity_score=data["connectivity_score"],
            density_score=data["density_score"],
            navigation_score=data["navigation_score"],
            progression_score=data["progression_score"],
            exploration_score=data["exploration_score"],
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> BlueprintMetrics:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise TypeError("BlueprintMetrics JSON must decode to an object")
        return cls.from_dict(data)


def _require_number(field_name: str, value: object) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be a number")
    if not 0.0 <= value <= 100.0:
        raise ValueError(f"{field_name} must be between 0.0 and 100.0")


__all__ = ["BlueprintMetrics"]
