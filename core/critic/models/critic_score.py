"""
CriticScore — represents a numeric quality score in the 0-100 range.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CriticScore:
    """
    A normalized score (0-100) for a critic category.

    Attributes:
        category: Name of the scoring category (e.g. "visual", "navigation").
        value: Score value, must be 0-100.
        max_value: Maximum possible value (default 100).
        breakdown: Optional dict with sub-component scores.
    """

    category: str
    value: float
    max_value: float = 100.0
    breakdown: Dict[str, float] = field(default_factory=dict)
    notes: str = ""

    def __post_init__(self) -> None:
        # Clamp to a valid range so downstream consumers can rely on bounds.
        try:
            v = float(self.value)
        except (TypeError, ValueError):
            v = 0.0
        self.value = max(0.0, min(self.max_value, v))

    @property
    def ratio(self) -> float:
        """Score as a normalized ratio in [0, 1]."""
        if self.max_value <= 0:
            return 0.0
        return self.value / self.max_value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "value": round(self.value, 2),
            "max_value": self.max_value,
            "ratio": round(self.ratio, 4),
            "breakdown": {k: round(v, 2) for k, v in self.breakdown.items()},
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriticScore":
        return cls(
            category=data.get("category", "unknown"),
            value=data.get("value", 0.0),
            max_value=data.get("max_value", 100.0),
            breakdown=data.get("breakdown", {}) or {},
            notes=data.get("notes", ""),
        )

    def __repr__(self) -> str:
        return f"CriticScore({self.category}={self.value:.1f}/{self.max_value:.0f})"
