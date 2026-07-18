"""
DensityAnalyzer — analyzes tile density and content concentration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from core.world.world_model import WorldModel

from .base_analyzer import (
    build_snapshots,
    snapshots_by_zone,
    safe_ratio,
    clamp,
)

logger = logging.getLogger(__name__)


class DensityAnalyzer:
    """
    Computes density_score in [0, 100] from tile content distribution.

    Metrics:
      - empty tile ratio
      - tiles with content
      - items per tile
      - concentration (how clustered content is)
    """

    CATEGORY = "density"

    def __init__(self, min_items: int = 1, optimal_items: int = 3):
        self.min_items = min_items
        self.optimal_items = optimal_items

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
        total = len(snapshots)
        if total == 0:
            return {
                "category": self.CATEGORY,
                "score": CriticScore(self.CATEGORY, 0.0, notes="Empty world"),
                "issues": [],
                "recommendations": [],
                "metrics": {"total_tiles": 0},
            }

        # Build bounding box of ground tiles
        grounded = [s for s in snapshots if s.ground is not None]
        bbox = self._bbox(grounded)
        bbox_area = 1
        if bbox is not None:
            min_x, min_y, max_x, max_y = bbox
            bbox_area = max(1, (max_x - min_x + 1) * (max_y - min_y + 1))

        # Compute basic metrics
        tiles_with_items = [s for s in snapshots if s.item_count >= self.min_items]
        tiles_with_spawns = [s for s in snapshots if s.has_spawn]
        item_counts = [s.item_count for s in snapshots]
        avg_items = sum(item_counts) / total
        max_items = max(item_counts) if item_counts else 0

        # Concentration: standard deviation / mean of item count
        if avg_items > 0:
            variance = sum((c - avg_items) ** 2 for c in item_counts) / total
            std = variance**0.5
            cv = std / avg_items  # coefficient of variation
        else:
            cv = 0.0

        # Per-zone density
        by_zone = snapshots_by_zone(snapshots)
        zone_density: Dict[str, float] = {}
        for zone_name, items in by_zone.items():
            zone_density[zone_name] = safe_ratio(
                sum(1 for s in items if s.item_count >= self.min_items),
                len(items),
            )

        # Score
        # 40% from fill ratio (bbox coverage), 30% from content ratio, 20% from
        # spawn coverage, 10% from concentration.
        fill_ratio = safe_ratio(len(grounded), bbox_area)
        content_ratio = safe_ratio(len(tiles_with_items), total)
        spawn_ratio = safe_ratio(len(tiles_with_spawns), max(len(grounded), 1))
        # Concentration: 1.0 is good (uniform), 0.0 means highly clustered
        concentration = 1.0 - min(1.0, cv / 3.0)
        concentration = max(0.0, concentration)

        score_value = (
            fill_ratio * 100.0 * 0.40
            + content_ratio * 100.0 * 0.30
            + spawn_ratio * 100.0 * 0.20
            + concentration * 100.0 * 0.10
        )
        score_value = clamp(score_value)

        score = CriticScore(
            category=self.CATEGORY,
            value=score_value,
            breakdown={
                "fill_ratio": round(fill_ratio * 100.0, 2),
                "content_ratio": round(content_ratio * 100.0, 2),
                "spawn_ratio": round(spawn_ratio * 100.0, 2),
                "concentration": round(concentration * 100.0, 2),
                "avg_items_per_tile": round(avg_items, 2),
                "max_items_per_tile": max_items,
            },
        )

        issues: List = []
        recs: List = []

        if content_ratio < 0.2 and total > 10:
            issues.append(
                CriticIssue(
                    issue_type=IssueType.UNDERDECORATED_AREA,
                    severity=IssueSeverity.WARNING,
                    category=self.CATEGORY,
                    message=f"Only {content_ratio * 100:.0f}% of tiles have content",
                )
            )
            recs.append(
                CriticRecommendation(
                    title="Add decoration to empty areas",
                    description="Large portions of the map are empty. Add decoration, structures or spawns to improve density.",
                    category=self.CATEGORY,
                    priority=RecommendationPriority.MEDIUM,
                )
            )

        if avg_items > 10:
            issues.append(
                CriticIssue(
                    issue_type=IssueType.OVERDECORATED_AREA,
                    severity=IssueSeverity.WARNING,
                    category=self.CATEGORY,
                    message=f"Average items per tile is {avg_items:.1f} — possibly over-decorated",
                )
            )

        return {
            "category": self.CATEGORY,
            "score": score,
            "issues": issues,
            "recommendations": recs,
            "metrics": {
                "total_tiles": total,
                "grounded_tiles": len(grounded),
                "tiles_with_items": len(tiles_with_items),
                "tiles_with_spawns": len(tiles_with_spawns),
                "bbox_area": bbox_area,
                "zone_density": {k: round(v, 4) for k, v in zone_density.items()},
            },
        }

    @staticmethod
    def _bbox(snapshots: List) -> Tuple[int, int, int, int] | None:
        if not snapshots:
            return None
        xs = [s.x for s in snapshots]
        ys = [s.y for s in snapshots]
        return (min(xs), min(ys), max(xs), max(ys))
