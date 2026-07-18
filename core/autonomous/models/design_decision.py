"""
Design Decision model - represents a decision made by the autonomous decision engine.
"""

from dataclasses import dataclass, field
from typing import Dict, List
from datetime import datetime


@dataclass
class DesignDecision:
    """Represents a decision made by the autonomous decision engine."""

    decision_id: str
    region_id: str
    decision_type: str  # "blueprint", "pattern", "cluster", "hybrid"
    selected_option: str
    alternatives: List[str] = field(default_factory=list)
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    total_score: float = 0.0
    reasoning: str = ""
    confidence: float = 0.0
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate decision after initialization."""
        valid_types = ["blueprint", "pattern", "cluster", "hybrid"]
        if self.decision_type not in valid_types:
            raise ValueError(f"Decision type must be one of {valid_types}")
        if not self.region_id:
            raise ValueError("Region ID cannot be empty")
        if not self.selected_option:
            raise ValueError("Selected option cannot be empty")
        if not (0 <= self.confidence <= 1):
            raise ValueError("Confidence must be between 0 and 1")

        # Calculate total score from breakdown if not provided
        if self.total_score == 0.0 and self.score_breakdown:
            self.total_score = sum(self.score_breakdown.values()) / len(
                self.score_breakdown
            )

    def update_score(self, metric: str, score: float) -> None:
        """Update a specific score metric."""
        self.score_breakdown[metric] = score
        # Recalculate total score
        if self.score_breakdown:
            self.total_score = sum(self.score_breakdown.values()) / len(
                self.score_breakdown
            )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "decision_id": self.decision_id,
            "region_id": self.region_id,
            "decision_type": self.decision_type,
            "selected_option": self.selected_option,
            "alternatives": self.alternatives,
            "score_breakdown": self.score_breakdown,
            "total_score": self.total_score,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DesignDecision":
        """Create from dictionary."""
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
