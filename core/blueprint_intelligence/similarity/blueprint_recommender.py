"""Blueprint recommendation facade for BI-4 similarity."""

from __future__ import annotations

from .explanation_engine import strongest_dimensions, weakest_dimensions
from .similarity_engine import SimilarityEngine


class BlueprintRecommender:
    """Typed recommendation helpers backed by a BI-4 SimilarityEngine."""

    def __init__(self, engine: SimilarityEngine) -> None:
        self.engine = engine

    def recommend_city(
        self, reference_blueprint_id: str, top_k: int = 10
    ) -> list[dict[str, object]]:
        return self._recommend(reference_blueprint_id, "city", top_k)

    def recommend_hunt(
        self, reference_blueprint_id: str, top_k: int = 10
    ) -> list[dict[str, object]]:
        return self._recommend(reference_blueprint_id, "hunt", top_k)

    def recommend_spawn(
        self, reference_blueprint_id: str, top_k: int = 10
    ) -> list[dict[str, object]]:
        return self._recommend(reference_blueprint_id, "spawn", top_k)

    def recommend_dungeon(
        self, reference_blueprint_id: str, top_k: int = 10
    ) -> list[dict[str, object]]:
        return self._recommend(reference_blueprint_id, "dungeon", top_k)

    def _recommend(
        self, reference_blueprint_id: str, blueprint_type: str, top_k: int
    ) -> list[dict[str, object]]:
        source = self.engine.features[reference_blueprint_id]
        if source.blueprint_type != blueprint_type:
            raise ValueError("Reference blueprint type does not match recommender method")
        recommendations = []
        for match in self.engine.find_similar(reference_blueprint_id, top_k):
            recommendations.append(
                {
                    "match_id": match.target_blueprint_id,
                    "score": round(match.score, 6),
                    "explanation": list(match.explanation),
                    "strongest_dimensions": strongest_dimensions(match.dimensions),
                    "weakest_dimensions": weakest_dimensions(match.dimensions),
                }
            )
        return recommendations


__all__ = ["BlueprintRecommender"]
