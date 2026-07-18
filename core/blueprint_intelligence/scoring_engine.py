# mypy: ignore-errors
"""
Blueprint Intelligence 2.0 — Blueprint Scoring Engine.

Measures blueprint quality across 6 dimensions:
  - Pathing (navigation flow)
  - Density (structural richness)
  - Readability (organization clarity)
  - Progression (difficulty ramp / flow)
  - Landmarks (POI quality)
  - Exploration (discoverability)

Produces an aggregate blueprint_score in [0, 100].
"""

from __future__ import annotations

from typing import Dict, Optional

from .models.blueprint_v2 import BlueprintV2


class BlueprintScoringEngine:
    """
    Scores BlueprintV2 objects across 6 dimensions.
    """

    # Weights for each scoring dimension
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "pathing": 0.20,
        "density": 0.15,
        "readability": 0.20,
        "progression": 0.15,
        "landmarks": 0.15,
        "exploration": 0.15,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self.weights = weights or dict(self.DEFAULT_WEIGHTS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def score(self, bp: BlueprintV2) -> Dict[str, float]:
        """
        Compute all quality scores for a blueprint.

        Returns:
            {
                "pathing_score": float,
                "density_score": float,
                "readability_score": float,
                "progression_score": float,
                "landmark_score": float,
                "exploration_score": float,
                "blueprint_score": float,   # weighted aggregate
            }
        """
        pathing = self._score_pathing(bp)
        density = self._score_density(bp)
        readability = self._score_readability(bp)
        progression = self._score_progression(bp)
        landmarks = self._score_landmarks(bp)
        exploration = self._score_exploration(bp)

        blueprint_score = (
            self.weights["pathing"] * pathing
            + self.weights["density"] * density
            + self.weights["readability"] * readability
            + self.weights["progression"] * progression
            + self.weights["landmarks"] * landmarks
            + self.weights["exploration"] * exploration
        )

        return {
            "pathing_score": round(pathing, 2),
            "density_score": round(density, 2),
            "readability_score": round(readability, 2),
            "progression_score": round(progression, 2),
            "landmark_score": round(landmarks, 2),
            "exploration_score": round(exploration, 2),
            "blueprint_score": round(blueprint_score, 2),
        }

    # ------------------------------------------------------------------
    # Dimension scoring
    # ------------------------------------------------------------------

    def _score_pathing(self, bp: BlueprintV2) -> float:
        """
        Score pathing/navigation quality.

        Evaluates whether the blueprint has clear paths,
        adequate waypoints, and road infrastructure.
        """
        score = 0.0

        # Waypoints are critical for pathing
        if bp.waypoints >= 10:
            score += 40.0
        elif bp.waypoints >= 5:
            score += 30.0
        elif bp.waypoints >= 2:
            score += 20.0
        elif bp.waypoints >= 1:
            score += 10.0

        # Roads enable movement
        if bp.roads >= 15:
            score += 35.0
        elif bp.roads >= 8:
            score += 25.0
        elif bp.roads >= 3:
            score += 15.0
        elif bp.roads >= 1:
            score += 5.0

        # Region connectivity (roads per region)
        if bp.regions > 0 and bp.roads > 0:
            connectivity = bp.roads / bp.regions
            if connectivity >= 2.0:
                score += 25.0
            elif connectivity >= 1.0:
                score += 15.0
            else:
                score += 5.0

        return min(100.0, score)

    def _score_density(self, bp: BlueprintV2) -> float:
        """
        Score structural density.

        Evaluates how richly populated the blueprint is
        with structural elements.
        """
        if bp.area == 0:
            return 0.0

        area_norm = bp.area / 10000.0
        score = 0.0

        # Combined structural density
        total_structural = bp.landmarks + bp.roads + bp.districts + bp.spawn_clusters
        structural_density = total_structural / max(1.0, area_norm)

        if structural_density >= 5.0:
            score += 45.0
        elif structural_density >= 2.0:
            score += 35.0
        elif structural_density >= 1.0:
            score += 20.0
        elif structural_density > 0.0:
            score += 10.0

        # Region density
        region_density = bp.regions / max(1.0, area_norm)
        if region_density >= 0.5:
            score += 30.0
        elif region_density >= 0.1:
            score += 20.0
        elif region_density > 0.0:
            score += 10.0

        # District density
        district_density = bp.districts / max(1.0, area_norm)
        if district_density >= 0.3:
            score += 25.0
        elif district_density >= 0.05:
            score += 15.0
        elif district_density > 0.0:
            score += 5.0

        return min(100.0, score)

    def _score_readability(self, bp: BlueprintV2) -> float:
        """
        Score blueprint readability / organization clarity.

        Evaluates whether the blueprint has clear structure
        that is easy to understand and navigate.
        """
        score = 20.0  # Base readability

        # Balanced districts improve readability
        if 3 <= bp.districts <= 6:
            score += 25.0
        elif bp.districts >= 1:
            score += 10.0

        # Regions provide structural clarity
        if 3 <= bp.regions <= 8:
            score += 20.0
        elif bp.regions >= 1:
            score += 10.0

        # Landmarks serve as orientation anchors
        if bp.landmarks >= 4:
            score += 20.0
        elif bp.landmarks >= 2:
            score += 10.0

        # Road network readability
        if bp.roads >= 5 and bp.roads <= 20:
            score += 15.0
        elif bp.roads > 20:
            score += 5.0  # Too many roads can be confusing

        return min(100.0, score)

    def _score_progression(self, bp: BlueprintV2) -> float:
        """
        Score difficulty progression / flow.

        Evaluates whether the blueprint has a natural
        difficulty ramp (spawn clusters, boss presence).
        """
        score = 0.0

        # Spawn clusters indicate possible difficulty zones
        if bp.spawn_clusters >= 15:
            score += 35.0
        elif bp.spawn_clusters >= 8:
            score += 25.0
        elif bp.spawn_clusters >= 3:
            score += 15.0
        elif bp.spawn_clusters >= 1:
            score += 5.0

        # Multiple regions allow progression through zones
        if bp.regions >= 5:
            score += 25.0
        elif bp.regions >= 3:
            score += 15.0
        elif bp.regions >= 1:
            score += 5.0

        # Landmarks can serve as progression checkpoints
        if bp.landmarks >= 5:
            score += 20.0
        elif bp.landmarks >= 2:
            score += 10.0

        # Waypoints for guided progression
        if bp.waypoints >= 8:
            score += 20.0
        elif bp.waypoints >= 3:
            score += 10.0
        elif bp.waypoints >= 1:
            score += 5.0

        return min(100.0, score)

    def _score_landmarks(self, bp: BlueprintV2) -> float:
        """
        Score landmark/POI quality.

        Evaluates the quantity and distribution of landmarks.
        """
        score = 0.0

        # Landmark count
        if bp.landmarks >= 8:
            score += 40.0
        elif bp.landmarks >= 5:
            score += 30.0
        elif bp.landmarks >= 3:
            score += 20.0
        elif bp.landmarks >= 1:
            score += 10.0

        # Landmark-to-region diversity
        if bp.regions > 0 and bp.landmarks > 0:
            ratio = bp.landmarks / bp.regions
            if ratio >= 2.0:
                score += 30.0
            elif ratio >= 1.0:
                score += 20.0
            elif ratio >= 0.5:
                score += 10.0

        # Landmarks in context of area
        if bp.area > 0:
            area_norm = bp.area / 10000.0
            ldmk_density = bp.landmarks / max(1.0, area_norm)
            if 0.3 <= ldmk_density <= 1.5:
                score += 30.0
            elif ldmk_density > 0.0:
                score += 15.0

        return min(100.0, score)

    def _score_exploration(self, bp: BlueprintV2) -> float:
        """
        Score exploration / discoverability.

        Evaluates how much the blueprint rewards exploration.
        """
        score = 10.0  # Base exploration

        # Regions provide exploration variety
        if bp.regions >= 6:
            score += 25.0
        elif bp.regions >= 3:
            score += 15.0
        elif bp.regions >= 1:
            score += 5.0

        # Spawn clusters reward exploration
        if bp.spawn_clusters >= 20:
            score += 20.0
        elif bp.spawn_clusters >= 10:
            score += 15.0
        elif bp.spawn_clusters >= 5:
            score += 10.0
        elif bp.spawn_clusters >= 1:
            score += 5.0

        # Landmarks as discovery points
        if bp.landmarks >= 6:
            score += 20.0
        elif bp.landmarks >= 3:
            score += 15.0
        elif bp.landmarks >= 1:
            score += 5.0

        # Road network enables exploration paths
        if bp.roads >= 10:
            score += 15.0
        elif bp.roads >= 5:
            score += 10.0
        elif bp.roads >= 1:
            score += 5.0

        # District variety
        if bp.districts >= 4:
            score += 10.0
        elif bp.districts >= 1:
            score += 5.0

        return min(100.0, score)
