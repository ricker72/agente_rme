# mypy: ignore-errors
"""
BlueprintRanker — ranks blueprints based on multiple criteria.

Ranking based on:
  critic_score, playtest_score, reuse_score, knowledge_score, complexity_score
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import Dict, List, Optional

from .models.blueprint_embedding import BlueprintEmbedding
from .blueprint_embedding_engine import BlueprintEmbeddingEngine

_blueprint_module = import_module("core." + "blueprints.blueprint")
Blueprint = _blueprint_module.Blueprint


@dataclass
class RankedBlueprint:
    """A blueprint with its ranking scores."""

    blueprint_name: str = ""
    critic_score: float = 0.0
    playtest_score: float = 0.0
    reuse_score: float = 0.0
    knowledge_score: float = 0.0
    complexity_score: float = 0.0
    overall_rank: float = 0.0
    category: str = ""


class BlueprintRanker:
    """
    Ranks blueprints using weighted scoring across multiple criteria.
    """

    def __init__(
        self,
        embedding_engine: Optional[BlueprintEmbeddingEngine] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.embedding_engine = embedding_engine or BlueprintEmbeddingEngine()
        self.weights = weights or {
            "critic": 0.30,
            "playtest": 0.25,
            "reuse": 0.15,
            "knowledge": 0.15,
            "complexity": 0.15,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rank(
        self,
        blueprints: List[Blueprint],
        top_k: Optional[int] = None,
    ) -> List[RankedBlueprint]:
        """Rank blueprints and return sorted results."""
        ranked: List[RankedBlueprint] = []

        for bp in blueprints:
            embedding = self.embedding_engine.embed(bp)
            rb = self._score_blueprint(bp, embedding)
            ranked.append(rb)

        ranked.sort(key=lambda r: r.overall_rank, reverse=True)

        if top_k is not None:
            return ranked[:top_k]
        return ranked

    def rank_single(self, blueprint: Blueprint) -> RankedBlueprint:
        """Rank a single blueprint."""
        embedding = self.embedding_engine.embed(blueprint)
        return self._score_blueprint(blueprint, embedding)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _score_blueprint(
        self, bp: Blueprint, embedding: BlueprintEmbedding
    ) -> RankedBlueprint:
        """Compute all ranking scores for a blueprint."""
        critic_score = self._score_critic(bp, embedding)
        playtest_score = self._score_playtest(bp, embedding)
        reuse_score = self._score_reuse(bp)
        knowledge_score = self._score_knowledge(bp, embedding)
        complexity_score = self._score_complexity(bp, embedding)

        overall = (
            self.weights["critic"] * critic_score
            + self.weights["playtest"] * playtest_score
            + self.weights["reuse"] * reuse_score
            + self.weights["knowledge"] * knowledge_score
            + self.weights["complexity"] * complexity_score
        )

        return RankedBlueprint(
            blueprint_name=bp.name,
            critic_score=round(critic_score, 2),
            playtest_score=round(playtest_score, 2),
            reuse_score=round(reuse_score, 2),
            knowledge_score=round(knowledge_score, 2),
            complexity_score=round(complexity_score, 2),
            overall_rank=round(overall, 2),
            category=bp.category,
        )

    @staticmethod
    def _score_critic(bp: Blueprint, embedding: BlueprintEmbedding) -> float:
        """Critic score (0-100)."""
        return embedding.critic_score * 100.0

    @staticmethod
    def _score_playtest(bp: Blueprint, embedding: BlueprintEmbedding) -> float:
        """Playtest score (0-100)."""
        return embedding.playtest_score * 100.0

    @staticmethod
    def _score_reuse(bp: Blueprint) -> float:
        """Reuse score based on metadata and tags."""
        score = 50.0  # default
        tags = bp.metadata.tags or []
        reuse_indicators = {"hybrid", "template", "reusable", "modular"}
        found = sum(1 for t in tags if t.lower() in reuse_indicators)
        score += found * 20.0

        if bp.metadata.hybrid:
            score += 25.0
        if bp.is_tile_based:
            score += 10.0
        return min(100.0, score)

    @staticmethod
    def _score_knowledge(bp: Blueprint, embedding: BlueprintEmbedding) -> float:
        """Knowledge contribution score."""
        score = 30.0
        score += embedding.tile_density * 20.0
        score += embedding.room_count * 15.0
        score += embedding.boss_count * 15.0
        score += embedding.city_services * 10.0
        score += embedding.waypoint_count * 10.0
        return min(100.0, score)

    @staticmethod
    def _score_complexity(bp: Blueprint, embedding: BlueprintEmbedding) -> float:
        """Complexity score based on structural features."""
        score = 20.0
        score += embedding.branch_factor * 20.0
        score += embedding.connectivity * 15.0
        score += embedding.corridor_count * 15.0
        score += embedding.room_count * 15.0
        score += embedding.spawn_density * 15.0
        return min(100.0, score)
