"""BlueprintSimilarityResult model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class BlueprintSimilarityResult:
    """
    Result of a similarity query against one blueprint.
    """

    query_blueprint: str = ""
    target_blueprint: str = ""
    cosine_similarity: float = 0.0
    jaccard_similarity: float = 0.0
    structural_similarity: float = 0.0
    graph_similarity: float = 0.0
    hybrid_score: float = 0.0
    category: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_blueprint": self.query_blueprint,
            "target_blueprint": self.target_blueprint,
            "cosine_similarity": self.cosine_similarity,
            "jaccard_similarity": self.jaccard_similarity,
            "structural_similarity": self.structural_similarity,
            "graph_similarity": self.graph_similarity,
            "hybrid_score": self.hybrid_score,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BlueprintSimilarityResult:
        return cls(
            query_blueprint=data.get("query_blueprint", ""),
            target_blueprint=data.get("target_blueprint", ""),
            cosine_similarity=data.get("cosine_similarity", 0.0),
            jaccard_similarity=data.get("jaccard_similarity", 0.0),
            structural_similarity=data.get("structural_similarity", 0.0),
            graph_similarity=data.get("graph_similarity", 0.0),
            hybrid_score=data.get("hybrid_score", 0.0),
            category=data.get("category", ""),
        )