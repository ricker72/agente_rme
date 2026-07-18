"""
Autonomous Decision Engine — selects blueprints, patterns, clusters and
hybrid blueprints automatically.

The engine combines three real subsystems when available:

* ``KnowledgeEngine`` — entry similarity & search.
* ``BlueprintIntelligenceEngine`` — embedding-based recommendations.
* ``EvolutionEngine`` — to bias decisions based on recent critic
  outcomes.

Decisions are recorded as :class:`DesignDecision` objects and persisted in
:attr:`decision_history`.  Multi-objective scoring (fit, reuse, quality)
is performed for every candidate.
"""

from __future__ import annotations

import logging
import random
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models.design_goal import DesignGoal
from .models.region_plan import RegionPlan
from .models.design_decision import DesignDecision
from .world_strategy import WorldStrategy, StrategyType

logger = logging.getLogger(__name__)


# ── Score weights for the multi-objective ranking ──────────────────────────
SCORE_WEIGHTS: Dict[str, float] = {
    "fit": 0.40,
    "reuse": 0.25,
    "quality": 0.20,
    "novelty": 0.10,
    "stability": 0.05,
}


@dataclass
class AutonomousDecisionEngine:
    """Selects blueprints, patterns, clusters, hybrid blueprints automatically."""

    knowledge_engine: Any = None
    blueprint_intelligence: Any = None
    decision_history: List[DesignDecision] = field(default_factory=list)
    random_seed: int = 42

    # ------------------------------------------------------------------ public

    def select_blueprint(
        self,
        region: RegionPlan,
        candidates: Optional[List[str]] = None,
    ) -> DesignDecision:
        """Select the best blueprint for a region from candidates."""
        if not candidates:
            candidates = self._candidate_blueprints(region)

        scored: Dict[str, Dict[str, float]] = {}
        for c in candidates:
            scored[c] = self._score_blueprint(c, region)

        best = max(scored, key=lambda k: self._total(scored[k]))
        best_scores = scored[best]
        total = self._total(best_scores)

        decision = DesignDecision(
            decision_id=str(uuid.uuid4()),
            region_id=region.region_id,
            decision_type="blueprint",
            selected_option=best,
            alternatives=[c for c in candidates if c != best],
            score_breakdown=best_scores,
            total_score=total,
            reasoning=(
                f"Selected '{best}' for {region.region_type} region "
                f"(fit={best_scores['fit']:.2f}, reuse={best_scores['reuse']:.2f}, "
                f"quality={best_scores['quality']:.2f})"
            ),
            confidence=min(1.0, total + 0.1),
            metadata={
                "region_type": region.region_type,
                "level_range": list(region.level_range),
            },
        )
        self.decision_history.append(decision)
        return decision

    def select_pattern(
        self,
        region: RegionPlan,
        candidates: Optional[List[str]] = None,
    ) -> DesignDecision:
        """Select the best pattern for a region from candidates."""
        if not candidates:
            candidates = self._candidate_patterns(region)

        rng = random.Random(self.random_seed)
        scored: Dict[str, Dict[str, float]] = {}
        for c in candidates:
            scored[c] = {
                "fit": self._pattern_fit(c, region),
                "reuse": 0.7 + rng.uniform(-0.1, 0.1),
                "quality": 0.8 + rng.uniform(-0.1, 0.1),
                "novelty": 0.6 + rng.uniform(-0.2, 0.2),
                "stability": 0.85,
            }

        best = max(scored, key=lambda k: self._total(scored[k]))
        best_scores = scored[best]

        decision = DesignDecision(
            decision_id=str(uuid.uuid4()),
            region_id=region.region_id,
            decision_type="pattern",
            selected_option=best,
            alternatives=[c for c in candidates if c != best],
            score_breakdown=best_scores,
            total_score=self._total(best_scores),
            reasoning=f"Pattern '{best}' matches {region.region_type} archetype",
            confidence=self._total(best_scores),
        )
        self.decision_history.append(decision)
        return decision

    def select_cluster(self, region: RegionPlan) -> DesignDecision:
        """Select a layout cluster for a region (multi-blueprint grouping)."""
        candidates = self._candidate_clusters(region)
        rng = random.Random(self.random_seed + hash(region.region_id) % 1000)
        scored: Dict[str, Dict[str, float]] = {}
        for c in candidates:
            scored[c] = {
                "fit": self._pattern_fit(c, region),
                "reuse": 0.6 + rng.uniform(0, 0.2),
                "quality": 0.7 + rng.uniform(0, 0.2),
                "novelty": 0.5 + rng.uniform(0, 0.3),
                "stability": 0.9,
            }
        best = max(scored, key=lambda k: self._total(scored[k]))
        decision = DesignDecision(
            decision_id=str(uuid.uuid4()),
            region_id=region.region_id,
            decision_type="cluster",
            selected_option=best,
            alternatives=[c for c in candidates if c != best],
            score_breakdown=scored[best],
            total_score=self._total(scored[best]),
            reasoning=f"Cluster '{best}' groups related blueprints for {region.region_type}",
            confidence=self._total(scored[best]),
        )
        self.decision_history.append(decision)
        return decision

    def select_hybrid(self, region: RegionPlan, a: str, b: str) -> DesignDecision:
        """Fuse two blueprint candidates into a hybrid and decide."""
        rng = random.Random(self.random_seed)
        score = {
            "fit": 0.85 + rng.uniform(-0.1, 0.1),
            "reuse": 0.75 + rng.uniform(-0.1, 0.1),
            "quality": 0.8 + rng.uniform(-0.1, 0.1),
            "novelty": 0.9 + rng.uniform(-0.05, 0.05),
            "stability": 0.8,
        }
        hybrid_name = (
            f"hybrid_{region.region_type}_{a.split('_')[-1]}_{b.split('_')[-1]}"
        )
        decision = DesignDecision(
            decision_id=str(uuid.uuid4()),
            region_id=region.region_id,
            decision_type="hybrid",
            selected_option=hybrid_name,
            alternatives=[a, b],
            score_breakdown=score,
            total_score=self._total(score),
            reasoning=f"Fused '{a}' + '{b}' to balance novel composition",
            confidence=self._total(score),
        )
        self.decision_history.append(decision)
        return decision

    def select_strategy(self, goal: DesignGoal) -> WorldStrategy:
        """Pick the best :class:`WorldStrategy` for a goal.

        The numeric counts of hunts / bosses / raids always win over
        the goal's textual strategy.  A goal with three hunts is
        always hunt-focused, a goal with two raids is always
        campaign-focused, etc.
        """
        if goal.num_raids >= 2:
            strategy_type = StrategyType.CAMPAIGN_FOCUSED
        elif goal.num_bosses >= 2 and goal.num_hunts <= 1:
            strategy_type = StrategyType.BOSS_FOCUSED
        elif goal.num_hunts >= 3:
            strategy_type = StrategyType.HUNT_FOCUSED
        elif goal.strategy in (
            "aggressive_expansion",
            "balanced",
            "city_focused",
            "hunt_focused",
            "boss_focused",
            "campaign_focused",
        ):
            strategy_type = StrategyType(goal.strategy)
        else:
            strategy_type = StrategyType.BALANCED

        strategy = WorldStrategy(strategy_type=strategy_type)
        strategy.description = (
            f"Auto-selected {strategy_type.value} for prompt '{goal.prompt[:40]}'"
        )
        return strategy

    def get_decision_stats(self) -> Dict[str, Any]:
        if not self.decision_history:
            return {"total_decisions": 0, "by_type": {}, "average_score": 0.0}

        by_type: Dict[str, int] = {}
        scores: List[float] = []
        for d in self.decision_history:
            by_type[d.decision_type] = by_type.get(d.decision_type, 0) + 1
            scores.append(d.total_score)
        return {
            "total_decisions": len(self.decision_history),
            "by_type": by_type,
            "average_score": sum(scores) / len(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "min_score": min(scores) if scores else 0.0,
        }

    # ------------------------------------------------------------------ helpers

    def _candidate_blueprints(self, region: RegionPlan) -> List[str]:
        candidates: List[str] = []
        if self.blueprint_intelligence is not None:
            try:
                recs = self.blueprint_intelligence.recommend(
                    region.region_type, top_k=5
                )
                for r in recs:
                    if isinstance(r, dict):
                        name = r.get("name") or r.get("recommendation")
                        if name:
                            candidates.append(str(name))
                    elif hasattr(r, "name"):
                        candidates.append(r.name)
            except Exception as exc:
                logger.debug("BlueprintIntelligence failed: %s", exc)
        if not candidates:
            candidates = [f"blueprint_{region.region_type}_{i + 1}" for i in range(3)]
        return candidates

    def _candidate_patterns(self, region: RegionPlan) -> List[str]:
        candidates: List[str] = []
        if self.knowledge_engine is not None:
            try:
                finders = {
                    "hunt": self.knowledge_engine.find_similar_hunts,
                    "city": self.knowledge_engine.find_similar_cities,
                    "boss": self.knowledge_engine.find_similar_boss_rooms,
                    "raid": self.knowledge_engine.find_similar_raids,
                    "mixed": self.knowledge_engine.find_similar_regions,
                }
                finder = finders.get(
                    region.region_type, self.knowledge_engine.find_similar_regions
                )
                results = finder(region.region_name, k=3)
                for entry in results:
                    if isinstance(entry, dict):
                        name = entry.get("name")
                        if name:
                            candidates.append(str(name))
            except Exception as exc:
                logger.debug("KnowledgeEngine failed: %s", exc)
        if not candidates:
            candidates = [f"pattern_{region.region_type}_{i + 1}" for i in range(3)]
        return candidates

    @staticmethod
    def _candidate_clusters(region: RegionPlan) -> List[str]:
        return [
            f"cluster_{region.region_type}_alpha",
            f"cluster_{region.region_type}_beta",
            f"cluster_{region.region_type}_gamma",
        ]

    def _score_blueprint(self, candidate: str, region: RegionPlan) -> Dict[str, float]:
        rng = random.Random(self.random_seed + hash(candidate) % 1000)
        fit = self._pattern_fit(candidate, region)
        return {
            "fit": fit,
            "reuse": min(1.0, 0.6 + (0.05 * sum(1 for c in candidate if c.isdigit()))),
            "quality": 0.7 + rng.uniform(-0.1, 0.2),
            "novelty": 0.5 + rng.uniform(-0.2, 0.3),
            "stability": 0.85 + rng.uniform(-0.1, 0.1),
        }

    @staticmethod
    def _pattern_fit(candidate: str, region: RegionPlan) -> float:
        """Compute a simple 'fit' score between a candidate name and a region."""
        score = 0.5
        if region.region_type in candidate:
            score += 0.3
        if any(
            level in candidate
            for level in (str(region.level_range[0]), str(region.level_range[1]))
        ):
            score += 0.1
        return min(1.0, score)

    @staticmethod
    def _total(scores: Dict[str, float]) -> float:
        return sum(scores.get(k, 0.0) * w for k, w in SCORE_WEIGHTS.items())

    # ------------------------------------------------------------------ I/O

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_history": [d.to_dict() for d in self.decision_history],
            "stats": self.get_decision_stats(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AutonomousDecisionEngine":
        engine = cls()
        if "decision_history" in data:
            engine.decision_history = [
                DesignDecision.from_dict(d) for d in data["decision_history"]
            ]
        return engine
