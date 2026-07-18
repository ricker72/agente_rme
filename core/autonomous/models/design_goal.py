"""
Design Goal model - represents the high-level objectives for autonomous world design.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class DesignGoal:
    """Represents the high-level design objectives for world generation."""

    prompt: str
    level_range: tuple = (1, 200)
    num_hunts: int = 2
    num_bosses: int = 1
    num_raids: int = 0
    target_critic_score: float = 90.0
    target_playtest_score: float = 80.0
    target_size: Optional[int] = None  # in tiles
    target_complexity: Optional[float] = None
    strategy: str = "balanced"
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate the design goal after initialization."""
        if not self.prompt:
            raise ValueError("Prompt cannot be empty")
        if self.level_range[0] >= self.level_range[1]:
            raise ValueError("Invalid level range")
        if self.num_hunts < 0 or self.num_bosses < 0 or self.num_raids < 0:
            raise ValueError("Counts cannot be negative")
        if self.target_critic_score < 0 or self.target_critic_score > 100:
            raise ValueError("Target critic score must be between 0 and 100")
        if self.target_playtest_score < 0 or self.target_playtest_score > 100:
            raise ValueError("Target playtest score must be between 0 and 100")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "prompt": self.prompt,
            "level_range": list(self.level_range),
            "num_hunts": self.num_hunts,
            "num_bosses": self.num_bosses,
            "num_raids": self.num_raids,
            "target_critic_score": self.target_critic_score,
            "target_playtest_score": self.target_playtest_score,
            "target_size": self.target_size,
            "target_complexity": self.target_complexity,
            "strategy": self.strategy,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DesignGoal":
        """Create from dictionary."""
        if "level_range" in data and isinstance(data["level_range"], list):
            data["level_range"] = tuple(data["level_range"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
