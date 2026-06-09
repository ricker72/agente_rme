"""
Design Iteration model - represents a single iteration in the optimization loop.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime
from .design_plan import DesignPlan


@dataclass
class DesignIteration:
    """Represents a single iteration in the optimization loop."""
    
    iteration_id: int
    plan_snapshot: DesignPlan
    scores: Dict[str, float] = field(default_factory=dict)
    critic_score: float = 0.0
    playtest_score: float = 0.0
    navigation_score: float = 0.0
    density_score: float = 0.0
    reuse_score: float = 0.0
    improvements: List[str] = field(default_factory=list)
    regressions: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate iteration after initialization."""
        if self.iteration_id < 0:
            raise ValueError("Iteration ID cannot be negative")
        if not self.plan_snapshot:
            raise ValueError("Plan snapshot cannot be empty")
        
        # Update scores from individual metrics
        self.scores.update({
            "critic": self.critic_score,
            "playtest": self.playtest_score,
            "navigation": self.navigation_score,
            "density": self.density_score,
            "reuse": self.reuse_score,
        })
    
    def update_scores(self, **kwargs) -> None:
        """Update multiple scores at once."""
        for key, value in kwargs.items():
            if hasattr(self, f"{key}_score"):
                setattr(self, f"{key}_score", value)
                self.scores[key] = value
    
    def get_score(self, metric: str) -> float:
        """Get a specific score by metric name."""
        return self.scores.get(metric, 0.0)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "iteration_id": self.iteration_id,
            "plan_snapshot": self.plan_snapshot.to_dict(),
            "scores": self.scores,
            "critic_score": self.critic_score,
            "playtest_score": self.playtest_score,
            "navigation_score": self.navigation_score,
            "density_score": self.density_score,
            "reuse_score": self.reuse_score,
            "improvements": self.improvements,
            "regressions": self.regressions,
            "duration_seconds": self.duration_seconds,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DesignIteration":
        """Create from dictionary."""
        if "plan_snapshot" in data:
            data["plan_snapshot"] = DesignPlan.from_dict(data["plan_snapshot"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)