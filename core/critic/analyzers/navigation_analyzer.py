"""
NavigationAnalyzer — analyzes path connectivity, dead-ends, and bottlenecks.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from typing import Any, Dict, List, Set, Tuple

from core.world.world_model import WorldModel

from .base_analyzer import (
    build_snapshots,
    find_regions,
    snapshots_by_z,
    safe_ratio,
    clamp,
)

logger = logging.getLogger(__name__)


class NavigationAnalyzer:
    """
    Computes navigation_score in [0, 100] from connectivity and route health.

    Uses only structural analysis (no A* / Dijkstra) — the heavy
    path-planning work lives in PathfindingAnalyzer.
    """

    CATEGORY = "navigation"

    def __init__(self,
                 min_region_size: int = 5,
                 dead_end_threshold: int = 1):
        self.min_region_size = min_region_size
        self.dead_end_threshold = dead_end_threshold

    def analyze(self, world: WorldModel) -> Dict[str, Any]:
        from ..models import (
            CriticScore, CriticIssue, CriticRecommendation,
            IssueType, IssueSeverity, RecommendationPriority,
        )

        snapshots = build_snapshots(world)
        by_z = snapshots_by_z(snapshots)
        if not by_z:
            return {
                "category": self.CATEGORY,
                "score": CriticScore(self.CATEGORY, 0.0, notes="Empty world"),
                "issues": [],
                "recommendations": [],
                "metrics": {"regions": 0, "dead_ends": 0},
            }

        all_regions = []
        for z in by_z:
            all_regions.extend(find_regions(snapshots, z, connectivity=4))
        small_regions = [r for r in all_regions if r.size < self.min_region_size]
        major_regions = [r for r in all_regions if r.size >= self.min_region_size]

        # Dead-end detection: tiles with only 1 neighbor (within 4-connectivity)
        dead_ends: List[Tuple[int, int, int]] = []
        for z, snaps in by_z.items():
            positions = {(s.x, s.y) for s in snaps if s.ground is not None}
            for s in snaps:
                if s.ground is None:
                    continue
                n = 0
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if (s.x + dx, s.y + dy) in positions:
                        n += 1
                if n <= self.dead_end_threshold:
                    dead_ends.append((s.x, s.y, s.z))

        # Bottleneck detection: tiles with exactly 2 neighbors
        bottlenecks: List[Tuple[int, int, int]] = []
        for z, snaps in by_z.items():
            positions = {(s.x, s.y) for s in snaps if s.ground is not None}
            for s in snaps:
                if s.ground is None:
                    continue
                n = 0
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if (s.x + dx, s.y + dy) in positions:
                        n += 1
                if n == 2 and len(positions) > 20:
                    bottlenecks.append((s.x, s.y, s.z))

        total_grounded = sum(1 for s in snapshots if s.ground is not None)
        dead_end_ratio = safe_ratio(len(dead_ends), max(total_grounded, 1))
        bottleneck_ratio = safe_ratio(len(bottlenecks), max(total_grounded, 1))
        region_count = len(major_regions)
        isolated_count = len(small_regions)

        # Score
        # 30 connectivity (count of major regions), 30 dead-end ratio,
        # 20 bottleneck ratio, 20 absence of isolated regions
        connectivity_score = 100.0
        if region_count == 0 and total_grounded > 0:
            connectivity_score = 0.0
        elif region_count > 1:
            connectivity_score = max(0.0, 100.0 - (region_count - 1) * 10.0)

        dead_end_score = 100.0
        if dead_end_ratio > 0.05:
            dead_end_score = max(0.0, 100.0 - (dead_end_ratio - 0.05) * 500.0)

        bottleneck_score = 100.0
        if bottleneck_ratio > 0.10:
            bottleneck_score = max(0.0, 100.0 - (bottleneck_ratio - 0.10) * 300.0)

        isolation_score = 100.0
        if isolated_count > 0:
            isolation_score = max(0.0, 100.0 - isolated_count * 5.0)

        score_value = (
            connectivity_score * 0.30
            + dead_end_score * 0.30
            + bottleneck_score * 0.20
            + isolation_score * 0.20
        )
        score_value = clamp(score_value)

        score = CriticScore(
            category=self.CATEGORY,
            value=score_value,
            breakdown={
                "connectivity": round(connectivity_score, 2),
                "dead_end_health": round(dead_end_score, 2),
                "bottleneck_health": round(bottleneck_score, 2),
                "isolation_health": round(isolation_score, 2),
                "major_regions": region_count,
            },
        )

        issues: List = []
        recs: List = []

        if region_count > 1 and total_grounded > 20:
            issues.append(CriticIssue(
                issue_type=IssueType.ISOLATED_REGION,
                severity=IssueSeverity.ERROR,
                category=self.CATEGORY,
                message=f"Map has {region_count} disconnected regions",
                details={"region_count": region_count},
            ))
            recs.append(CriticRecommendation(
                title="Connect disconnected regions",
                description=f"There are {region_count} disconnected map regions. Add paths, doors, teleporters or stairs to connect them.",
                category=self.CATEGORY,
                priority=RecommendationPriority.HIGH,
            ))

        for de in dead_ends[:5]:
            issues.append(CriticIssue(
                issue_type=IssueType.DEAD_END,
                severity=IssueSeverity.INFO,
                category=self.CATEGORY,
                location=f"({de[0]},{de[1]},{de[2]})",
                message="Dead-end path detected",
            ))
        if dead_end_ratio > 0.10:
            recs.append(CriticRecommendation(
                title="Reduce dead ends in dungeon",
                description=f"Dead ends represent {dead_end_ratio*100:.1f}% of tiles. Consider adding loops or secondary paths.",
                category=self.CATEGORY,
                priority=RecommendationPriority.LOW,
            ))

        for bn in bottlenecks[:3]:
            issues.append(CriticIssue(
                issue_type=IssueType.BOTTLENECK,
                severity=IssueSeverity.WARNING,
                category=self.CATEGORY,
                location=f"({bn[0]},{bn[1]},{bn[2]})",
                message="Bottleneck: only 2 connections",
            ))

        if isolated_count > 0:
            issues.append(CriticIssue(
                issue_type=IssueType.POOR_NAVIGATION,
                severity=IssueSeverity.WARNING,
                category=self.CATEGORY,
                message=f"{isolated_count} small isolated regions detected",
            ))

        return {
            "category": self.CATEGORY,
            "score": score,
            "issues": issues,
            "recommendations": recs,
            "metrics": {
                "regions": region_count,
                "small_regions": isolated_count,
                "dead_ends": len(dead_ends),
                "bottlenecks": len(bottlenecks),
                "dead_end_ratio": round(dead_end_ratio, 4),
                "bottleneck_ratio": round(bottleneck_ratio, 4),
                "total_grounded": total_grounded,
            },
        }
