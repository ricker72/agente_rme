"""
Design Plan model - represents the complete plan for world generation.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from .region_plan import RegionPlan


@dataclass
class DesignPlan:
    """Represents the complete plan for world generation."""

    plan_id: str
    goal_id: str
    description: str = ""
    regions: List[RegionPlan] = field(default_factory=list)
    total_estimated_size: int = 0
    estimated_complexity: float = 0.0
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate design plan after initialization."""
        if not self.plan_id:
            raise ValueError("Plan ID cannot be empty")
        if not self.goal_id:
            raise ValueError("Goal ID cannot be empty")
        if len(self.regions) == 0:
            raise ValueError("Plan must contain at least one region")

        # Calculate total estimated size
        self.total_estimated_size = sum(region.target_size for region in self.regions)

    def add_region(self, region: RegionPlan) -> None:
        """Add a region to the plan."""
        self.regions.append(region)
        self.total_estimated_size = sum(region.target_size for region in self.regions)

    def get_region(self, region_id: str) -> Optional[RegionPlan]:
        """Get a region by ID."""
        for region in self.regions:
            if region.region_id == region_id:
                return region
        return None

    def get_regions_by_type(self, region_type: str) -> List[RegionPlan]:
        """Get all regions of a specific type."""
        return [region for region in self.regions if region.region_type == region_type]

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "plan_id": self.plan_id,
            "goal_id": self.goal_id,
            "description": self.description,
            "regions": [region.to_dict() for region in self.regions],
            "total_estimated_size": self.total_estimated_size,
            "estimated_complexity": self.estimated_complexity,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DesignPlan":
        """Create from dictionary."""
        if "regions" in data:
            data["regions"] = [RegionPlan.from_dict(r) for r in data["regions"]]
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
