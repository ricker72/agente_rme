"""Stdlib-only BI-4 similarity metrics."""

from __future__ import annotations

from math import sqrt
from typing import Iterable


def numeric_similarity(a: float | int | None, b: float | int | None) -> float:
    """Return a 0..100 similarity score for two numeric values."""
    if a is None or b is None:
        return 0.0
    left = float(a)
    right = float(b)
    if left == right:
        return 100.0
    scale = max(abs(left), abs(right), 1.0)
    return _clamp_100(100.0 * (1.0 - abs(left - right) / scale))


def categorical_similarity(a: str | None, b: str | None) -> float:
    """Return exact-match categorical similarity."""
    if not a or not b:
        return 0.0
    return 100.0 if a == b else 0.0


def set_similarity(a: Iterable[str] | None, b: Iterable[str] | None) -> float:
    """Return Jaccard similarity scaled to 0..100."""
    if a is None or b is None:
        return 0.0
    left = set(a)
    right = set(b)
    if not left or not right:
        return 0.0
    return _clamp_100(100.0 * len(left & right) / len(left | right))


def bounds_similarity(
    a: dict[str, float | int | None] | None,
    b: dict[str, float | int | None] | None,
) -> float:
    """Compare estimated bounds by dimensions and z range."""
    if not a or not b:
        return 0.0
    dims = []
    for axis in ("x", "y", "z"):
        left = _extent(a, axis)
        right = _extent(b, axis)
        dims.append(numeric_similarity(left, right))
    return sum(dims) / len(dims)


def position_similarity(
    a: dict[str, float | int | None] | None,
    b: dict[str, float | int | None] | None,
    max_distance: float = 512.0,
) -> float:
    """Compare two positions, with z-level receiving an explicit penalty."""
    if not a or not b:
        return 0.0
    ax = a.get("x")
    ay = a.get("y")
    az = a.get("z")
    bx = b.get("x")
    by = b.get("y")
    bz = b.get("z")
    if ax is None or ay is None or az is None or bx is None or by is None or bz is None:
        return 0.0
    dx = float(ax) - float(bx)
    dy = float(ay) - float(by)
    distance = sqrt(dx * dx + dy * dy)
    planar = _clamp_100(100.0 * (1.0 - min(distance, max_distance) / max_distance))
    z_score = numeric_similarity(float(az), float(bz))
    return planar * 0.7 + z_score * 0.3


def weighted_similarity(scores: dict[str, float], weights: dict[str, float]) -> float:
    """Combine dimension scores into a 0..100 weighted score."""
    total_weight = sum(weight for weight in weights.values() if weight > 0)
    if total_weight <= 0:
        return 0.0
    total = 0.0
    for key, weight in weights.items():
        total += _clamp_100(scores.get(key, 0.0)) * max(weight, 0.0)
    return _clamp_100(total / total_weight)


def _extent(bounds: dict[str, float | int | None], axis: str) -> float | None:
    min_value = bounds.get(f"min_{axis}")
    max_value = bounds.get(f"max_{axis}")
    if min_value is None or max_value is None:
        return None
    return float(max_value) - float(min_value) + 1.0


def _clamp_100(value: float) -> float:
    return max(0.0, min(100.0, round(value, 6)))


__all__ = [
    "bounds_similarity",
    "categorical_similarity",
    "numeric_similarity",
    "position_similarity",
    "set_similarity",
    "weighted_similarity",
]
