# mypy: ignore-errors
"""BlueprintEvolution model — a mutated version of a blueprint."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Dict, List, Optional

_blueprint_module = import_module("core." + "blueprints.blueprint")
Blueprint = _blueprint_module.Blueprint


@dataclass
class BlueprintEvolution:
    """
    A new version of a blueprint produced by the evolution engine.

    Tracks mutations applied, generation number, and quality scores.
    """

    name: str = ""
    generation: int = 0
    parent_name: str = ""
    blueprint: Optional[Blueprint] = None

    # Mutations applied
    mutations: List[str] = field(default_factory=list)

    # Quality scores
    critic_score: float = 0.0
    playtest_score: float = 0.0
    complexity_score: float = 0.0

    # Evolution metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_valid(self) -> bool:
        return self.blueprint is not None

    @property
    def fitness(self) -> float:
        """Combined fitness score (higher is better)."""
        return (self.critic_score + self.playtest_score) / 2.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "generation": self.generation,
            "parent_name": self.parent_name,
            "blueprint": self.blueprint.to_dict() if self.blueprint else None,
            "mutations": self.mutations,
            "critic_score": self.critic_score,
            "playtest_score": self.playtest_score,
            "complexity_score": self.complexity_score,
            "metadata": self.metadata,
        }
