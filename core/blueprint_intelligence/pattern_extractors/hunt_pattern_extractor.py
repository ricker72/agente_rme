"""BI-3C — Hunt Pattern Extractor.

Transforms Blueprint(type="hunt") into reusable Pattern objects.

Supported patterns:
    Spawn Cluster Pattern
    Hunt Loop Pattern
    Progression Pattern
    Risk Zone Pattern
    Reward Zone Pattern

Examples:
    roshamuul_loop, roshamuul_cluster
"""

from __future__ import annotations

from typing import Any

from core.blueprint_intelligence.models.blueprint import Blueprint
from core.blueprint_intelligence.models.pattern import Pattern


# ---------------------------------------------------------------------------
# Deterministic hunt pattern definitions (no randomness allowed)
# ---------------------------------------------------------------------------

_HUNT_PATTERN_DEFS: list[dict[str, Any]] = [
    {
        "category": "spawn_cluster",
        "name_fmt": "{} Spawn Cluster",
        "pattern_id_fmt": "{}_spawn_cluster",
        "confidence": 0.93,
        "tags_base": ["hunt", "spawn", "cluster", "combat"],
    },
    {
        "category": "hunt_loop",
        "name_fmt": "{} Hunt Loop",
        "pattern_id_fmt": "{}_hunt_loop",
        "confidence": 0.90,
        "tags_base": ["hunt", "loop", "circuit", "path"],
    },
    {
        "category": "progression",
        "name_fmt": "{} Progression",
        "pattern_id_fmt": "{}_progression",
        "confidence": 0.86,
        "tags_base": ["hunt", "progression", "difficulty"],
    },
    {
        "category": "risk_zone",
        "name_fmt": "{} Risk Zone",
        "pattern_id_fmt": "{}_risk_zone",
        "confidence": 0.84,
        "tags_base": ["hunt", "risk", "danger", "high_level"],
    },
    {
        "category": "reward_zone",
        "name_fmt": "{} Reward Zone",
        "pattern_id_fmt": "{}_reward_zone",
        "confidence": 0.82,
        "tags_base": ["hunt", "reward", "loot", "treasure"],
    },
]


class HuntPatternExtractor:
    """Extract hunt patterns from a Blueprint with type="hunt".

    Input:  Blueprint(type="hunt")
    Output: list[Pattern]

    Deterministic — same blueprint always produces same patterns.
    """

    EXTRACTION_VERSION: str = "BI-3C.1"

    def supports(self, blueprint: Blueprint) -> bool:
        """Return True if this extractor can handle the blueprint."""
        return blueprint.blueprint_type == "hunt"

    def extract(self, blueprint: Blueprint) -> list[Pattern]:
        """Extract hunt patterns from the blueprint.

        Args:
            blueprint: A Blueprint with blueprint_type == "hunt".

        Returns:
            A list of Pattern objects derived from the blueprint.

        Raises:
            TypeError: If blueprint is not type "hunt".
        """
        if not self.supports(blueprint):
            raise TypeError(
                f"HuntPatternExtractor requires blueprint_type='hunt', "
                f"got '{blueprint.blueprint_type}'"
            )

        source_name = _derive_source(blueprint)

        patterns: list[Pattern] = []
        for pdef in _HUNT_PATTERN_DEFS:
            pattern_id = pdef["pattern_id_fmt"].format(source_name)
            name = pdef["name_fmt"].format(blueprint.name)
            tags = [source_name] + list(pdef["tags_base"])
            pattern = Pattern(
                pattern_id=pattern_id,
                name=name,
                category=pdef["category"],
                source=blueprint.name,
                confidence=pdef["confidence"],
                tags=tags,
            )
            patterns.append(pattern)

        return patterns


def _derive_source(blueprint: Blueprint) -> str:
    """Derive a short source key from a blueprint name."""
    name = blueprint.name.lower().replace(" hunt", "").replace(" ", "_")
    return name


__all__ = ["HuntPatternExtractor"]
