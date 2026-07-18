"""
CriticRecommendation — concrete actions to improve a map.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict


class RecommendationPriority(str, enum.Enum):
    """How urgently the recommendation should be applied."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CriticRecommendation:
    """
    A concrete recommendation to improve the map.

    Attributes:
        title: Short actionable title.
        description: Detailed description of the action.
        category: Critic category (e.g. "spawn", "navigation").
        priority: How urgent the recommendation is.
        target_location: Optional location string.
        action: Optional structured action payload.
    """

    title: str
    description: str
    category: str
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    target_location: str = ""
    action: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.priority, str):
            self.priority = RecommendationPriority(self.priority)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority.value,
            "target_location": self.target_location,
            "action": self.action,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriticRecommendation":
        return cls(
            title=data.get("title", ""),
            description=data.get("description", ""),
            category=data.get("category", "general"),
            priority=data.get("priority", RecommendationPriority.MEDIUM),
            target_location=data.get("target_location", ""),
            action=data.get("action", {}) or {},
        )
