"""
CriticEngine — orchestrates all analyzers and produces a CriticResult.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from core.world.world_model import WorldModel

from .models import (
    CriticScore, CriticIssue, CriticRecommendation,
    CriticResult, CriticCategoryResult, IssueType, IssueSeverity,
    RecommendationPriority,
)
from .analyzers import (
    VisualAnalyzer, NavigationAnalyzer, DensityAnalyzer, SpawnAnalyzer,
    HuntAnalyzer, BossRoomAnalyzer, CityAnalyzer, DecorAnalyzer,
    RegionAnalyzer, PathfindingAnalyzer,
)
from .score_calculator import ScoreCalculator

logger = logging.getLogger(__name__)


class CriticEngine:
    """
    Main entry point for running the visual map critic on a WorldModel.

    Usage:
        engine = CriticEngine()
        result = engine.analyze(world, map_name="issavi_roshamuul")
    """

    def __init__(self,
                 score_calculator: Optional[ScoreCalculator] = None,
                 analyzers: Optional[Dict[str, Any]] = None,
                 penalty_max: float = 30.0):
        self.score_calculator = score_calculator or ScoreCalculator()
        self.penalty_max = penalty_max
        self.analyzers: Dict[str, Any] = analyzers or self._default_analyzers()

    @staticmethod
    def _default_analyzers() -> Dict[str, Any]:
        return {
            "visual": VisualAnalyzer(),
            "navigation": NavigationAnalyzer(),
            "density": DensityAnalyzer(),
            "spawn": SpawnAnalyzer(),
            "hunt": HuntAnalyzer(),
            "boss": BossRoomAnalyzer(),
            "city": CityAnalyzer(),
            "decor": DecorAnalyzer(),
            "region": RegionAnalyzer(),
            "pathfinding": PathfindingAnalyzer(),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze(self, world: WorldModel, map_name: str = "",
                preview_path: Optional[str] = None,
                extra_context: Optional[Dict[str, Any]] = None) -> CriticResult:
        """
        Run all analyzers and return a CriticResult.
        """
        if not isinstance(world, WorldModel):
            # Try to coerce
            world = self._coerce_world(world)

        started = time.time()
        category_results: Dict[str, CriticCategoryResult] = {}
        all_issues: List[CriticIssue] = []
        all_recs: List[CriticRecommendation] = []
        per_category_metrics: Dict[str, Dict[str, Any]] = {}

        for category, analyzer in self.analyzers.items():
            try:
                if category == "visual" and preview_path:
                    res = analyzer.analyze(world, preview_path=preview_path)
                else:
                    res = analyzer.analyze(world)
                score: CriticScore = res["score"]
                issues: List[CriticIssue] = res.get("issues", [])
                recs: List[CriticRecommendation] = res.get("recommendations", [])
                metrics: Dict[str, Any] = res.get("metrics", {})
                category_results[category] = CriticCategoryResult(
                    category=category,
                    score=score,
                    issues=issues,
                    recommendations=recs,
                    metrics=metrics,
                )
                all_issues.extend(issues)
                all_recs.extend(recs)
                per_category_metrics[category] = metrics
            except Exception as exc:  # pragma: no cover — defensive
                logger.exception("Analyzer %s failed: %s", category, exc)
                category_results[category] = CriticCategoryResult(
                    category=category,
                    score=CriticScore(category, 0.0, notes=f"Analyzer failed: {exc}"),
                    issues=[
                        CriticIssue(
                            issue_type=IssueType.POOR_NAVIGATION,
                            severity=IssueSeverity.WARNING,
                            category=category,
                            message=f"Analyzer {category} failed: {exc}",
                        ),
                    ],
                    recommendations=[],
                    metrics={"error": str(exc)},
                )
                all_issues.append(category_results[category].issues[0])

        # Apply penalty from issues to each category score
        scores: Dict[str, CriticScore] = {}
        for cat, cres in category_results.items():
            penalty = sum(i.penalty for i in cres.issues)
            penalty = min(penalty, self.penalty_max)
            new_value = max(0.0, min(100.0, cres.score.value - penalty))
            scores[cat] = CriticScore(
                category=cat,
                value=new_value,
                breakdown=cres.score.breakdown,
                notes=cres.score.notes,
            )

        overall = self.score_calculator.combine_scores(scores)

        # Cross-cutting recommendations
        self._add_cross_cutting_recommendations(all_issues, all_recs, category_results)

        # Deduplicate recommendations by title
        all_recs = self._dedupe_recommendations(all_recs)

        elapsed = time.time() - started
        return CriticResult(
            map_name=map_name,
            scores=scores,
            issues=all_issues,
            recommendations=all_recs,
            overall_score=overall,
            metadata={
                "execution_time": round(elapsed, 4),
                "analyzers": list(self.analyzers.keys()),
                "category_metrics": per_category_metrics,
                "preview_path": preview_path or "",
                "extra_context": extra_context or {},
            },
        )

    def analyze_dict(self, data: Dict[str, Any], map_name: str = "",
                     preview_path: Optional[str] = None) -> CriticResult:
        """Analyze a world described as a dict (tiles list, structures, regions)."""
        world = self._dict_to_world(data)
        return self.analyze(world, map_name=map_name, preview_path=preview_path)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _coerce_world(self, data: Any) -> WorldModel:
        if isinstance(data, WorldModel):
            return data
        if isinstance(data, dict):
            return self._dict_to_world(data)
        raise TypeError(f"Cannot coerce {type(data).__name__} to WorldModel")

    @staticmethod
    def _dict_to_world(data: Dict[str, Any]) -> WorldModel:
        from core.world.world_model import WorldModel
        from core.world.tile import Tile
        from core.world.structure import Structure
        from core.world.region import Region

        world = WorldModel()
        tiles = data.get("tiles", [])
        if isinstance(tiles, dict):
            iterable = tiles.items()
        else:
            iterable = enumerate(tiles)
        for _key, td in iterable:
            if not isinstance(td, dict):
                continue
            world.set_tile(Tile(
                x=int(td.get("x", 0)),
                y=int(td.get("y", 0)),
                z=int(td.get("z", 7)),
                ground=td.get("ground"),
                items=td.get("items", []) or [],
                spawn=td.get("spawn"),
                zone=td.get("zone"),
            ))
        for sd in data.get("structures", []) or []:
            if isinstance(sd, dict):
                world.add_structure(Structure.from_dict(sd))
        for rd in data.get("regions", []) or []:
            if isinstance(rd, dict):
                world.add_region(Region.from_dict(rd))
        return world

    def _add_cross_cutting_recommendations(
        self,
        all_issues: List[CriticIssue],
        all_recs: List[CriticRecommendation],
        category_results: Dict[str, CriticCategoryResult],
    ) -> None:
        # If two or more critical issues exist, recommend a global review
        critical = [i for i in all_issues if i.severity == IssueSeverity.CRITICAL]
        if len(critical) >= 2:
            all_recs.append(CriticRecommendation(
                title="Critical issues detected — full map review",
                description=f"{len(critical)} critical issues found. Consider a full review of the map.",
                category="global",
                priority=RecommendationPriority.CRITICAL,
            ))
        # If overall score is low, recommend a major rework
        scores = {cat: cr.score.value for cat, cr in category_results.items()}
        avg = (sum(scores.values()) / max(len(scores), 1)) if scores else 0.0
        if avg < 40.0:
            all_recs.append(CriticRecommendation(
                title="Major map rework suggested",
                description=f"Average score is {avg:.1f}. A substantial rework is suggested.",
                category="global",
                priority=RecommendationPriority.HIGH,
            ))

    @staticmethod
    def _dedupe_recommendations(recs: List[CriticRecommendation]) -> List[CriticRecommendation]:
        seen = set()
        out: List[CriticRecommendation] = []
        for r in recs:
            key = (r.title, r.target_location)
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
        return out
       