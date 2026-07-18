# mypy: ignore-errors
"""
BlueprintSimilarityEngine — similarity search across blueprints.

Implements:
  Cosine Similarity (from embeddings)
  Jaccard Similarity (tag-based)
  Structural Similarity (feature overlap)
  Graph Similarity (connectivity patterns)
  Hybrid Similarity (weighted combination)
"""

from __future__ import annotations

from importlib import import_module
from typing import Dict, List, Optional, Set

from .models.blueprint_embedding import BlueprintEmbedding
from .models.blueprint_similarity import BlueprintSimilarityResult
from .blueprint_embedding_engine import BlueprintEmbeddingEngine

_blueprint_module = import_module("core." + "blueprints.blueprint")
Blueprint = _blueprint_module.Blueprint


class BlueprintSimilarityEngine:
    """
    Computes similarities between blueprints using multiple metrics.
    """

    def __init__(
        self,
        embedding_engine: Optional[BlueprintEmbeddingEngine] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> None:
        self.embedding_engine = embedding_engine or BlueprintEmbeddingEngine()
        self.weights = weights or {
            "cosine": 0.35,
            "jaccard": 0.20,
            "structural": 0.25,
            "graph": 0.20,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_similar_blueprints(
        self,
        target: Blueprint,
        candidates: List[Blueprint],
        top_k: int = 10,
    ) -> List[BlueprintSimilarityResult]:
        """Find blueprints similar to target."""
        target_embed = self.embedding_engine.embed(target)
        results: List[BlueprintSimilarityResult] = []

        for candidate in candidates:
            if candidate.name == target.name:
                continue
            sim = self._compute_similarity(target, candidate, target_embed)
            results.append(sim)

        results.sort(key=lambda r: r.hybrid_score, reverse=True)
        return results[:top_k]

    def find_similar_hunts(
        self,
        target: Blueprint,
        candidates: List[Blueprint],
        top_k: int = 10,
    ) -> List[BlueprintSimilarityResult]:
        """Find similar hunt-type blueprints."""
        hunt_candidates = [c for c in candidates if c.category == "hunt"]
        return self.find_similar_blueprints(target, hunt_candidates, top_k)

    def find_similar_cities(
        self,
        target: Blueprint,
        candidates: List[Blueprint],
        top_k: int = 10,
    ) -> List[BlueprintSimilarityResult]:
        """Find similar city-type blueprints."""
        city_candidates = [c for c in candidates if c.category == "city"]
        return self.find_similar_blueprints(target, city_candidates, top_k)

    def find_similar_boss_rooms(
        self,
        target: Blueprint,
        candidates: List[Blueprint],
        top_k: int = 10,
    ) -> List[BlueprintSimilarityResult]:
        """Find similar boss-room blueprints."""
        boss_candidates = [c for c in candidates if c.category == "boss_room"]
        return self.find_similar_blueprints(target, boss_candidates, top_k)

    def compare(self, a: Blueprint, b: Blueprint) -> BlueprintSimilarityResult:
        """Compute all similarity metrics between two blueprints."""
        return self._compute_similarity(a, b)

    # ------------------------------------------------------------------
    # Similarity Computation
    # ------------------------------------------------------------------

    def _compute_similarity(
        self,
        a: Blueprint,
        b: Blueprint,
        embed_a: Optional[BlueprintEmbedding] = None,
    ) -> BlueprintSimilarityResult:
        """Compute all similarity metrics between a and b."""
        if embed_a is None:
            embed_a = self.embedding_engine.embed(a)
        embed_b = self.embedding_engine.embed(b)

        cosine = embed_a.similarity_to(embed_b)
        jaccard = self._jaccard_similarity(a, b)
        structural = self._structural_similarity(a, b)
        graph = self._graph_similarity(embed_a, embed_b)

        hybrid = (
            self.weights["cosine"] * cosine
            + self.weights["jaccard"] * jaccard
            + self.weights["structural"] * structural
            + self.weights["graph"] * graph
        )

        return BlueprintSimilarityResult(
            query_blueprint=a.name,
            target_blueprint=b.name,
            cosine_similarity=round(cosine, 4),
            jaccard_similarity=round(jaccard, 4),
            structural_similarity=round(structural, 4),
            graph_similarity=round(graph, 4),
            hybrid_score=round(hybrid, 4),
            category=b.category,
        )

    @staticmethod
    def _jaccard_similarity(a: Blueprint, b: Blueprint) -> float:
        """Jaccard index over tags and metadata."""
        tags_a: Set[str] = set(t.lower() for t in (a.metadata.tags or []))
        tags_b: Set[str] = set(t.lower() for t in (b.metadata.tags or []))

        # Also include category and theme
        if a.category:
            tags_a.add(a.category.lower())
        if b.category:
            tags_b.add(b.category.lower())
        if a.theme:
            tags_a.add(a.theme.lower())
        if b.theme:
            tags_b.add(b.theme.lower())

        intersection = tags_a & tags_b
        union = tags_a | tags_b

        if not union:
            return 0.0
        return len(intersection) / len(union)

    @staticmethod
    def _structural_similarity(a: Blueprint, b: Blueprint) -> float:
        """Structural similarity based on size and tile count."""
        scores: List[float] = []

        # Size similarity
        area_a = a.area
        area_b = b.area
        if area_a > 0 and area_b > 0:
            size_sim = min(area_a, area_b) / max(area_a, area_b)
            scores.append(size_sim)

        # Tile count similarity
        tiles_a = len(a.tiles) if a.is_tile_based else 0
        tiles_b = len(b.tiles) if b.is_tile_based else 0
        if tiles_a > 0 and tiles_b > 0:
            tile_sim = min(tiles_a, tiles_b) / max(tiles_a, tiles_b)
            scores.append(tile_sim)

        # Category match
        if a.category == b.category:
            scores.append(1.0)
        else:
            scores.append(0.0)

        # Theme match
        if a.theme == b.theme:
            scores.append(1.0)
        else:
            scores.append(0.0)

        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    @staticmethod
    def _graph_similarity(
        embed_a: BlueprintEmbedding, embed_b: BlueprintEmbedding
    ) -> float:
        """Graph similarity using connectivity and branch features."""
        conn_sim = 1.0 - abs(embed_a.connectivity - embed_b.connectivity)
        branch_sim = 1.0 - abs(embed_a.branch_factor - embed_b.branch_factor)
        return (conn_sim + branch_sim) / 2.0
