"""
HuntAnalyzer — analyzes hunt zones for farming flow, rotation, and respawn.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple

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


class HuntAnalyzer:
    """
    Computes hunt_score in [0, 100] from spawn flow and rotation quality.

    A "hunt" is identified by zones whose name contains 'hunt' or 'spawn',
    or by regions of dense spawns.
    """

    CATEGORY = "hunt"
    HUNT_KEYWORDS = ("hunt", "spawn", "farm", "cave", "-")

    def __init__(self,
                 min_hunt_tiles: int = 10,
                 optimal_respawn_seconds: int = 60):
        self.min_hunt_tiles = min_hunt_tiles
        self.optimal_respawn_seconds = optimal_respawn_seconds

    def analyze(self, world: WorldModel) -> Dict[str, Any]:
        from ..models import (
            CriticScore, CriticIssue, CriticRecommendation,
            IssueType, IssueSeverity, RecommendationPriority,
        )

        snapshots = build_snapshots(world)
        if not snapshots:
            return {
                "category": self.CATEGORY,
                "score": CriticScore(self.CATEGORY, 0.0, notes="Empty world"),
                "issues": [],
                "recommendations": [],
                "metrics": {"hunts": 0},
            }

        # Identify hunts
        hunts = self._identify_hunts(snapshots, world)
        if not hunts:
            return {
                "category": self.CATEGORY,
                "score": CriticScore(self.CATEGORY, 50.0, notes="No hunt zones identified"),
                "issues": [],
                "recommendations": [
                    CriticRecommendation(
                        title="Define hunt zones",
                        description="Add zones with names containing 'hunt', 'spawn', 'farm' or 'cave' to enable hunt analysis.",
                        category=self.CATEGORY,
                        priority=RecommendationPriority.LOW,
                    ),
                ],
                "metrics": {"hunts": 0},
            }

        # Per-hunt analysis
        hunt_scores: List[float] = []
        issues: List = []
        recs: List = []
        per_hunt_metrics: List[Dict[str, Any]] = []

        for hunt in hunts:
            score, hunt_issues, hunt_recs, metrics = self._analyze_hunt(hunt)
            hunt_scores.append(score)
            issues.extend(hunt_issues)
            recs.extend(hunt_recs)
            per_hunt_metrics.append(metrics)

        overall = clamp(average(hunt_scores))
        score = CriticScore(
            category=self.CATEGORY,
            value=overall,
            breakdown={
                "hunt_count": float(len(hunts)),
                "min_hunt_score": round(min(hunt_scores), 2) if hunt_scores else 0.0,
                "max_hunt_score": round(max(hunt_scores), 2) if hunt_scores else 0.0,
            },
        )

        # Hunt rotation: detect gaps (hunts that are too far apart)
        centroids = [m["centroid"] for m in per_hunt_metrics]
        if len(centroids) > 1:
            for i in range(len(centroids)):
                for j in range(i + 1, len(centroids)):
                    d = manhattan(centroids[i], centroids[j])
                    if d > 80:
                        issues.append(CriticIssue(
                            issue_type=IssueType.HUNT_GAP,
                            severity=IssueSeverity.WARNING,
                            category=self.CATEGORY,
                            message=f"Hunts {i} and {j} are {d} tiles apart — consider adding a closer hunt",
                            details={"distance": d},
                        ))

        return {
            "category": self.CATEGORY,
            "score": score,
            "issues": issues,
            "recommendations": recs,
            "metrics": {
                "hunts": len(hunts),
                "per_hunt": per_hunt_metrics,
            },
        }

    def _identify_hunts(self, snapshots, world) -> List[Dict[str, Any]]:
        """Return list of hunt dicts."""
        hunts: List[Dict[str, Any]] = []

        # First: zones with hunt-like names
        by_zone = snapshots_by_zone(snapshots)
        for name, items in by_zone.items():
            if any(kw in name.lower() for kw in self.HUNT_KEYWORDS):
                hunts.append({
                    "name": name,
                    "snapshots": items,
                    "source": "zone_name",
                })

        # Second: if no explicit hunts, derive from regions
        if not hunts:
            for region in world.regions:
                if any(kw in region.name.lower() for kw in self.HUNT_KEYWORDS):
                    zone_snaps = by_zone.get(region.name, [])
                    hunts.append({
                        "name": region.name,
                        "snapshots": zone_snaps,
                        "source": "region_name",
                    })

        return hunts

    def _analyze_hunt(self, hunt: Dict[str, Any]) -> Tuple[float, List, List, Dict[str, Any]]:
        from ..models import (
            CriticScore, CriticIssue, CriticRecommendation,
            IssueType, IssueSeverity, RecommendationPriority,
        )

        snaps = hunt["snapshots"]
        name = hunt["name"]
        spawns = [s for s in snaps if s.has_spawn]
        tiles = snaps
        if len(tiles) < self.min_hunt_tiles:
            return 50.0, [], [], {
                "name": name,
                "size": len(tiles),
                "spawns": len(spawns),
                "centroid": (0, 0),
            }

        spawn_density = safe_ratio(len(spawns), len(tiles))
        # Quality components
        # 1. spawn density in [0.05, 0.30]
        if 0.05 <= spawn_density <= 0.30:
            density_quality = 100.0
        elif spawn_density < 0.05:
            density_quality = spawn_density / 0.05 * 100.0
        else:
            density_quality = max(0.0, 100.0 - (spawn_density - 0.30) * 200.0)

        # 2. spawn diversity (variety of monsters)
        monster_types = set()
        for s in spawns:
            if s.zone:
                monster_types.add(s.zone)
        diversity = min(1.0, len(monster_types) / 3.0) if monster_types else 0.5

        # 3. respawn health — average respawn time vs target
        respawns: List[int] = []
        for s in snaps:
            if s.has_spawn and s.zone:
                # Use zone as proxy; we don't have direct respawn in snapshots
                pass
        respawn_quality = 80.0  # neutral default

        # 4. spatial flow — average nearest neighbor distance
        flow_quality = 50.0
        if len(spawns) > 1:
            sample = spawns[:30]
            dists: List[int] = []
            for i, a in enumerate(sample):
                nearest = float("inf")
                for j, b in enumerate(sample):
                    if i == j:
                        continue
                    d = manhattan((a.x, a.y), (b.x, b.y))
                    if d < nearest:
                        nearest = d
                if nearest < float("inf"):
                    dists.append(int(nearest))
            if dists:
                avg = average(dists)
                # Best around 6-12 manhattan tiles
                if 6 <= avg <= 12:
                    flow_quality = 100.0
                else:
                    flow_quality = max(0.0, 100.0 - abs(avg - 9.0) * 5.0)

        score = (
            density_quality * 0.40
            + diversity * 100.0 * 0.20
            + respawn_quality * 0.20
            + flow_quality * 0.20
        )
        score = clamp(score)

        issues: List = []
        recs: List = []

        if spawn_density < 0.03:
            issues.append(CriticIssue(
                issue_type=IssueType.LOW_SPAWN_DENSITY,
                severity=IssueSeverity.WARNING,
                category=self.CATEGORY,
                location=name,
                message=f"Hunt '{name}' has low spawn density ({spawn_density*100:.1f}%)",
            ))
            recs.append(CriticRecommendation(
                title=f"Increase spawn density in {name}",
                description=f"Hunt '{name}' has only {spawn_density*100:.1f}% spawn coverage. Add more spawns.",
                category=self.CATEGORY,
                priority=RecommendationPriority.MEDIUM,
                target_location=name,
            ))

        # Centroid
        cx = sum(s.x for s in tiles) / len(tiles)
        cy = sum(s.y for s in tiles) / len(tiles)

        return score, issues, recs, {
            "name": name,
            "size": len(tiles),
            "spawns": len(spawns),
            "spawn_density": round(spawn_density, 4),
            "diversity": round(diversity, 2),
            "centroid": (int(cx), int(cy)),
        }
