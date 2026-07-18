"""BI-3D — Dungeon Pattern Extractor.

Transforms Blueprint(type="dungeon") into reusable Pattern objects.

Supported patterns:
    Room Graph Pattern
    Branch Pattern
    Shortcut Pattern
    Key-Lock Pattern
    Boss Access Pattern
"""

from __future__ import annotations

from typing import Any

from core.blueprint_intelligence.models.blueprint import Blueprint
from core.blueprint_intelligence.models.pattern import Pattern


# ---------------------------------------------------------------------------
# Deterministic dungeon pattern definitions (no randomness allowed)
# ---------------------------------------------------------------------------

_DUNGEON_PATTERN_DEFS: list[dict[str, Any]] = [
    {
        "category": "room_graph",
        "name_fmt": "{} Room Graph",
        "pattern_id_fmt": "{}_room_graph",
        "confidence": 0.92,
        "tags_base": ["dungeon", "room", "graph", "layout"],
    },
    {
        "category": "branch",
        "name_fmt": "{} Branch",
        "pattern_id_fmt": "{}_branch",
        "confidence": 0.88,
        "tags_base": ["dungeon", "branch", "fork", "path"],
    },
    {
        "category": "shortcut",
        "name_fmt": "{} Shortcut",
        "pattern_id_fmt": "{}_shortcut",
        "confidence": 0.85,
        "tags_base": ["dungeon", "shortcut", "connector", "secret"],
    },
    {
        "category": "key_lock",
        "name_fmt": "{} Key-Lock",
        "pattern_id_fmt": "{}_key_lock",
        "confidence": 0.83,
        "tags_base": ["dungeon", "key", "lock", "puzzle", "access"],
    },
    {
        "category": "boss_access",
        "name_fmt": "{} Boss Access",
        "pattern_id_fmt": "{}_boss_access",
        "confidence": 0.89,
        "tags_base": ["dungeon", "boss", "access", "gate", "arena"],
    },
]


class DungeonPatternExtractor:
    """Extract dungeon patterns from a Blueprint with type="dungeon".

    Input:  Blueprint(type="dungeon")
    Output: list[Pattern]

    Deterministic — same blueprint always produces same patterns.
    """

    EXTRACTION_VERSION: str = "BI-3D.1"

    def supports(self, blueprint: Blueprint) -> bool:
        """Return True if this extractor can handle the blueprint."""
        return blueprint.blueprint_type == "dungeon"

    def extract(self, blueprint: Blueprint) -> list[Pattern]:
        """Extract dungeon patterns from the blueprint.

        Args:
            blueprint: A Blueprint with blueprint_type == "dungeon".

        Returns:
            A list of Pattern objects derived from the blueprint.

        Raises:
            TypeError: If blueprint is not type "dungeon".
        """
        if not self.supports(blueprint):
            raise TypeError(
                f"DungeonPatternExtractor requires blueprint_type='dungeon', "
                f"got '{blueprint.blueprint_type}'"
            )

        source_name = _derive_source(blueprint)

        patterns: list[Pattern] = []
        for pdef in _DUNGEON_PATTERN_DEFS:
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
    name = blueprint.name.lower().replace(" dungeon", "").replace(" ", "_")
    return name


__all__ = ["DungeonPatternExtractor"]
