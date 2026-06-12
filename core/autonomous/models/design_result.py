"""
Design Result model - represents the final result of the autonomous design process.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime
from .design_plan import DesignPlan
from .design_iteration import DesignIteration
from .design_decision import DesignDecision


@dataclass
class DesignResult:
    """Represents the final result of the autonomous design process."""

    result_id: str
    goal_id: str
    plan: DesignPlan
    iterations: List[DesignIteration] = field(default_factory=list)
    decisions: List[DesignDecision] = field(default_factory=list)
    final_world: Any = None  # The actual generated world data
    final_scores: Dict[str, float] = field(default_factory=dict)
    convergence_data: List[float] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    success: bool = False
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate result after initialization."""
        if not self.result_id:
            raise ValueError("Result ID cannot be empty")
        if not self.goal_id:
            raise ValueError("Goal ID cannot be empty")
        if not self.plan:
            raise ValueError("Plan cannot be empty")

        # Extract final scores from last iteration if available
        if self.iterations:
            last_iteration = self.iterations[-1]
            self.final_scores = {
                "critic": last_iteration.critic_score,
                "playtest": last_iteration.playtest_score,
                "navigation": last_iteration.navigation_score,
                "density": last_iteration.density_score,
                "reuse": last_iteration.reuse_score,
            }
            self.convergence_data = [iter.critic_score for iter in self.iterations]

    def add_iteration(self, iteration: DesignIteration) -> None:
        """Add an iteration to the result."""
        self.iterations.append(iteration)
        # Update convergence data
        self.convergence_data.append(iteration.critic_score)
        # Update final scores
        self.final_scores = {
            "critic": iteration.critic_score,
            "playtest": iteration.playtest_score,
            "navigation": iteration.navigation_score,
            "density": iteration.density_score,
            "reuse": iteration.reuse_score,
        }

    def add_decision(self, decision: DesignDecision) -> None:
        """Add a decision to the result."""
        self.decisions.append(decision)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the result."""
        return {
            "result_id": self.result_id,
            "goal_id": self.goal_id,
            "total_iterations": len(self.iterations),
            "total_decisions": len(self.decisions),
            "final_scores": self.final_scores,
            "convergence_achieved": len(self.convergence_data) > 1
            and abs(self.convergence_data[-1] - self.convergence_data[-2]) < 0.1,
            "total_duration_seconds": self.total_duration_seconds,
            "success": self.success,
        }

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "result_id": self.result_id,
            "goal_id": self.goal_id,
            "plan": self.plan.to_dict(),
            "iterations": [iter.to_dict() for iter in self.iterations],
            "decisions": [dec.to_dict() for dec in self.decisions],
            "final_scores": self.final_scores,
            "convergence_data": self.convergence_data,
            "total_duration_seconds": self.total_duration_seconds,
            "success": self.success,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DesignResult":
        """Create from dictionary."""
        if "plan" in data:
            data["plan"] = DesignPlan.from_dict(data["plan"])
        if "iterations" in data:
            data["iterations"] = [
                DesignIteration.from_dict(i) for i in data["iterations"]
            ]
        if "decisions" in data:
            data["decisions"] = [DesignDecision.from_dict(d) for d in data["decisions"]]
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
