"""BI-3B — City Pattern Extractor.

Transforms Blueprint(type="city") into reusable Pattern objects.

Supported patterns:
    Plaza Pattern
    District Pattern
    Road Pattern
    Landmark Pattern
    Entrance Pattern

Examples:
    issavi_plaza, issavi_market, issavi_district
"""

from __future__ import annotations

from typing import Any

from core.blueprint_intelligence.models.blueprint import Blueprint
from core.blueprint_intelligence.models.pattern import Pattern


# ---------------------------------------------------------------------------
# Deterministic city pattern definitions (no randomness allowed)
# ---------------------------------------------------------------------------

_CITY_PATTERN_DEFS: list[dict[str, Any]] = [
    {
        "category": "plaza",
        "name_fmt": "{} Plaza",
        "pattern_id_fmt": "{}_plaza",
        "confidence": 0.94,
        "tags_base": ["city", "plaza", "social_hub"],
    },
    {
        "category": "market",
        "name_fmt": "{} Market",
        "pattern_id_fmt": "{}_market",
        "confidence": 0.91,
        "tags_base": ["city", "market", "commerce"],
    },
    {
        "category": "district",
        "name_fmt": "{} District",
        "pattern_id_fmt": "{}_district",
        "confidence": 0.88,
        "tags_base": ["city", "district", "residential"],
    },
    {
        "category": "road",
        "name_fmt": "{} Road",
        "pattern_id_fmt": "{}_road",
        "confidence": 0.90,
        "tags_base": ["city", "road", "connector"],
    },
    {
        "category": "landmark",
        "name_fmt": "{} Landmark",
        "pattern_id_fmt": "{}_landmark",
        "confidence": 0.85,
        "tags_base": ["city", "landmark", "point_of_interest"],
    },
    {
        "category": "entrance",
        "name_fmt": "{} Entrance",
        "pattern_id_fmt": "{}_entrance",
        "confidence": 0.87,
        "tags_base": ["city", "entrance", "gate"],
    },
]


class CityPatternExtractor:
    """Extract city patterns from a Blueprint with type="city".

    Input:  Blueprint(type="city")
    Output: list[Pattern]

    Deterministic — same blueprint always produces same patterns.
    """

    EXTRACTION_VERSION: str = "BI-3B.1"

    def supports(self, blueprint: Blueprint) -> bool:
        """Return True if this extractor can handle the blueprint."""
        return blueprint.blueprint_type == "city"

    def extract(self, blueprint: Blueprint) -> list[Pattern]:
        """Extract city patterns from the blueprint.

        Args:
            blueprint: A Blueprint with blueprint_type == "city".

        Returns:
            A list of Pattern objects derived from the blueprint.

        Raises:
            TypeError: If blueprint is not type "city".
        """
        if not self.supports(blueprint):
            raise TypeError(
                f"CityPatternExtractor requires blueprint_type='city', "
                f"got '{blueprint.blueprint_type}'"
            )

        # Derive a short name from the blueprint (e.g. "Issavi City" -> "issavi")
        source_name = _derive_source(blueprint)

        patterns: list[Pattern] = []
        for pdef in _CITY_PATTERN_DEFS:
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
    """Derive a short source key from a blueprint name.

    Examples:
        "Issavi City" -> "issavi"
        "Roshamuul"   -> "roshamuul"
        "Soul War"    -> "soulwar"
    """
    name = blueprint.name.lower().replace(" city", "").replace(" ", "_")
    return name


__all__ = ["CityPatternExtractor"]
