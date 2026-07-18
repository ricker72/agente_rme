# mypy: ignore-errors
"""
Blueprint Intelligence 2.0 — Constraint Builder.

Converts patterns into generation rules consumable by World Generator 2.0.

Takes patterns from the Pattern Library and builds Constraint objects
that encode the structural rules for world generation.
"""

from __future__ import annotations

from typing import List, Optional

from .models.blueprint_v2 import BlueprintV2
from .models.pattern_v2 import PatternV2
from .models.constraint import Constraint
from .pattern_library import PatternLibrary


class ConstraintBuilder:
    """
    Builds generation constraints from patterns and blueprints.

    These constraints are consumed by World Generator 2.0 to
    generate maps that follow the structural rules of a given style.
    """

    def __init__(self, pattern_library: Optional[PatternLibrary] = None):
        self.pattern_library = pattern_library or PatternLibrary()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_from_pattern(self, pattern: PatternV2) -> Constraint:
        """
        Build a constraint from a single pattern.

        Args:
            pattern: PatternV2 to convert to constraints.

        Returns:
            Constraint with rules derived from the pattern.
        """
        return Constraint(
            constraint_id=f"constraint_{pattern.name}",
            name=f"constraint_{pattern.name}",
            value={
                "constraint_type": "structural",
                "source_pattern": pattern.name,
                "source_blueprint": pattern.source_blueprint,
                "confidence": pattern.confidence,
                "min_width": pattern.width,
                "max_width": pattern.width * 3,
                "min_height": pattern.height,
                "max_height": pattern.height * 3,
                "min_connectivity": 0.5,
                "min_landmarks": 1,
                "min_districts": 1,
                "road_pattern": self._infer_road_pattern(pattern),
                "landmark_types": [e for e in pattern.elements if self._is_landmark(e)],
                "district_types": pattern.tags,
                "spawn_types": [e for e in pattern.elements if self._is_spawn_related(e)],
                "min_spawn_clusters": 1,
                "max_spawn_clusters": 5,
                "tags": pattern.tags,
                "metadata": {
                    "source": pattern.source_blueprint,
                    "pattern_type": pattern.pattern_type,
                },
            },
            required=True,
        )

    def build_from_blueprint(self, bp: BlueprintV2) -> List[Constraint]:
        """
        Build constraints from a full blueprint.

        Analyzes the blueprint's structural metrics and creates
        appropriate constraints for each structural aspect.

        Args:
            bp: BlueprintV2 to analyze.

        Returns:
            List of Constraint objects.
        """
        constraints: List[Constraint] = []

        # Structural constraint
        structural = self._build_structural_constraint(bp)
        if structural:
            constraints.append(structural)

        # Density constraint
        density = self._build_density_constraint(bp)
        if density:
            constraints.append(density)

        # Connectivity constraint
        connectivity = self._build_connectivity_constraint(bp)
        if connectivity:
            constraints.append(connectivity)

        # Spawn constraint (if applicable)
        if bp.type in ("hunt", "boss_room", "dungeon"):
            spawn = self._build_spawn_constraint(bp)
            if spawn:
                constraints.append(spawn)

        return constraints

    def build_for_style(self, style: str) -> List[Constraint]:
        """
        Build constraints for a specific style.

        Uses patterns from the library that match the given style.

        Args:
            style: Style name (e.g. "issavi", "roshamuul", "soulwar").

        Returns:
            List of Constraint objects.
        """
        constraints: List[Constraint] = []

        # Get patterns for this source/style
        patterns = self.pattern_library.get_by_source(style.capitalize())

        # Also try by tag
        if not patterns:
            patterns = self.pattern_library.get_by_tag(style.lower())

        for pattern in patterns:
            constraint = self.build_from_pattern(pattern)
            constraints.append(constraint)

        return constraints

    # ------------------------------------------------------------------
    # Constraint builders
    # ------------------------------------------------------------------

    def _build_structural_constraint(self, bp: BlueprintV2) -> Optional[Constraint]:
        """Build a structural constraint from blueprint metrics."""
        if bp.width == 0 and bp.height == 0:
            return None

        return Constraint(
            constraint_id=f"structural_{bp.blueprint_id}",
            name=f"structural_{bp.blueprint_id}",
            value={
                "constraint_type": "structural",
                "source_blueprint": bp.blueprint_id,
                "confidence": 0.85,
                "min_width": bp.width,
                "max_width": bp.width * 2,
                "min_height": bp.height,
                "max_height": bp.height * 2,
                "min_landmarks": max(1, bp.landmarks // 2),
                "min_districts": max(1, bp.districts // 2),
                "landmark_types": bp.tags,
                "district_types": bp.tags,
                "tags": bp.tags,
                "metadata": {"blueprint_type": bp.type, "style": bp.provenance.source},
            },
            required=True,
        )

    def _build_density_constraint(self, bp: BlueprintV2) -> Optional[Constraint]:
        """Build a density constraint from blueprint metrics."""
        if bp.area == 0:
            return None

        area_norm = bp.area / 10000.0

        return Constraint(
            constraint_id=f"density_{bp.blueprint_id}",
            name=f"density_{bp.blueprint_id}",
            value={
                "constraint_type": "density",
                "source_blueprint": bp.blueprint_id,
                "confidence": 0.80,
                "road_density": min(1.0, bp.roads / max(1.0, area_norm)),
                "spawn_density": min(1.0, bp.spawn_clusters / max(1.0, area_norm)),
                "building_density": min(
                    1.0,
                    (bp.landmarks + bp.districts) / max(1.0, area_norm),
                ),
                "min_spawn_clusters": max(1, bp.spawn_clusters // 2),
                "max_spawn_clusters": bp.spawn_clusters * 2,
                "tags": bp.tags,
                "metadata": {"blueprint_type": bp.type},
            },
            required=False,
        )

    def _build_connectivity_constraint(self, bp: BlueprintV2) -> Optional[Constraint]:
        """Build a connectivity constraint from blueprint metrics."""
        return Constraint(
            constraint_id=f"connectivity_{bp.blueprint_id}",
            name=f"connectivity_{bp.blueprint_id}",
            value={
                "constraint_type": "connectivity",
                "source_blueprint": bp.blueprint_id,
                "confidence": 0.80,
                "min_connectivity": 0.5 if bp.roads > 0 else 0.3,
                "min_landmarks": max(1, bp.landmarks // 3),
                "road_pattern": "grid" if bp.roads > 5 else "organic",
                "tags": bp.tags,
            },
            required=True,
        )

    def _build_spawn_constraint(self, bp: BlueprintV2) -> Optional[Constraint]:
        """Build a spawn constraint from blueprint metrics."""
        if bp.spawn_clusters == 0:
            return None

        return Constraint(
            constraint_id=f"spawn_{bp.blueprint_id}",
            name=f"spawn_{bp.blueprint_id}",
            value={
                "constraint_type": "spawn",
                "source_blueprint": bp.blueprint_id,
                "confidence": 0.75,
                "spawn_density": min(1.0, bp.spawn_clusters / max(1, bp.regions)),
                "spawn_types": bp.tags,
                "min_spawn_clusters": max(1, bp.spawn_clusters // 2),
                "max_spawn_clusters": bp.spawn_clusters * 2,
                "tags": bp.tags,
                "metadata": {"blueprint_type": bp.type, "regions": bp.regions},
            },
            required=False,
        )

    # ------------------------------------------------------------------
    # Pattern analysis helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _infer_road_pattern(pattern: PatternV2) -> str:
        """Infer road pattern from pattern type and tags."""
        road_keywords = pattern.tags + [pattern.pattern_type]
        if "grid" in road_keywords:
            return "grid"
        if "loop" in road_keywords or "circular" in road_keywords:
            return "loop"
        if "radial" in road_keywords:
            return "radial"
        return "organic"

    @staticmethod
    def _is_landmark(element: str) -> bool:
        """Check if an element name suggests it's a landmark."""
        landmark_keywords = {
            "fountain", "statue", "building", "tower", "gate",
            "monument", "shrine", "altar", "bridge", "well",
        }
        return any(kw in element.lower() for kw in landmark_keywords)

    @staticmethod
    def _is_spawn_related(element: str) -> bool:
        """Check if an element name suggests spawn-related content."""
        spawn_keywords = {
            "spawn", "monster", "boss", "enemy", "creature",
            "guard", "patrol", "aggro",
        }
        return any(kw in element.lower() for kw in spawn_keywords)
