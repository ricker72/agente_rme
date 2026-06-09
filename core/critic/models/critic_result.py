"""
CriticResult — aggregated critic output for a map.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .critic_score import CriticScore
from .critic_issue import CriticIssue
from .critic_recommendation import CriticRecommendation


@dataclass
class CriticCategoryResult:
    """
    The result of analyzing a single category (e.g. "visual", "navigation").

    Attributes:
        category: Name of the category.
        score: The score for this category.
        issues: Issues detected.
        recommendations: Recommendations for improvement.
        metrics: Optional raw metrics produced by the analyzer.
    """

    category: str
    score: CriticScore
    issues: List[CriticIssue] = field(default_factory=list)
    recommendations: List[CriticRecommendation] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "score": self.score.to_dict(),
            "issues": [i.to_dict() for i in self.issues],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "metrics": self.metrics,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriticCategoryResult":
        return cls(
            category=data.get("category", "general"),
            score=CriticScore.from_dict(data.get("score", {"category": "general", "value": 0.0})),
            issues=[CriticIssue.from_dict(i) for i in data.get("issues", [])],
            recommendations=[CriticRecommendation.from_dict(r) for r in data.get("recommendations", [])],
            metrics=data.get("metrics", {}) or {},
        )


@dataclass
class CriticResult:
    """
    The final aggregated critic result for a map.

    Attributes:
        map_name: Optional identifier for the analyzed map.
        scores: Per-category scores.
        issues: All issues detected.
        recommendations: All recommendations.
        overall_score: A single representative score (0-100).
        timestamp: ISO-8601 timestamp of the analysis.
        metadata: Additional information about the analysis.
    """

    map_name: str = ""
    scores: Dict[str, CriticScore] = field(default_factory=dict)
    issues: List[CriticIssue] = field(default_factory=list)
    recommendations: List[CriticRecommendation] = field(default_factory=list)
    overall_score: float = 0.0
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.datetime.utcnow().isoformat()
        # Clamp overall score
        try:
            v = float(self.overall_score)
        except (TypeError, ValueError):
            v = 0.0
        self.overall_score = max(0.0, min(100.0, v))

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    def get_score(self, category: str) -> Optional[CriticScore]:
        return self.scores.get(category)

    @property
    def visual_score(self) -> float:
        return self._score("visual")

    @property
    def navigation_score(self) -> float:
        return self._score("navigation")

    @property
    def density_score(self) -> float:
        return self._score("density")

    @property
    def spawn_score(self) -> float:
        return self._score("spawn")

    @property
    def hunt_score(self) -> float:
        return self._score("hunt")

    @property
    def boss_score(self) -> float:
        return self._score("boss")

    @property
    def city_score(self) -> float:
        return self._score("city")

    @property
    def decor_score(self) -> float:
        return self._score("decor")

    @property
    def pathfinding_score(self) -> float:
        return self._score("pathfinding")

    def _score(self, name: str) -> float:
        s = self.scores.get(name)
        return s.value if s else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "map_name": self.map_name,
            "overall_score": round(self.overall_score, 2),
            "visual_score": round(self.visual_score, 2),
            "navigation_score": round(self.navigation_score, 2),
            "density_score": round(self.density_score, 2),
            "spawn_score": round(self.spawn_score, 2),
            "hunt_score": round(self.hunt_score, 2),
            "boss_score": round(self.boss_score, 2),
            "city_score": round(self.city_score, 2),
            "decor_score": round(self.decor_score, 2),
            "pathfinding_score": round(self.pathfinding_score, 2),
            "scores": {k: v.to_dict() for k, v in self.scores.items()},
            "issues": [i.to_dict() for i in self.issues],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriticResult":
        scores_raw = data.get("scores", {}) or {}
        scores: Dict[str, CriticScore] = {}
        for k, v in scores_raw.items():
            if isinstance(v, dict):
                scores[k] = CriticScore.from_dict(v)
        return cls(
            map_name=data.get("map_name", ""),
            scores=scores,
            issues=[CriticIssue.from_dict(i) for i in data.get("issues", [])],
            recommendations=[CriticRecommendation.from_dict(r) for r in data.get("recommendations", [])],
            overall_score=data.get("overall_score", 0.0),
            timestamp=data.get("timestamp", ""),
            metadata=data.get("metadata", {}) or {},
        )
