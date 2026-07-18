"""BI-4 Pattern Similarity Engine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .similarity_result import SimilarityResult

if TYPE_CHECKING:
    from ..models.pattern import Pattern

class PatternSimilarityEngine:
    """Deterministic pattern-to-pattern similarity comparison."""

    def compare(self, target: Pattern, candidate: Pattern) -> SimilarityResult:
        """Compare target pattern against candidate pattern."""
        reasons = []

        # Category similarity
        category_score = self._category_similarity(target, candidate)
        if category_score > 0:
            reasons.append("matching category")

        # Source similarity
        source_score = self._source_similarity(target, candidate)
        if source_score > 0:
            reasons.append("matching source")

        # Tag similarity
        tag_score = self._tag_similarity(target, candidate)
        if tag_score > 0:
            reasons.append("shared tags")

        # Confidence compatibility
        confidence_score = self._confidence_similarity(target, candidate)
        if confidence_score > 0:
            reasons.append("similar confidence")

        # Calculate final score (equal weighting)
        final_score = (category_score + source_score + tag_score + confidence_score) / 4.0

        return SimilarityResult(
            target_id=target.pattern_id,
            candidate_id=candidate.pattern_id,
            score=final_score,
            category="pattern",
            source="similarity_engine",
            reasons=reasons,
        )

    def rank(self, target: Pattern, candidates: list[Pattern]) -> list[SimilarityResult]:
        """Rank candidates by similarity to target."""
        results = []

        for candidate in candidates:
            result = self.compare(target, candidate)
            results.append(result)

        # Deterministic sorting: by score descending, then by candidate_id ascending
        results.sort(key=lambda x: (-x.score, x.candidate_id))

        return results

    def _category_similarity(self, target: Pattern, candidate: Pattern) -> float:
        """Calculate category similarity."""
        if target.category == candidate.category:
            return 1.0
        return 0.0

    def _source_similarity(self, target: Pattern, candidate: Pattern) -> float:
        """Calculate source similarity."""
        if target.source == candidate.source:
            return 1.0
        return 0.0

    def _tag_similarity(self, target: Pattern, candidate: Pattern) -> float:
        """Calculate tag similarity using Jaccard index."""
        return safe_jaccard(target.tags, candidate.tags)

    def _confidence_similarity(self, target: Pattern, candidate: Pattern) -> float:
        """Calculate confidence compatibility."""
        # 1.0 - absolute confidence difference
        confidence_diff: float = abs(target.confidence - candidate.confidence)
        return 1.0 - confidence_diff

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

__all__ = ["PatternSimilarityEngine"]
