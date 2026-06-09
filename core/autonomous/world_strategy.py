"""
World Strategy - defines different strategies for autonomous world design.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from enum import Enum


class StrategyType(Enum):
    """Types of world design strategies."""
    AGGRESSIVE_EXPANSION = "aggressive_expansion"
    BALANCED = "balanced"
    CITY_FOCUSED = "city_focused"
    HUNT_FOCUSED = "hunt_focused"
    BOSS_FOCUSED = "boss_focused"
    CAMPAIGN_FOCUSED = "campaign_focused"


@dataclass
class WorldStrategy:
    """Defines a strategy for autonomous world design."""
    
    strategy_type: StrategyType
    weights: Dict[str, float] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    def __post_init__(self):
        """Initialize default weights if not provided."""
        if not self.weights:
            self.weights = self._get_default_weights()
    
    def _get_default_weights(self) -> Dict[str, float]:
        """Get default weights based on strategy type."""
        defaults = {
            StrategyType.AGGRESSIVE_EXPANSION: {
                "size": 0.3,
                "density": 0.2,
                "difficulty": 0.3,
                "reuse": 0.2,
            },
            StrategyType.BALANCED: {
                "size": 0.2,
                "density": 0.2,
                "difficulty": 0.2,
                "navigation": 0.2,
                "reuse": 0.2,
            },
            StrategyType.CITY_FOCUSED: {
                "city_quality": 0.4,
                "navigation": 0.3,
                "density": 0.2,
                "reuse": 0.1,
            },
            StrategyType.HUNT_FOCUSED: {
                "hunt_quality": 0.4,
                "difficulty": 0.3,
                "density": 0.2,
                "reuse": 0.1,
            },
            StrategyType.BOSS_FOCUSED: {
                "boss_quality": 0.4,
                "difficulty": 0.3,
                "challenge": 0.2,
                "reuse": 0.1,
            },
            StrategyType.CAMPAIGN_FOCUSED: {
                "storyline": 0.3,
                "progression": 0.3,
                "variety": 0.2,
                "reuse": 0.2,
            },
        }
        return defaults.get(self.strategy_type, self._get_balanced_weights())
    
    def _get_balanced_weights(self) -> Dict[str, float]:
        """Get balanced weights as fallback."""
        return {
            "size": 0.2,
            "density": 0.2,
            "difficulty": 0.2,
            "navigation": 0.2,
            "reuse": 0.2,
        }
    
    def apply_strategy(self, metrics: Dict[str, float]) -> float:
        """Apply strategy weights to metrics and return weighted score."""
        if not metrics:
            return 0.0
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric, value in metrics.items():
            weight = self.weights.get(metric, 0.1)  # Default weight for unknown metrics
            total_score += value * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return total_score / total_weight
    
    def get_parameter(self, key: str, default: Any = None) -> Any:
        """Get a strategy parameter."""
        return self.parameters.get(key, default)
    
    def set_parameter(self, key: str, value: Any) -> None:
        """Set a strategy parameter."""
        self.parameters[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "strategy_type": self.strategy_type.value,
            "weights": self.weights,
            "parameters": self.parameters,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorldStrategy":
        """Create from dictionary."""
        data["strategy_type"] = StrategyType(data["strategy_type"])
        return cls(**data)