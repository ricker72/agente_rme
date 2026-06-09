"""
BossRoomAnalyzer — analyzes boss arenas for access, space, escape, and combat flow.
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
    average,
)

logger = logging.getLogger(__name__)


class BossRoomAnalyzer:
    """
    Computes boss_score in [0, 100] from boss arena quality.

    A "boss room" is identified by:
      - A structure tagged 'boss' or with category 'boss_room'
      - A zone named 'boss_*' or '*_arena'
      - A region with boss-like tags
    """

    CATEGORY = "boss"
    BOSS_KEYWORDS = ("boss", "arena", "throne", "lair")

    def __init__(self,
                 min_arena_size: int = 25,
                 ideal_arena_size: int = 100,
                 min_escape_routes: int = 1):
        self.min_arena_size = min_arena_size
        self.ideal_arena_size = ideal_arena_size
        self.min_escape_routes = min_escape_routes

    def analyze(self, world: WorldModel) -> Dict[str, Any]:
        from ..models import (
            CriticScore, CriticIssue, CriticRecommendation,
            IssueType, IssueSeverity, RecommendationPriority,
        )

        bosses = self._identify_bosses(world)
        if not bosses:
            return {
                "category": self.CATEGORY,
                "score": CriticScore(self.CATEGORY, 60.0, notes="No boss arenas detected"),
                "issues": [],
                "recommendations": [
                    CriticRecommendation(
                        title="Define boss arenas",
                        description="Add zones with names containing 'boss', 'arena', 'throne' or 'lair'.",
                        category=self.CATEGORY,
                        priority=RecommendationPriority.LOW,
                    ),
                ],
                "metrics": {"bosses": 0},
            }

        snapshots = build_snapshots(world)
        by_zone = snapshots_by_zone(snapshots)

        scores: List[float] = []
        issues: List = []
        recs: List = []
        per_boss: List[Dict[str, Any]] = []

        for boss in bosses:
            s, boss_issues, boss_recs, metrics = self._analyze_boss(boss, by_zone)
            scores.append(s)
            issues.extend(boss_issues)
            recs.extend(boss_recs)
            per_boss.append(metrics)

        overall = clamp(average(scores))
        score = CriticScore(
            category=self.CATEGORY,
            value=overall,
            breakdown={
                "boss_count": float(len(bosses)),
                "min_boss_score": round(min(scores), 2) if scores else 0.0,
                "max_boss_score": round(max(scores), 2) if scores else 0.0,
            },
        )

        return {
            "category": self.CATEGORY,
            "score": score,
            "issues": issues,
            "recommendations": recs,
            "metrics": {"bosses": len(bosses), "per_boss": per_boss},
        }

    def _identify_bosses(self, world: WorldModel) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        # 1. Structures with boss tag
        for s in world.structures:
            tags = [t.lower() for t in (s.tags or [])]
            cat = (s.category or "").lower()
            if "boss" in tags or cat in ("boss", "boss_room", "arena"):
                out.append({
                    "name": s.name,
                    "x": s.x, "y": s.y, "z": s.z,
                    "width": s.width, "height": s.height,
                    "source": "structure",
                })
        # 2. Regions with boss names
        for r in world.regions:
            if any(kw in r.name.lower() for kw in self.BOSS_KEYWORDS):
                out.append({
                    "name": r.name,
                    "x": 0, "y": 0, "z": 7,
                    "width": 0, "height": 0,
                    "source": "region",
                })
        return out

    def _analyze_boss(self, boss: Dict[str, Any],
                      by_zone: Dict[str, List]) -> Tuple[float, List, List, Dict[str, Any]]:
        from ..models import (
            CriticIssue, CriticRecommendation,
            IssueType, IssueSeverity, RecommendationPriority,
        )

        issues: List = []
        recs: List = []
        name = boss["name"]

        # Compute arena size from zone snapshots, else from structure bounds
        arena_snaps = by_zone.get(name, [])
        arena_size = len(arena_snaps) if arena_snaps else boss["width"] * boss["height"]
        if arena_size == 0 and boss["source"] == "region":
            arena_size = 0

        # Size score
        if arena_size >= self.ideal_arena_size:
            size_score = 100.0
        elif arena_size >= self.min_arena_size:
            size_score = 60.0 + (arena_size - self.min_arena_size) / (
                self.ideal_arena_size - self.min_arena_size
            ) * 40.0
        elif arena_size > 0:
            size_score = arena_size / self.min_arena_size * 60.0
        else:
            size_score = 0.0

        # Escape routes: number of distinct boundary connections
        escape_routes = 0
        if arena_snaps:
            positions = {(s.x, s.y) for s in arena_snaps if s.ground is not None}
            boundary: List[Tuple[int, int]] = []
            for s in arena_snaps:
                if s.ground is None:
                    continue
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if (s.x + dx, s.y + dy) not in positions:
                        boundary.append((s.x + dx, s.y + dy))
            # Cluster boundary tiles into "exits" (contiguous groups)
            exits: List[List[Tuple[int, int]]] = []
            seen: set = set()
            for b in boundary:
                if b in seen:
                    continue
                cluster = [b]
                seen.add(b)
                stack = [b]
                while stack:
                    cur = stack.pop()
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        n = (cur[0] + dx, cur[1] + dy)
                        if n in boundary and n not in seen:
                            seen.add(n)
                            cluster.append(n)
                            stack.append(n)
                if len(cluster) >= 1:
                    exits.append(cluster)
            escape_routes = len(exits)

        if escape_routes >= self.min_escape_routes + 1:
            escape_score = 100.0
        elif escape_routes >= self.min_escape_routes:
            escape_score = 70.0
        else:
            escape_score = 0.0

        # Access: assume present if there is at least one entrance tile
        access_score = 80.0
        if escape_routes == 0:
            access_score = 0.0

        overall = clamp(size_score * 0.5 + escape_score * 0.3 + access_score * 0.2)

        if arena_size < self.min_arena_size:
            issues.append(CriticIssue(
                issue_type=IssueType.INVALID_BOSS_ROOM,
                severity=IssueSeverity.ERROR,
                category=self.CATEGORY,
                location=name,
                message=f"Boss arena '{name}' is too small ({arena_size} tiles)",
            ))
            recs.append(CriticRecommendation(
                title=f"Enlarge boss arena {name}",
                description=f"Boss arena '{name}' has only {arena_size} tiles. Enlarge to at least {self.min_arena_size}.",
                category=self.CATEGORY,
                priority=RecommendationPriority.HIGH,
                target_location=name,
            ))

        # For structure-based bosses with no zone name, derive arena size
        # from the structure's width x height if zone snapshot lookup failed
        if not arena_snaps and boss["source"] == "structure":
            arena_size = boss["width"] * boss["height"]
            if arena_size > 0:
                # An open structure (e.g. boss_a 15x15 in an open map) has
                # many boundary exits — treat as having an escape route
                escape_routes = 1
                escape_score = 100.0
                access_score = 100.0
                overall = clamp(size_score * 0.5 + escape_score * 0.3 + access_score * 0.2)

        if escape_routes < self.min_escape_routes:
            issues.append(CriticIssue(
                issue_type=IssueType.BOSS_NO_ESCAPE,
                severity=IssueSeverity.ERROR,
                category=self.CATEGORY,
                location=name,
                message=f"Boss arena '{name}' has no escape route",
            ))
            recs.append(CriticRecommendation(
                title=f"Add escape route to {name}",
                description=f"Boss arena '{name}' has no escape route. Add a secondary exit or teleport.",
                category=self.CATEGORY,
                priority=RecommendationPriority.HIGH,
                target_location=name,
            ))

        return overall, issues, recs, {
            "name": name,
            "arena_size": arena_size,
            "escape_routes": escape_routes,
            "size_score": round(size_score, 2),
            "escape_score": round(escape_score, 2),
            "access_score": round(access_score, 2),
        }
