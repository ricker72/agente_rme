"""BI-1 canonical reusable blueprint pattern model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Pattern:
    """Reusable structural pattern extracted from real Tibia/OpenTibia maps."""

    pattern_id: str
    name: str
    category: str
    source: str
    confidence: float
    tags: list[str]

    def __post_init__(self) -> None:
        _require_str("pattern_id", self.pattern_id)
        _require_str("name", self.name)
        _require_str("category", self.category)
        _require_str("source", self.source)
        if not isinstance(self.confidence, (int, float)) or isinstance(self.confidence, bool):
            raise TypeError("confidence must be a number")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        _require_str_list("tags", self.tags)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "name": self.name,
            "category": self.category,
            "source": self.source,
            "confidence": self.confidence,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Pattern:
        return cls(
            pattern_id=data["pattern_id"],
            name=data["name"],
            category=data["category"],
            source=data["source"],
            confidence=data["confidence"],
            tags=data["tags"],
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Pattern:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise TypeError("Pattern JSON must decode to an object")
        return cls.from_dict(data)


def _require_str(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if not value:
        raise ValueError(f"{field_name} must not be empty")


def _require_str_list(field_name: str, value: object) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError(f"{field_name} must be a list[str]")


__all__ = ["Pattern"]
