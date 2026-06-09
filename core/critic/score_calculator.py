"""
ScoreCalculator — combines per-category scores into a final overall_score.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from .models import CriticScore


# Default weights for the final overall_score.
# Tuned to give visual and navigation slightly more influence.
DEFAULT_WEIGHTS: Dict[str, float] = {
    "visual": 0.12,
    "navigation": 0.12,
    "density": 0.10,
    "spawn": 0.13,
    "hunt": 0.12,
    "boss": 0.10,
    "city": 0.08,
    "decor": 0.10,
    "pathfinding": 0.08,
    "region": 0.05,
}


class ScoreCalculator:
    """
    Computes a weighted average of per-category scores.

    Usage:
        calc = ScoreCalculator()
        overall = calc.combine({"visual": 85.0, "navigation": 90.0, ...})
    """

    # Class-level alias of the default weights so callers can introspect
    # ``ScoreCalculator.weights`` without instantiating.
    weights: Dict[str, float] = dict(DEFAULT_WEIGHTS)

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights: Dict[str, float] = dict(weights) if weights else dict(DEFAULT_WEIGHTS)

    def combine(self, scores: Dict[str, float]) -> float:
        """
        Combine a dict of category -> value into a single overall score in [0, 100].

        Missing categories are skipped. The weights of the supplied categories
        are renormalized so the result is independent of which categories are
        present.
        """
        if not scores:
            return 0.0
        active = {k: v for k, v in scores.items() if k in self.weights}
        if not active:
            # No known categories — fall back to simple mean.
            values = [float(v) for v in scores.values()]
            return _clamp(sum(values) / max(len(values), 1))
        total_weight = sum(self.weights[k] for k in active.keys())
        if total_weight <= 0:
            return 0.0
        weighted = sum(float(v) * self.weights[k] for k, v in active.items())
        return _clamp(weighted / total_weight)

    def combine_scores(self, scores: Dict[str, CriticScore]) -> float:
        """Combine CriticScore objects."""
        return self.combine({k: v.value for k, v in scores.items()})

    def penalized(self,
                  scores: Dict[str, float],
                  issues_penalty: float,
                  max_penalty: float = 50.0) -> float:
        """
        Apply a penalty (deducted from the combined score) based on issue severity.
        """
        overall = self.combine(scores)
        penalty = max(0.0, min(max_penalty, issues_penalty))
        return _clamp(overall - penalty)

    @staticmethod
    def issues_penalty(issues: Iterable[Any]) -> float:
        """
        Sum of penalty values from a list of CriticIssue-like objects.

        Each issue contributes its `penalty` property (or default 5.0).
        """
        total = 0.0
        for issue in issues:
            if hasattr(issue, "penalty"):
                try:
                    total += float(issue.penalty)
                except (TypeError, ValueError):
                    total += 5.0
            elif isinstance(issue, dict):
                total += float(issue.get("penalty", 5.0))
        return total


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))
