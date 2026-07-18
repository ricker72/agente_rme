"""Deterministic explanation text for BI-4 similarity scores."""

from __future__ import annotations


def explain_dimensions(dimensions: dict[str, float]) -> list[str]:
    """Build deterministic explanation lines from dimension scores."""
    explanation = []
    for name, score in sorted(dimensions.items()):
        if score >= 85.0:
            explanation.append(_strong_text(name))
        elif score <= 35.0:
            explanation.append(_weak_text(name))
    if not explanation:
        explanation.append("mixed similarity signals")
    return explanation


def strongest_dimensions(dimensions: dict[str, float], limit: int = 2) -> list[str]:
    return [
        name
        for name, _score in sorted(dimensions.items(), key=lambda item: (-item[1], item[0]))[:limit]
    ]


def weakest_dimensions(dimensions: dict[str, float], limit: int = 2) -> list[str]:
    return [
        name
        for name, _score in sorted(dimensions.items(), key=lambda item: (item[1], item[0]))[:limit]
    ]


def _strong_text(name: str) -> str:
    return {
        "bounds": "similar estimated bounds",
        "density_score": "similar spawn density",
        "house_count": "similar house count",
        "metadata": "similar metadata completeness",
        "monster_name": "same monster species",
        "monster_species": "similar monster composition",
        "position": "similar position or z-level",
        "radius": "similar spawn radius",
        "spawn_count": "similar spawn count",
        "spawn_time": "similar spawn time",
        "town_metadata": "similar town/type metadata",
        "z_level": "same z-level",
    }.get(name, f"similar {name}")


def _weak_text(name: str) -> str:
    return {
        "bounds": "different estimated bounds",
        "density_score": "different spawn density",
        "house_count": "different house count",
        "metadata": "different metadata completeness",
        "monster_name": "different monster species",
        "monster_species": "different monster composition",
        "position": "different position or z-level",
        "radius": "different spawn radius",
        "spawn_count": "different spawn count",
        "spawn_time": "different spawn time",
        "town_metadata": "different town/type metadata",
        "z_level": "different z-level",
    }.get(name, f"different {name}")


__all__ = ["explain_dimensions", "strongest_dimensions", "weakest_dimensions"]
