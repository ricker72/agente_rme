"""
RegionAnalyzer — analyzes named regions: emptiness, level ranges, coverage.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from core.world.world_model import WorldModel
from core.world.region import Region

from .base_analyzer import (
    build_snapshots,
    snapshots_by_zone,
    safe_ratio,
    clamp,
    average,
)

logger = logging.getLogger(__name__)


class RegionAnalyzer:
    """
    Computes a 'region' overview used to enrich the overall map critic result.

    This analyzer is a meta-analyzer — it does not produce its own
    primary score but contributes metrics used by the engine.
    """

    CATEGORY = "region"

    def __init__(self, empty_threshold: int = 5):
        self.empty_threshold = empty_threshold

    def analyze(self, world: WorldModel) -> Dict[str, Any]:
        from ..models import (
            CriticScore, CriticIssue, CriticRecommendation,
            IssueType, IssueSeverity, RecommendationPriority,
        )

        regions = list(world.regions)
        snapshots = build_snapshots(world)
        by_zone = snapshots_by_zone(snapshots)

        empty_regions: List[str] = []
        issues: List = []
        recs: List = []

        for region in regions:
            snaps = by_zone.get(region.name, [])
            if len(snaps) < self.empty_threshold:
                empty_regions.append(region.name)
                issues.append(CriticIssue(
                    issue_type=IssueType.EMPTY_REGION,
                    severity=IssueSeverity.WARNING,
                    category=self.CATEGORY,
                    location=region.name,
                    message=f"Region '{region.name}' is empty or near-empty ({len(snaps)} tiles)",
                ))

        if empty_regions:
            recs.append(CriticRecommendation(
                title="Populate empty regions",
                description=f"Empty regions: {', '.join(empty_regions)}. Add tiles, decoration or remove them.",
                category=self.CATEGORY,
                priority=RecommendationPriority.MEDIUM,
            ))

        # Level-range consistency
        level_issues = 0
        for region in regions:
            if region.min_level > region.max_level:
                level_issues += 1
                issues.append(CriticIssue(
                    issue_type=IssueType.POOR_NAVIGATION,
                    severity=IssueSeverity.WARNING,
                    category=self.CATEGORY,
                    location=region.name,
                    message=f"Region '{region.name}' has invalid level range ({region.min_level}-{region.max_level})",
                ))

        # Compute the average region "size" as a quality proxy
        region_sizes = [len(by_zone.get(r.name, [])) for r in regions]
        avg_size = average(region_sizes) if region_sizes else 0.0

        coverage = safe_ratio(
            sum(1 for r in regions if len(by_zone.get(r.name, [])) >= self.empty_threshold),
            len(regions),
        )

        # Score
        emptiness_penalty = min(50.0, len(empty_regions) * 10.0)
        level_penalty = min(20.0, level_issues * 10.0)
        overall = clamp(100.0 - emptiness_penalty - level_penalty)
        overall = overall * 0.7 + coverage * 100.0 * 0.3

        score = CriticScore(
            category=self.CATEGORY,
            value=overall,
            breakdown={
                "region_count": float(len(regions)),
                "empty_regions": float(len(empty_regions)),
                "level_issues": float(level_issues),
                "avg_size": round(avg_size, 2),
                "coverage": round(coverage * 100.0, 2),
            },
        )

        return {
            "category": self.CATEGORY,
            "score": score,
            "issues": issues,
            "recommendations": recs,
            "metrics": {
                "region_count": len(regions),
                "empty_regions": empty_regions,
                "level_issues": level_issues,
                "avg_size": round(avg_size, 2),
                "coverage": round(coverage, 4),
            },
        }
