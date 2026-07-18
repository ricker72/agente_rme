"""BI-4 Blueprint Similarity Engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .similarity_config import SimilarityConfig
from .similarity_result import SimilarityResult

if TYPE_CHECKING:
    from ..models.blueprint import Blueprint

class BlueprintSimilarityEngine:
    """Deterministic blueprint-to-blueprint similarity comparison."""

    def __init__(self, config: SimilarityConfig | None = None) -> None:
        """Initialize with optional configuration."""
        self.config = config or SimilarityConfig()

    def compare(self, target: Blueprint, candidate: Blueprint) -> SimilarityResult:
        """Compare target blueprint against candidate blueprint."""
        reasons = []

        # Type similarity
        type_score = self._type_similarity(target, candidate)
        if type_score > 0:
            reasons.append("matching blueprint type")

        # Region similarity
        region_score = self._region_similarity(target, candidate)
        if region_score > 0:
            reasons.append("shared regions")

        # Pattern similarity
        pattern_score = self._pattern_similarity(target, candidate)
        if pattern_score > 0:
            reasons.append("shared patterns")

        # Dimension similarity
        dimension_score = self._dimension_similarity(target, candidate)
        if dimension_score > 0:
            reasons.append("similar dimensions")

        # Source similarity
        source_score = self._source_similarity(target, candidate)
        if source_score > 0:
            reasons.append("matching source")

        # Calculate weighted score
        norm_weights = self.config.normalized_weights()
        final_score = (
            type_score * norm_weights[0]
            + region_score * norm_weights[1]
            + pattern_score * norm_weights[2]
            + dimension_score * norm_weights[3]
            + source_score * norm_weights[4]
        )

        return SimilarityResult(
            target_id=target.blueprint_id,
            candidate_id=candidate.blueprint_id,
            score=final_score,
            category="blueprint",
            source="similarity_engine",
            reasons=reasons,
        )

    def rank(self, target: Blueprint, candidates: list[Blueprint]) -> list[SimilarityResult]:
        """Rank candidates by similarity to target."""
        results = []

        for candidate in candidates:
            result = self.compare(target, candidate)
            results.append(result)

        # Deterministic sorting: by score descending, then by candidate_id ascending
        results.sort(key=lambda x: (-x.score, x.candidate_id))

        return results

    def _type_similarity(self, target: Blueprint, candidate: Blueprint) -> float:
        """Calculate type similarity score."""
        if target.blueprint_type == candidate.blueprint_type:
            return 1.0

        # Related type groups
        related_groups = {
            "city": {"region"},
            "region": {"city"},
            "hunt": {"dungeon"},
            "dungeon": {"hunt", "boss_area"},
            "boss_area": {"dungeon"},
            "quest_chain": {"region"},
        }

        if candidate.blueprint_type in related_groups.get(target.blueprint_type, set()):
            return 0.5

        return 0.0

    def _region_similarity(self, target: Blueprint, candidate: Blueprint) -> float:
        """Calculate region similarity using Jaccard index."""
        return safe_jaccard(target.regions, candidate.regions)

    def _pattern_similarity(self, target: Blueprint, candidate: Blueprint) -> float:
        """Calculate pattern similarity using Jaccard index."""
        return safe_jaccard(target.patterns, candidate.patterns)

    def _dimension_similarity(self, target: Blueprint, candidate: Blueprint) -> float:
        """Calculate dimension similarity."""
        return dimension_similarity(
            target.width, target.height, candidate.width, candidate.height
        )

    def _source_similarity(self, target: Blueprint, candidate: Blueprint) -> float:
        """Calculate source similarity."""
        if target.provenance.source == candidate.provenance.source:
            return 1.0
        return 0.0

def safe_jaccard(a: list[str], b: list[str]) -> float:
    """Calculate Jaccard similarity between two lists."""

    if not a or not b:
        return 0.0

    set_a = set(a)
    set_b = set(b)

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    if union == 0:
        return 0.0

    return intersection / union

def dimension_similarity(width_a: int, height_a: int, width_b: int, height_b: int) -> float:
    """Calculate dimension similarity."""

    # Handle invalid dimensions safely
    if width_a <= 0 or height_a <= 0 or width_b <= 0 or height_b <= 0:
        return 0.0

    # Exact match
    if width_a == width_b and height_a == height_b:
        return 1.0

    # Area ratio similarity
    area_a = width_a * height_a
    area_b = width_b * height_b

    if area_a == 0 or area_b == 0:
        return 0.0

    area_ratio = min(area_a, area_b) / max(area_a, area_b)

    # Aspect ratio similarity
    aspect_a = width_a / height_a
    aspect_b = width_b / height_b

    if aspect_a == aspect_b:
        aspect_similarity = 1.0
    else:
        # Normalize aspect ratios to avoid extreme values
        aspect_similarity = 1.0 - abs(aspect_a - aspect_b) / (aspect_a + aspect_b)

    # Combine area and aspect similarity
    return 0.7 * area_ratio + 0.3 * aspect_similarity

__all__ = ["BlueprintSimilarityEngine"]
