"""
Goal Manager - manages design goals and determines when to stop the optimization process.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from .models.design_goal import DesignGoal
from .models.design_result import DesignResult


def _normalise_target(value: float) -> float:
    """Normalise a 0-100 score target to 0-1."""
    return value / 100.0 if value > 1.0 else value


@dataclass
class GoalManager:
    """Manages design goals and stop conditions."""

    goals: List[DesignGoal] = field(default_factory=list)
    active_goal: Optional[DesignGoal] = None
    stop_conditions: Dict[str, float] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self):
        """Initialize default stop conditions."""
        if not self.stop_conditions:
            self.stop_conditions = {
                "critic_score": 0.9,  # 0-1 normalised
                "playtest_score": 0.8,  # 0-1 normalised
                "max_iterations": 20,
                "min_improvement": 0.005,
                "convergence_threshold": 0.01,
            }

    def add_goal(self, goal: DesignGoal) -> None:
        """Add a new design goal."""
        self.goals.append(goal)
        if self.active_goal is None:
            self.active_goal = goal

    def set_active_goal(self, goal_id: str) -> bool:
        """Set the active goal by ID."""
        for goal in self.goals:
            if goal.prompt == goal_id:  # Using prompt as ID for simplicity
                self.active_goal = goal
                return True
        return False

    def should_stop(self, result: DesignResult, iteration: int) -> bool:
        """Determine if we should stop the optimization process."""
        if not self.active_goal:
            return True

        # Check iteration limit
        if iteration >= self.stop_conditions.get("max_iterations", 20):
            return True

        # Internal scores are 0-1; user-specified targets may be 0-100.
        critic = result.final_scores.get("critic", 0.0)
        playtest = result.final_scores.get("playtest", 0.0)

        critic_target = _normalise_target(self.stop_conditions.get("critic_score", 0.9))
        if critic >= critic_target:
            return True

        playtest_target = _normalise_target(
            self.stop_conditions.get("playtest_score", 0.8)
        )
        if playtest >= playtest_target:
            return True

        # Don't trigger convergence-based stop too early — let the loop
        # have at least a few iterations to evolve the plan.
        if iteration < 3:
            return False

        # Convergence: last 3 iterations flat
        if len(result.convergence_data) >= 3:
            recent = result.convergence_data[-3:]
            if max(recent) - min(recent) < self.stop_conditions.get(
                "convergence_threshold", 0.01
            ):
                return True

        # No improvement in the last iteration
        if len(result.convergence_data) >= 2:
            improvement = result.convergence_data[-1] - result.convergence_data[-2]
            if improvement < self.stop_conditions.get("min_improvement", 0.005):
                return True

        return False

    def get_progress(self, result: DesignResult) -> Dict[str, Any]:
        """Get the progress towards the active goal."""
        if not self.active_goal:
            return {"status": "no_active_goal"}

        critic_target = _normalise_target(self.active_goal.target_critic_score)
        playtest_target = _normalise_target(self.active_goal.target_playtest_score)

        progress = {
            "critic_score": {
                "current": result.final_scores.get("critic", 0),
                "target": critic_target,
                "achieved": result.final_scores.get("critic", 0) >= critic_target,
            },
            "playtest_score": {
                "current": result.final_scores.get("playtest", 0),
                "target": playtest_target,
                "achieved": result.final_scores.get("playtest", 0) >= playtest_target,
            },
            "iterations": {
                "current": len(result.iterations),
                "max": self.stop_conditions.get("max_iterations", 20),
            },
            "overall_progress": self._calculate_overall_progress(result),
        }

        return progress

    def _calculate_overall_progress(self, result: DesignResult) -> float:
        """Calculate overall progress as a percentage."""
        if not self.active_goal:
            return 0.0

        target_critic = _normalise_target(self.active_goal.target_critic_score)
        target_playtest = _normalise_target(self.active_goal.target_playtest_score)

        progress_sum = 0.0
        total_weight = 0.0

        critic_progress = min(
            1.0, result.final_scores.get("critic", 0) / max(target_critic, 1e-9)
        )
        progress_sum += critic_progress * 0.6  # 60% weight for critic score
        total_weight += 0.6

        playtest_progress = min(
            1.0, result.final_scores.get("playtest", 0) / max(target_playtest, 1e-9)
        )
        progress_sum += playtest_progress * 0.4  # 40% weight for playtest score
        total_weight += 0.4

        if total_weight == 0:
            return 0.0

        return (progress_sum / total_weight) * 100

    def update_stop_condition(self, key: str, value: float) -> None:
        """Update a stop condition."""
        self.stop_conditions[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "goals": [goal.to_dict() for goal in self.goals],
            "active_goal": self.active_goal.to_dict() if self.active_goal else None,
            "stop_conditions": self.stop_conditions,
            "history": self.history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoalManager":
        """Create from dictionary."""
        manager = cls()
        if "goals" in data:
            manager.goals = [DesignGoal.from_dict(g) for g in data["goals"]]
        if "active_goal" in data and data["active_goal"]:
            manager.active_goal = DesignGoal.from_dict(data["active_goal"])
        if "stop_conditions" in data:
            manager.stop_conditions = data["stop_conditions"]
        if "history" in data:
            manager.history = data["history"]
        return manager
