"""
VisualAnalyzer — analyzes the visual quality of the map: tile quantity,
content density, decoration, consistency.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel

from .base_analyzer import (
    build_snapshots,
    snapshots_by_zone,
    safe_ratio,
    clamp,
    average,
)

logger = logging.getLogger(__name__)


class VisualAnalyzer:
    """
    Computes visual_score in [0, 100] from:
      - total tile count
      - useful content ratio
      - visual density
      - decoration
      - consistency (uniformity of ground IDs)
    """

    CATEGORY = "visual"

    def __init__(self,
                 min_tiles: int = 50,
                 ideal_tiles: int = 5000,
                 ideal_ground_variety: int = 5):
        self.min_tiles = min_tiles
        self.ideal_tiles = ideal_tiles
        self.ideal_ground_variety = ideal_ground_variety

    def analyze(self, world: WorldModel,
                preview_path: Optional[str] = None) -> Dict[str, Any]:
        from ..models import (
            CriticScore, CriticIssue, CriticRecommendation,
            IssueType, IssueSeverity, RecommendationPriority,
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

        # 1. Quantity (saturating curve)
        if total >= self.ideal_tiles:
            quantity_score = 100.0
        elif total >= self.min_tiles:
            quantity_score = (total - self.min_tiles) / (self.ideal_tiles - self.min_tiles) * 100.0
        else:
            quantity_score = total / max(self.min_tiles, 1) * 60.0

        # 2. Useful content: tiles with ground + items OR spawn
        grounded = [s for s in snapshots if s.ground is not None]
        useful = [s for s in snapshots if s.ground is not None and (s.item_count > 0 or s.has_spawn)]
        content_ratio = safe_ratio(len(useful), len(grounded))

        # 3. Visual density: items per tile (saturating)
        item_counts = [s.item_count for s in snapshots]
        avg_items = average(item_counts)
        # Optimal 1.0-3.0 items per tile
        if 1.0 <= avg_items <= 3.0:
            density_score = 100.0
        elif avg_items < 1.0:
            density_score = max(0.0, avg_items * 100.0)
        else:
            density_score = max(0.0, 100.0 - (avg_items - 3.0) * 20.0)

        # 4. Decoration: distinct item types per zone
        by_zone = snapshots_by_zone(snapshots)
        zone_varieties: List[int] = []
        for _name, items in by_zone.items():
            cnt = Counter()
            for s in items:
                for iid in s.item_ids:
                    cnt[iid] += 1
            zone_varieties.append(len(cnt))
        avg_variety = average(zone_varieties) if zone_varieties else 0.0
        variety_score = min(100.0, avg_variety / self.ideal_ground_variety * 100.0)

        # 5. Consistency: ground ID diversity (lower is more consistent)
        grounds = Counter(s.ground for s in grounded if s.ground is not None)
        ground_variety = len(grounds)
        # Map has many ground types = inconsistent. A few = consistent.
        if ground_variety == 0:
            consistency_score = 0.0
        elif ground_variety <= 8:
            consistency_score = 100.0
        else:
            consistency_score = max(0.0, 100.0 - (ground_variety - 8) * 2.0)

        # Composite
        score_value = (
            quantity_score * 0.20
            + content_ratio * 100.0 * 0.25
            + density_score * 0.20
            + variety_score * 0.15
            + consistency_score * 0.20
        )
        score_value = clamp(score_value)

        score = CriticScore(
            category=self.CATEGORY,
            value=score_value,
            breakdown={
                "quantity": round(quantity_score, 2),
                "content_ratio": round(content_ratio * 100.0, 2),
                "density": round(density_score, 2),
                "variety": round(variety_score, 2),
                "consistency": round(consistency_score, 2),
                "total_tiles": float(total),
            },
        )

        issues: List = []
        recs: List = []

        if total < self.min_tiles:
            issues.append(CriticIssue(
                issue_type=IssueType.EMPTY_REGION,
                severity=IssueSeverity.WARNING,
                category=self.CATEGORY,
                message=f"Map has only {total} tiles (minimum {self.min_tiles})",
            ))
            recs.append(CriticRecommendation(
                title="Add more tiles",
                description=f"The map has only {total} tiles. Consider expanding or generating more content.",
                category=self.CATEGORY,
                priority=RecommendationPriority.MEDIUM,
            ))

        if content_ratio < 0.30 and total > 10:
            issues.append(CriticIssue(
                issue_type=IssueType.UNDERDECORATED_AREA,
                severity=IssueSeverity.WARNING,
                category=self.CATEGORY,
                message=f"Only {content_ratio*100:.0f}% of ground tiles have content",
            ))
            recs.append(CriticRecommendation(
                title="Add visual content",
                description="Large portions of the map are visually empty. Add items, spawns or decoration.",
                category=self.CATEGORY,
                priority=RecommendationPriority.MEDIUM,
            ))

        return {
            "category": self.CATEGORY,
            "score": score,
            "issues": issues,
            "recommendations": recs,
            "metrics": {
                "total_tiles": total,
                "grounded_tiles": len(grounded),
                "useful_tiles": len(useful),
                "content_ratio": round(content_ratio, 4),
                "avg_items_per_tile": round(avg_items, 2),
                "ground_variety": ground_variety,
                "preview_path": preview_path or "",
            },
        }
