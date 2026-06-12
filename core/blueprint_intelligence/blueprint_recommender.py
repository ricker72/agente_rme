"""
BlueprintRecommender — suggests patterns and designs.

Capable of:
  "Use Roshamuul corridor pattern"
  "Use Issavi city layout"
  "Use Falcon boss design"
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from core.blueprints.blueprint import Blueprint
from .models.blueprint_pattern import BlueprintPattern
from .models.blueprint_cluster import BlueprintCluster
from .models.blueprint_embedding import BlueprintEmbedding
from .blueprint_embedding_engine import BlueprintEmbeddingEngine
from .blueprint_similarity_engine import BlueprintSimilarityEngine


class BlueprintRecommender:
    """
    Recommends patterns, layouts, and designs from known successful blueprints.
    """

    def __init__(
        self,
        embedding_engine: Optional[BlueprintEmbeddingEngine] = None,
        similarity_engine: Optional[BlueprintSimilarityEngine] = None,
    ) -> None:
        self.embedding_engine = embedding_engine or BlueprintEmbeddingEngine()
        self.similarity_engine = similarity_engine or BlueprintSimilarityEngine(
            embedding_engine=self.embedding_engine,
        )
        self.patterns: List[BlueprintPattern] = []
        self.clusters: List[BlueprintCluster] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def recommend_pattern(
        self,
        query_type: str,
        blueprints: List[Blueprint],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Recommend patterns based on a query type.

        Args:
            query_type: Type of recommendation (e.g., "corridor", "city", "boss")
            blueprints: Available blueprints to search.
            top_k: Number of recommendations.

        Returns:
            List of recommendation dicts with pattern name, source, and confidence.
        """
        # Filter blueprints by type relevance
        relevant: List[Blueprint] = []
        query_lower = query_type.lower()

        for bp in blueprints:
            tags_lower = [t.lower() for t in (bp.metadata.tags or [])]
            cat_lower = (bp.category or "").lower()
            theme_lower = (bp.theme or "").lower()
            desc_lower = (bp.description or "").lower()

            if (
                query_lower in tags_lower
                or query_lower in cat_lower
                or query_lower in theme_lower
                or query_lower in desc_lower
            ):
                relevant.append(bp)

        if not relevant:
            # Fall back to all blueprints
            relevant = blueprints

        # Score and rank
        scored: List[Dict[str, Any]] = []
        for bp in relevant:
            embedding = self.embedding_engine.embed(bp)
            score = self._calc_relevance_score(bp, embedding, query_type)
            scored.append(
                {
                    "recommendation": f"Use {bp.name} {query_type} pattern",
                    "blueprint_name": bp.name,
                    "category": bp.category,
                    "theme": bp.theme,
                    "confidence": round(score, 2),
                    "source": "pattern_library",
                }
            )

        scored.sort(key=lambda x: x["confidence"], reverse=True)
        return scored[:top_k]

    def recommend_layout(
        self,
        query: str,
        blueprints: List[Blueprint],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Recommend a layout based on a natural language query.

        Example:
          "compact city layout" -> recommends Issavi-style layouts
        """
        query_lower = query.lower()
        scored: List[Dict[str, Any]] = []

        for bp in blueprints:
            score = 0.0
            desc_lower = (bp.description or "").lower()
            tags_lower = [t.lower() for t in (bp.metadata.tags or [])]

            # Keyword matching
            for word in query_lower.split():
                if word in desc_lower or word in tags_lower:
                    score += 0.2
                if word in (bp.theme or "").lower():
                    score += 0.3
                if word in (bp.category or "").lower():
                    score += 0.3

            if score > 0:
                scored.append(
                    {
                        "recommendation": f"Use {bp.name} layout",
                        "blueprint_name": bp.name,
                        "category": bp.category,
                        "theme": bp.theme,
                        "confidence": round(min(1.0, score), 2),
                        "source": "layout_library",
                    }
                )

        scored.sort(key=lambda x: x["confidence"], reverse=True)
        return scored[:top_k]

    def recommend_boss_design(
        self,
        blueprints: List[Blueprint],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Recommend boss room designs from known boss blueprints."""
        return self.recommend_pattern("boss", blueprints, top_k)

    def recommend_city_layout(
        self,
        blueprints: List[Blueprint],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Recommend city layouts."""
        return self.recommend_pattern("city", blueprints, top_k)

    def recommend_corridor_pattern(
        self,
        blueprints: List[Blueprint],
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Recommend corridor/hallway patterns."""
        return self.recommend_pattern("corridor", blueprints, top_k)

    def get_recommendations(
        self,
        blueprints: List[Blueprint],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Get general recommendations from the blueprint library."""
        recommendations: List[Dict[str, Any]] = []

        for bp in blueprints:
            embedding = self.embedding_engine.embed(bp)
            base_score = 0.5

            # Boost high-quality blueprints
            if embedding.critic_score > 0.7:
                base_score += 0.2
                recommendations.append(
                    {
                        "recommendation": f"Use {bp.name} design pattern (high critic score)",
                        "blueprint_name": bp.name,
                        "category": bp.category,
                        "theme": bp.theme,
                        "confidence": round(base_score, 2),
                        "source": "quality_recommendation",
                    }
                )

            if embedding.playtest_score > 0.7:
                base_score += 0.1
                recommendations.append(
                    {
                        "recommendation": f"Use {bp.name} layout (high playtest score)",
                        "blueprint_name": bp.name,
                        "category": bp.category,
                        "theme": bp.theme,
                        "confidence": round(base_score, 2),
                        "source": "playtest_recommendation",
                    }
                )

            if bp.metadata.hybrid:
                recommendations.append(
                    {
                        "recommendation": f"Consider {bp.name} hybrid design",
                        "blueprint_name": bp.name,
                        "category": bp.category,
                        "theme": bp.theme,
                        "confidence": 0.85,
                        "source": "hybrid_recommendation",
                    }
                )

        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        return recommendations[:top_k]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _calc_relevance_score(
        self,
        bp: Blueprint,
        embedding: BlueprintEmbedding,
        query_type: str,
    ) -> float:
        """Calculate relevance score for a recommendation."""
        score = 0.5  # base

        qt = query_type.lower()
        tags = [t.lower() for t in (bp.metadata.tags or [])]

        if qt in tags:
            score += 0.3
        if qt == (bp.category or "").lower():
            score += 0.2
        if qt == (bp.theme or "").lower():
            score += 0.2

        # Boost quality
        score += embedding.critic_score * 0.1
        score += embedding.playtest_score * 0.1

        return min(1.0, score)

    def load_patterns(self, path: str) -> None:
        """Load patterns from a JSON file."""
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            self.patterns = [BlueprintPattern.from_dict(p) for p in data]

    def save_patterns(self, path: str) -> None:
        """Save patterns to a JSON file."""
        with open(path, "w") as f:
            json.dump([p.to_dict() for p in self.patterns], f, indent=2)
