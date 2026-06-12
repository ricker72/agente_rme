"""
SpawnAnalyzer — analyzes monster spawn distribution and density.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Set, Tuple

from core.world.world_model import WorldModel

from .base_analyzer import (
    build_snapshots,
    snapshots_by_zone,
    manhattan,
    safe_ratio,
    clamp,
    average,
)

logger = logging.getLogger(__name__)


class SpawnAnalyzer:
    """
    Computes spawn_score in [0, 100] by analyzing:
      - distance between spawns
      - spawn density per zone
      - coverage (no huge empty gaps)
      - clusters of spawns
    """

    CATEGORY = "spawn"
    TARGET_SPAWN_DENSITY = 0.05  # 5% of grounded tiles
    IDEAL_MIN_DISTANCE = 4
    IDEAL_MAX_DISTANCE = 20

    def __init__(
        self,
        target_density: float = TARGET_SPAWN_DENSITY,
        ideal_min_distance: int = IDEAL_MIN_DISTANCE,
        ideal_max_distance: int = IDEAL_MAX_DISTANCE,
    ):
        self.target_density = target_density
        self.ideal_min_distance = ideal_min_distance
        self.ideal_max_distance = ideal_max_distance

    def analyze(self, world: WorldModel) -> Dict[str, Any]:
        from ..models import (
            CriticScore,
            CriticIssue,
            CriticRecommendation,
            IssueType,
            IssueSeverity,
            RecommendationPriority,
        )

        snapshots = build_snapshots(world)
        spawn_snaps = [s for s in snapshots if s.has_spawn]
        grounded = [s for s in snapshots if s.ground is not None]

        total_spawns = len(spawn_snaps)
        total_ground = len(grounded)
        if total_ground == 0:
            return {
                "category": self.CATEGORY,
                "score": CriticScore(self.CATEGORY, 0.0, notes="No grounded tiles"),
                "issues": [],
                "recommendations": [],
                "metrics": {"total_spawns": 0, "grounded_tiles": 0},
            }

        # Density
        density = safe_ratio(total_spawns, total_ground)
        density_score = 100.0
        if density < self.target_density:
            density_score = max(0.0, density / self.target_density * 100.0)
        elif density > self.target_density * 3:
            density_score = max(0.0, 100.0 - (density - self.target_density * 3) * 50.0)

        # Inter-spawn distances
        distances: List[int] = []
        if len(spawn_snaps) > 1:
            # Sample up to 100 random spawns to keep cost bounded
            sample = spawn_snaps[:100] if len(spawn_snaps) > 100 else spawn_snaps
            for i, a in enumerate(sample):
                nearest = float("inf")
                for j, b in enumerate(sample):
                    if i == j:
                        continue
                    d = manhattan((a.x, a.y), (b.x, b.y))
                    if d < nearest:
                        nearest = d
                if nearest < float("inf"):
                    distances.append(int(nearest))

        if distances:
            min_d = min(distances)
            max_d = max(distances)
            avg_d = average(distances)
        else:
            min_d = max_d = avg_d = 0

        # Cluster detection: spawns within ideal_min_distance of each other
        clusters: List[List[Tuple[int, int]]] = []
        used: Set[int] = set()
        for i, a in enumerate(spawn_snaps):
            if i in used:
                continue
            cluster = [i]
            used.add(i)
            for j, b in enumerate(spawn_snaps):
                if j in used:
                    continue
                if manhattan((a.x, a.y), (b.x, b.y)) <= self.ideal_min_distance:
                    cluster.append(j)
                    used.add(j)
            if len(cluster) > 1:
                clusters.append([(spawn_snaps[k].x, spawn_snaps[k].y) for k in cluster])

        # Coverage: percentage of "spawn zones" that have at least one spawn
        by_zone = snapshots_by_zone(spawn_snaps)
        zones_with_spawns = sum(1 for _, items in by_zone.items() if items)
        zone_coverage = safe_ratio(zones_with_spawns, max(len(by_zone), 1))

        # Score
        # 50% density, 30% distance distribution, 20% coverage
        dist_score = 100.0
        if distances:
            # Penalize if most distances are below ideal_min or above ideal_max
            too_close = sum(1 for d in distances if d < self.ideal_min_distance)
            too_far = sum(1 for d in distances if d > self.ideal_max_distance)
            dist_score = max(
                0.0, 100.0 - (too_close + too_far) / len(distances) * 100.0
            )
        score_value = (
            density_score * 0.5 + dist_score * 0.3 + zone_coverage * 100.0 * 0.2
        )
        score_value = clamp(score_value)

        score = CriticScore(
            category=self.CATEGORY,
            value=score_value,
            breakdown={
                "density_score": round(density_score, 2),
                "distance_score": round(dist_score, 2),
                "zone_coverage": round(zone_coverage * 100.0, 2),
                "spawn_density": round(density * 100.0, 4),
            },
        )

        issues: List = []
        recs: List = []

        if total_spawns == 0:
            issues.append(
                CriticIssue(
                    issue_type=IssueType.LOW_SPAWN_DENSITY,
                    severity=IssueSeverity.CRITICAL,
                    category=self.CATEGORY,
                    message="No monster spawns in the world",
                )
            )
            recs.append(
                CriticRecommendation(
                    title="Add monster spawns",
                    description="Place monster spawns in hunt areas. Aim for ~5% of grounded tiles.",
                    category=self.CATEGORY,
                    priority=RecommendationPriority.CRITICAL,
                )
            )
        elif density < self.target_density * 0.5:
            issues.append(
                CriticIssue(
                    issue_type=IssueType.LOW_SPAWN_DENSITY,
                    severity=IssueSeverity.WARNING,
                    category=self.CATEGORY,
                    message=f"Spawn density {density * 100:.2f}% is below target {self.target_density * 100:.0f}%",
                    details={"density": density, "target": self.target_density},
                )
            )
            recs.append(
                CriticRecommendation(
                    title="Increase spawn density",
                    description="Add more monster spawns in hunt areas to reach the target density.",
                    category=self.CATEGORY,
                    priority=RecommendationPriority.MEDIUM,
                )
            )

        for i, cluster in enumerate(clusters[:3]):
            issues.append(
                CriticIssue(
                    issue_type=IssueType.SPAWN_CLUSTER,
                    severity=IssueSeverity.WARNING,
                    category=self.CATEGORY,
                    location=f"({cluster[0][0]},{cluster[0][1]})",
                    message=f"Spawn cluster of {len(cluster)} creatures at {cluster[0]}",
                    details={"cluster_size": len(cluster)},
                )
            )
        if clusters:
            recs.append(
                CriticRecommendation(
                    title="Spread spawn clusters",
                    description="Some spawns are clustered very close together. Spread them out for better gameplay.",
                    category=self.CATEGORY,
                    priority=RecommendationPriority.LOW,
                )
            )

        return {
            "category": self.CATEGORY,
            "score": score,
            "issues": issues,
            "recommendations": recs,
            "metrics": {
                "total_spawns": total_spawns,
                "grounded_tiles": total_ground,
                "spawn_density": round(density, 4),
                "min_distance": min_d,
                "max_distance": max_d,
                "avg_distance": round(avg_d, 2),
                "cluster_count": len(clusters),
                "zone_coverage": round(zone_coverage, 4),
            },
        }
