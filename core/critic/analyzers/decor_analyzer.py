"""
DecorAnalyzer — analyzes decorative content: variety, repetition, overuse, void zones.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any, Dict, List

from core.world.world_model import WorldModel

from .base_analyzer import (
    build_snapshots,
    snapshots_by_zone,
    safe_ratio,
    clamp,
)

logger = logging.getLogger(__name__)


class DecorAnalyzer:
    """
    Computes decor_score in [0, 100] from decoration variety and distribution.
    """

    CATEGORY = "decor"

    def __init__(self, variety_target: int = 8, max_repetition_ratio: float = 0.40):
        self.variety_target = variety_target
        self.max_repetition_ratio = max_repetition_ratio

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
                "metrics": {"variety": 0},
            }

        # All item IDs across the world
        all_items: List[int] = []
        for s in snapshots:
            all_items.extend(s.item_ids)
        counter = Counter(all_items)
        variety = len(counter)
        total_items = sum(counter.values())

        # Repetition: most common item's share
        if counter:
            most_common_id, most_common_count = counter.most_common(1)[0]
            repetition_ratio = safe_ratio(most_common_count, max(total_items, 1))
        else:
            most_common_id = None
            most_common_count = 0
            repetition_ratio = 0.0

        # Variety score: saturates at variety_target
        variety_score = min(100.0, variety / max(self.variety_target, 1) * 100.0)

        # Repetition score: 100 if ratio <= 0.20, linearly down
        if repetition_ratio <= 0.20:
            repetition_score = 100.0
        else:
            repetition_score = max(0.0, 100.0 - (repetition_ratio - 0.20) * 200.0)

        # Decoration coverage: tiles with any decoration
        decorated = [s for s in snapshots if s.item_count > 0]
        coverage = safe_ratio(len(decorated), total)

        # Overuse: tiles with very high item count
        overused = [s for s in snapshots if s.item_count > 8]
        overuse_ratio = safe_ratio(len(overused), total)

        # Empty zones: zones with very few items
        by_zone = snapshots_by_zone(snapshots)
        empty_zones: List[str] = []
        for zname, items in by_zone.items():
            z_coverage = safe_ratio(
                sum(1 for s in items if s.item_count > 0),
                len(items),
            )
            if z_coverage < 0.05 and len(items) > 10:
                empty_zones.append(zname)

        overall = clamp(
            variety_score * 0.30
            + repetition_score * 0.25
            + coverage * 100.0 * 0.30
            + max(0.0, 100.0 - overuse_ratio * 500.0) * 0.15
        )

        score = CriticScore(
            category=self.CATEGORY,
            value=overall,
            breakdown={
                "variety_score": round(variety_score, 2),
                "repetition_score": round(repetition_score, 2),
                "coverage": round(coverage * 100.0, 2),
                "overuse_ratio": round(overuse_ratio * 100.0, 2),
            },
        )

        issues: List = []
        recs: List = []

        if variety < self.variety_target // 2:
            issues.append(
                CriticIssue(
                    issue_type=IssueType.UNDERDECORATED_AREA,
                    severity=IssueSeverity.WARNING,
                    category=self.CATEGORY,
                    message=f"Only {variety} unique decoration types — map looks repetitive",
                )
            )
            recs.append(
                CriticRecommendation(
                    title="Increase decoration variety",
                    description=f"Map uses only {variety} unique items. Add more decoration variety.",
                    category=self.CATEGORY,
                    priority=RecommendationPriority.MEDIUM,
                )
            )

        if repetition_ratio > self.max_repetition_ratio:
            issues.append(
                CriticIssue(
                    issue_type=IssueType.OVERDECORATED_AREA,
                    severity=IssueSeverity.WARNING,
                    category=self.CATEGORY,
                    message=f"Item {most_common_id} represents {repetition_ratio * 100:.0f}% of decorations",
                    details={"item_id": most_common_id, "count": most_common_count},
                )
            )

        for zname in empty_zones[:3]:
            issues.append(
                CriticIssue(
                    issue_type=IssueType.UNDERDECORATED_AREA,
                    severity=IssueSeverity.WARNING,
                    category=self.CATEGORY,
                    location=zname,
                    message=f"Zone '{zname}' is almost empty of decoration",
                )
            )
            recs.append(
                CriticRecommendation(
                    title=f"Add decoration to {zname}",
                    description=f"Zone '{zname}' has very few decorations. Add furniture, props, or natural elements.",
                    category=self.CATEGORY,
                    priority=RecommendationPriority.MEDIUM,
                    target_location=zname,
                )
            )

        return {
            "category": self.CATEGORY,
            "score": score,
            "issues": issues,
            "recommendations": recs,
            "metrics": {
                "variety": variety,
                "total_items": total_items,
                "repetition_ratio": round(repetition_ratio, 4),
                "coverage": round(coverage, 4),
                "overuse_ratio": round(overuse_ratio, 4),
                "empty_zones": empty_zones,
                "most_common_item": most_common_id,
            },
        }
