# mypy: ignore-errors
"""
Blueprint Intelligence 2.0 — Blueprint Analyzer v2.

Analyzes blueprint structure across multiple dimensions:
  - Connectivity (how well zones connect)
  - Density (tile fill ratio / structural density)
  - Pathing (navigation flow, corridor quality)
  - Landmark Placement (POI distribution)
  - District Layout (zone organization)
  - Spawn Distribution (monster placement)
  - POI Placement (point-of-interest arrangement)

Generates normalized scores in [0, 100] for each dimension.
"""

from __future__ import annotations

from typing import Dict

from .models.blueprint_v2 import BlueprintV2


class BlueprintAnalyzerV2:
    """
    Analyzes BlueprintV2 structural quality across 7 dimensions.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, bp: BlueprintV2) -> Dict[str, float]:
        """
        Run all analysis dimensions on a blueprint.

        Returns:
            Dict with scores: {
                "connectivity_score": float,
                "density_score": float,
                "navigation_score": float,
                "landmark_placement": float,
                "district_layout": float,
                "spawn_distribution": float,
                "poi_placement": float,
            }
        """
        return {
            "connectivity_score": self._analyze_connectivity(bp),
            "density_score": self._analyze_density(bp),
            "navigation_score": self._analyze_pathing(bp),
            "landmark_placement": self._analyze_landmark_placement(bp),
            "district_layout": self._analyze_district_layout(bp),
            "spawn_distribution": self._analyze_spawn_distribution(bp),
            "poi_placement": self._analyze_poi_placement(bp),
        }

    # ------------------------------------------------------------------
    # Connectivity Analysis
    # ------------------------------------------------------------------

    def _analyze_connectivity(self, bp: BlueprintV2) -> float:
        """
        Score how well the blueprint's zones connect to each other.

        Factors:
          - Has at least 1 connection per region
          - Road count relative to region count
          - Waypoints indicating paths
          - Has entry point
        """
        score = 0.0

        # Road-to-region ratio: ideally 1.5+ roads per region
        if bp.regions > 0 and bp.roads > 0:
            ratio = bp.roads / bp.regions
            if ratio >= 2.0:
                score += 40.0
            elif ratio >= 1.0:
                score += 30.0
            else:
                score += 20.0
        elif bp.roads > 0:
            score += 20.0

        # Waypoints indicate path planning
        if bp.waypoints >= 3:
            score += 30.0
        elif bp.waypoints >= 1:
            score += 15.0

        # Regions indicate organized zones
        if bp.regions >= 3:
            score += 20.0
        elif bp.regions >= 1:
            score += 10.0

        # Landmarks serve as orientation points
        if bp.landmarks >= 2:
            score += 10.0
        elif bp.landmarks >= 1:
            score += 5.0

        return min(100.0, score)

    # ------------------------------------------------------------------
    # Density Analysis
    # ------------------------------------------------------------------

    def _analyze_density(self, bp: BlueprintV2) -> float:
        """
        Score structural density.

        Factors:
          - Landmarks per area
          - Districts per area
          - Spawn clusters per area
          - Roads per area
        """
        if bp.area == 0:
            return 0.0

        area_normalized = bp.area / 10000.0  # Normalize to ~100x100 map basis

        score = 0.0

        # Landmark density
        if bp.landmarks > 0:
            ldmk_density = bp.landmarks / max(1.0, area_normalized)
            if ldmk_density >= 0.5:
                score += 25.0
            elif ldmk_density >= 0.1:
                score += 15.0
            else:
                score += 5.0

        # District density
        if bp.districts > 0:
            dist_density = bp.districts / max(1.0, area_normalized)
            if dist_density >= 0.3:
                score += 25.0
            elif dist_density >= 0.1:
                score += 15.0
            else:
                score += 5.0

        # Spawn density
        if bp.spawn_clusters > 0:
            spawn_density = bp.spawn_clusters / max(1.0, area_normalized)
            if spawn_density >= 1.0:
                score += 25.0
            elif spawn_density >= 0.3:
                score += 15.0
            else:
                score += 5.0

        # Road density
        if bp.roads > 0:
            road_density = bp.roads / max(1.0, area_normalized)
            if road_density >= 0.5:
                score += 25.0
            elif road_density >= 0.1:
                score += 15.0
            else:
                score += 5.0

        return min(100.0, score)

    # ------------------------------------------------------------------
    # Pathing Analysis
    # ------------------------------------------------------------------

    def _analyze_pathing(self, bp: BlueprintV2) -> float:
        """
        Score navigation flow / pathing quality.

        Factors:
          - Adequate waypoints for navigation
          - Roads enable movement
          - Regions have connections (implicitly through roads)
          - Scale-appropriate features
        """
        score = 0.0

        # Waypoints indicate designed paths
        if bp.waypoints >= 5:
            score += 35.0
        elif bp.waypoints >= 2:
            score += 25.0
        elif bp.waypoints >= 1:
            score += 10.0

        # Roads are navigation arteries
        if bp.roads >= 10:
            score += 30.0
        elif bp.roads >= 5:
            score += 20.0
        elif bp.roads >= 1:
            score += 10.0

        # Region diversity supports varied navigation
        if bp.regions >= 5:
            score += 20.0
        elif bp.regions >= 2:
            score += 10.0

        # Landmarks serve as navigation anchors
        if bp.landmarks >= 3:
            score += 15.0
        elif bp.landmarks >= 1:
            score += 5.0

        return min(100.0, score)

    # ------------------------------------------------------------------
    # Landmark Placement Analysis
    # ------------------------------------------------------------------

    def _analyze_landmark_placement(self, bp: BlueprintV2) -> float:
        """
        Score landmark placement quality.

        Factors:
          - Absolute landmark count
          - Landmark-to-region ratio (diverse placement)
          - Landmark-to-area ratio
        """
        score = 0.0

        # Absolute landmark count
        if bp.landmarks >= 7:
            score += 40.0
        elif bp.landmarks >= 4:
            score += 30.0
        elif bp.landmarks >= 2:
            score += 20.0
        elif bp.landmarks >= 1:
            score += 10.0

        # Landmarks per region (diversity)
        if bp.regions > 0 and bp.landmarks > 0:
            ratio = bp.landmarks / bp.regions
            if ratio >= 1.5:
                score += 35.0
            elif ratio >= 1.0:
                score += 25.0
            elif ratio >= 0.5:
                score += 15.0
            else:
                score += 5.0
        elif bp.landmarks > 0:
            score += 10.0

        # Bonus for having multiple landmarks in a large area
        if bp.area > 0 and bp.landmarks >= 3:
            score += 25.0

        return min(100.0, score)

    # ------------------------------------------------------------------
    # District Layout Analysis
    # ------------------------------------------------------------------

    def _analyze_district_layout(self, bp: BlueprintV2) -> float:
        """
        Score district layout organization.

        Factors:
          - District count (enough for structure, not too many)
          - District-to-region alignment
          - Scale match
        """
        score = 0.0

        # Optimal district count (3-8 is ideal for most maps)
        if 3 <= bp.districts <= 8:
            score += 50.0
        elif 1 <= bp.districts <= 2:
            score += 30.0
        elif bp.districts >= 9:
            score += 25.0
        else:
            score += 0.0

        # District alignment with regions
        if bp.regions > 0 and bp.districts > 0:
            alignment = 1.0 - abs(bp.districts - bp.regions) / max(
                bp.districts, bp.regions
            )
            score += alignment * 30.0

        # Scale: large maps need more districts
        if bp.area >= 250000 and bp.districts >= 4:  # 500x500+
            score += 20.0
        elif bp.area >= 10000 and bp.districts >= 2:  # 100x100+
            score += 10.0

        return min(100.0, score)

    # ------------------------------------------------------------------
    # Spawn Distribution Analysis
    # ------------------------------------------------------------------

    def _analyze_spawn_distribution(self, bp: BlueprintV2) -> float:
        """
        Score spawn distribution quality.

        Factors:
          - Spawn cluster count (adequate for map size)
          - Spawn-per-area ratio
        """
        if bp.area == 0:
            return 0.0

        score = 0.0

        area_normalized = bp.area / 10000.0

        # Absolute spawn cluster count
        if bp.spawn_clusters >= 20:
            score += 40.0
        elif bp.spawn_clusters >= 10:
            score += 30.0
        elif bp.spawn_clusters >= 5:
            score += 20.0
        elif bp.spawn_clusters >= 1:
            score += 10.0

        # Spawn density (normalized)
        spawn_density = bp.spawn_clusters / max(1.0, area_normalized)
        if 0.5 <= spawn_density <= 3.0:
            score += 35.0  # Optimal range
        elif spawn_density > 3.0:
            score += 20.0  # Dense but acceptable
        elif spawn_density > 0.0:
            score += 15.0  # Sparse

        # Distinct from other metrics bonus
        if bp.spawn_clusters > 0 and bp.regions > 0:
            spawn_per_region = bp.spawn_clusters / bp.regions
            if 2.0 <= spawn_per_region <= 8.0:
                score += 25.0

        return min(100.0, score)

    # ------------------------------------------------------------------
    # POI Placement Analysis
    # ------------------------------------------------------------------

    def _analyze_poi_placement(self, bp: BlueprintV2) -> float:
        """
        Score POI (Point of Interest) placement quality.

        Factors:
          - Landmarks (primary POIs)
          - Waypoints (secondary POIs)
          - Combined POI density
        """
        score = 0.0

        # Combined POIs
        total_pois = bp.landmarks + bp.waypoints

        if total_pois >= 15:
            score += 45.0
        elif total_pois >= 8:
            score += 35.0
        elif total_pois >= 4:
            score += 25.0
        elif total_pois >= 1:
            score += 10.0

        # POI-to-area balance
        if bp.area > 0:
            area_normalized = bp.area / 10000.0
            poi_density = total_pois / max(1.0, area_normalized)
            if 0.2 <= poi_density <= 2.0:
                score += 30.0
            elif poi_density > 0.0:
                score += 15.0

        # Landmark-to-waypoint balance (both types contribute)
        if bp.landmarks > 0 and bp.waypoints > 0:
            balance = 1.0 - abs(bp.landmarks - bp.waypoints) / max(
                bp.landmarks, bp.waypoints
            )
            score += balance * 25.0

        return min(100.0, score)
