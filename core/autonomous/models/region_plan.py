"""
Region Plan model - represents a plan for a specific region within the world.
"""

from dataclasses import dataclass, field
from typing import List
from datetime import datetime


@dataclass
class RegionPlan:
    """Represents a plan for a specific region within the world."""

    region_id: str
    region_name: str
    region_type: str  # "hunt", "boss", "raid", "city", "mixed"
    description: str = ""
    level_range: tuple = (1, 200)
    target_size: int = 1000  # tiles
    target_density: float = 0.5
    target_difficulty: float = 0.5
    blueprint_candidates: List[str] = field(default_factory=list)
    selected_blueprints: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate region plan after initialization."""
        valid_types = ["hunt", "boss", "raid", "city", "mixed"]
        if self.region_type not in valid_types:
            raise ValueError(f"Region type must be one of {valid_types}")
        if not self.region_name:
            raise ValueError("Region name cannot be empty")
        if self.target_size <= 0:
            raise ValueError("Target size must be positive")
        if not (0 <= self.target_density <= 1):
            raise ValueError("Target density must be between 0 and 1")
        if not (0 <= self.target_difficulty <= 1):
            raise ValueError("Target difficulty must be between 0 and 1")

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "region_id": self.region_id,
            "region_name": self.region_name,
            "region_type": self.region_type,
            "description": self.description,
            "level_range": list(self.level_range),
            "target_size": self.target_size,
            "target_density": self.target_density,
            "target_difficulty": self.target_difficulty,
            "blueprint_candidates": self.blueprint_candidates,
            "selected_blueprints": self.selected_blueprints,
            "patterns": self.patterns,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RegionPlan":
        """Create from dictionary."""
        if "level_range" in data and isinstance(data["level_range"], list):
            data["level_range"] = tuple(data["level_range"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
