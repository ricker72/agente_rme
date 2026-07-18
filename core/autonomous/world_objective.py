"""
World Objective - represents a single objective for world quality assessment.
"""

from dataclasses import dataclass, field
from typing import Dict, Any
from enum import Enum


class ObjectiveType(Enum):
    """Types of world objectives."""

    QUALITY = "quality"
    DENSITY = "density"
    NAVIGATION = "navigation"
    BOSS = "boss"
    CITY = "city"
    DIFFICULTY = "difficulty"
    PLAYTEST = "playtest"
    CRITIC = "critic"
    REUSE = "reuse"


@dataclass
class WorldObjective:
    """Represents a single objective for world quality assessment."""

    objective_type: ObjectiveType
    weight: float = 1.0
    target_value: float = 0.0
    current_value: float = 0.0
    threshold: float = 0.0
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate objective after initialization."""
        if not (0 <= self.weight <= 1):
            raise ValueError("Weight must be between 0 and 1")
        if not (0 <= self.target_value <= 1):
            raise ValueError("Target value must be between 0 and 1")
        if not (0 <= self.current_value <= 1):
            raise ValueError("Current value must be between 0 and 1")

    def evaluate(self, value: float) -> float:
        """Evaluate the objective with a given value and return the score."""
        self.current_value = value

        if self.target_value == 0:
            return 0.0

        # Calculate how close we are to the target
        if value >= self.target_value:
            score = 1.0
        else:
            score = value / self.target_value

        # Apply weight
        weighted_score = score * self.weight

        # Check if we meet the threshold
        if self.threshold > 0 and value < self.threshold:
            weighted_score *= 0.5  # Penalty for below threshold

        return weighted_score

    def get_status(self) -> str:
        """Get the status of the objective."""
        if self.current_value >= self.target_value:
            return "achieved"
        elif self.current_value >= self.threshold:
            return "in_progress"
        else:
            return "not_started"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "objective_type": self.objective_type.value,
            "weight": self.weight,
            "target_value": self.target_value,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "description": self.description,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldObjective":
        """Create from dictionary."""
        data["objective_type"] = ObjectiveType(data["objective_type"])
        return cls(**data)
