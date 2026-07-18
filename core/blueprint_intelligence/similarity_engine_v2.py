# mypy: ignore-errors
"""
Blueprint Intelligence 2.0 — Similarity Engine v2.

Answers the question: "What blueprint is most similar to this one?"

Supports comparisons between:
  - BlueprintV2 vs BlueprintV2
  - BlueprintV2 vs Pattern Library
  - Custom input vs all known blueprints

Uses feature-vector cosine similarity and structural metric overlap.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from .models.blueprint_v2 import BlueprintV2
from .models.pattern_v2 import PatternV2
from .pattern_library import PatternLibrary


@dataclass
class SimilarityResultV2:
    """Result of a similarity comparison."""

    query_name: str
    target_name: str
    target_type: str
    cosine_similarity: float
    structural_similarity: float
    tag_overlap: float
    hybrid_score: float
    source: str = ""

    def to_dict(self) -> Dict[str, Union[float, str]]:
        return {
            "query_name": self.query_name,
            "target_name": self.target_name,
            "target_type": self.target_type,
            "cosine_similarity": self.cosine_similarity,
            "structural_similarity": self.structural_similarity,
            "tag_overlap": self.tag_overlap,
            "hybrid_score": self.hybrid_score,
            "source": self.source,
        }


class SimilarityEngineV2:
    """
    Blueprint Intelligence 2.0 — Similarity Engine.

    Computes similarity between BlueprintV2 instances using:
      - Cosine similarity (feature vector)
      - Structural similarity (metrics overlap)
      - Tag overlap (semantic matching)
      - Hybrid score (weighted combination)
    """

    WEIGHTS = {
        "cosine": 0.40,
        "structural": 0.35,
        "tags": 0.25,
    }

    def __init__(self, pattern_library: Optional[PatternLibrary] = None):
        self.pattern_library = pattern_library or PatternLibrary()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_similar(
        self,
        query: BlueprintV2,
        candidates: List[BlueprintV2],
        top_k: int = 10,
    ) -> List[SimilarityResultV2]:
        """
        Find blueprints similar to the query.

        Args:
            query: BlueprintV2 to compare against.
            candidates: List of candidate blueprints.
            top_k: Maximum number of results.

        Returns:
            Sorted list of SimilarityResultV2 (highest first).
        """
        results: List[SimilarityResultV2] = []

        for candidate in candidates:
            if candidate.blueprint_id == query.blueprint_id:
                continue
            candidate.provenance  # ensure provenance is accessed

            sim = self.compare(query, candidate)
            results.append(sim)

        results.sort(key=lambda r: r.hybrid_score, reverse=True)
        return results[:top_k]

    def find_similar_by_type(
        self,
        query: BlueprintV2,
        candidates: List[BlueprintV2],
        bp_type: str,
        top_k: int = 10,
    ) -> List[SimilarityResultV2]:
        """Find similar blueprints of a specific type."""
        filtered = [c for c in candidates if c.type == bp_type]
        return self.find_similar(query, filtered, top_k)

    def compare(self, a: BlueprintV2, b: BlueprintV2) -> SimilarityResultV2:
        """
        Compute all similarity metrics between two blueprints.

        Args:
            a: First blueprint.
            b: Second blueprint.

        Returns:
            SimilarityResultV2 with all metrics.
        """
        cosine = self._cosine_similarity(a, b)
        structural = self._structural_similarity(a, b)
        tags = self._tag_overlap(a, b)

        hybrid = (
            self.WEIGHTS["cosine"] * cosine
            + self.WEIGHTS["structural"] * structural
            + self.WEIGHTS["tags"] * tags
        )

        return SimilarityResultV2(
            query_name=a.name,
            target_name=b.name,
            target_type=b.type,
            cosine_similarity=round(cosine, 4),
            structural_similarity=round(structural, 4),
            tag_overlap=round(tags, 4),
            hybrid_score=round(hybrid, 4),
            source=b.provenance.source,
        )

    def compare_to_patterns(
        self,
        query: BlueprintV2,
        top_k: int = 5,
    ) -> List[SimilarityResultV2]:
        """
        Compare a blueprint against all patterns in the library.

        Args:
            query: BlueprintV2 to compare.
            top_k: Maximum results.

        Returns:
            Sorted list of pattern similarities.
        """
        results: List[SimilarityResultV2] = []

        for pattern in self.pattern_library.list_all():
            cosine = SimilarityEngineV2._cosine_with_pattern(query, pattern)
            structural = SimilarityEngineV2._pattern_structural_similarity(
                query, pattern
            )
            tags = SimilarityEngineV2._tag_overlap_with_pattern(query, pattern)

            hybrid = (
                self.WEIGHTS["cosine"] * cosine
                + self.WEIGHTS["structural"] * structural
                + self.WEIGHTS["tags"] * tags
            )

            results.append(
                SimilarityResultV2(
                    query_name=query.name,
                    target_name=pattern.name,
                    target_type=pattern.pattern_type,
                    cosine_similarity=round(cosine, 4),
                    structural_similarity=round(structural, 4),
                    tag_overlap=round(tags, 4),
                    hybrid_score=round(hybrid, 4),
                    source=pattern.source_blueprint,
                )
            )

        results.sort(key=lambda r: r.hybrid_score, reverse=True)
        return results[:top_k]

    def classify(
        self,
        query: BlueprintV2,
        candidates: List[BlueprintV2],
    ) -> Dict[str, float]:
        """
        Classify a blueprint by finding which source it's most similar to.

        Groups candidates by provenance source and returns
        aggregate similarity per source.

        Args:
            query: BlueprintV2 to classify.
            candidates: Known blueprints with provenance.

        Returns:
            Dict of {source: aggregate_similarity}.
        """
        source_scores: Dict[str, List[float]] = {}

        for candidate in candidates:
            if candidate.blueprint_id == query.blueprint_id:
                continue
            source = candidate.provenance.source
            if not source:
                continue
            sim = self.compare(query, candidate)
            source_scores.setdefault(source, []).append(sim.hybrid_score)

        # Aggregate by source (mean score)
        result: Dict[str, float] = {}
        for source, scores in source_scores.items():
            result[source] = round(sum(scores) / len(scores), 4)

        # Sort by score descending
        return dict(sorted(result.items(), key=lambda x: x[1], reverse=True))

    # ------------------------------------------------------------------
    # Similarity metrics
    # ------------------------------------------------------------------

    @staticmethod
    def _cosine_similarity(a: BlueprintV2, b: BlueprintV2) -> float:
        """Cosine similarity between structural metric vectors."""
        vec_a = SimilarityEngineV2._to_vector(a)
        vec_b = SimilarityEngineV2._to_vector(b)

        dot = sum(va * vb for va, vb in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(v * v for v in vec_a))
        norm_b = math.sqrt(sum(v * v for v in vec_b))

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _to_vector(bp: BlueprintV2) -> List[float]:
        """Convert a blueprint's key metrics to a feature vector."""
        area_norm = min(1.0, bp.area / 262144.0)  # Normalize to 512x512 = 262144

        return [
            area_norm,
            min(1.0, bp.regions / 20.0),
            min(1.0, bp.roads / 30.0),
            min(1.0, bp.landmarks / 15.0),
            min(1.0, bp.districts / 10.0),
            min(1.0, bp.spawn_clusters / 50.0),
            min(1.0, bp.waypoints / 30.0),
            min(1.0, bp.connectivity_score / 100.0),
            min(1.0, bp.density_score / 100.0),
            min(1.0, bp.navigation_score / 100.0),
            min(1.0, bp.blueprint_score / 100.0),
        ]

    @staticmethod
    def _structural_similarity(a: BlueprintV2, b: BlueprintV2) -> float:
        """Structural similarity using raw metric ratios."""
        scores: List[float] = []

        # Dimensions
        if a.width > 0 and b.width > 0:
            scores.append(min(a.width, b.width) / max(a.width, b.width))
        if a.height > 0 and b.height > 0:
            scores.append(min(a.height, b.height) / max(a.height, b.height))

        # Structural counts
        for attr in [
            "regions",
            "roads",
            "landmarks",
            "districts",
            "spawn_clusters",
            "waypoints",
        ]:
            va = getattr(a, attr, 0)
            vb = getattr(b, attr, 0)
            if va > 0 and vb > 0:
                scores.append(min(va, vb) / max(va, vb))
            elif va == 0 and vb == 0:
                scores.append(1.0)
            else:
                scores.append(0.0)

        # Type match
        scores.append(1.0 if a.type == b.type else 0.0)

        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    @staticmethod
    def _tag_overlap(a: BlueprintV2, b: BlueprintV2) -> float:
        """Jaccard similarity over tags."""
        tags_a = set(t.lower() for t in a.tags)
        tags_b = set(t.lower() for t in b.tags)

        # Also include type
        if a.type:
            tags_a.add(a.type.lower())
        if b.type:
            tags_b.add(b.type.lower())

        if not tags_a or not tags_b:
            return 0.0

        intersection = tags_a & tags_b
        union = tags_a | tags_b
        return len(intersection) / len(union)

    # ------------------------------------------------------------------
    # Pattern comparison helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cosine_with_pattern(bp: BlueprintV2, pattern: PatternV2) -> float:
        """Cosine similarity between blueprint and pattern vectors."""
        bp_vec = SimilarityEngineV2._to_vector(bp)
        pat_vec = pattern.feature_vector[: len(bp_vec)]  # Align lengths

        # Pad pattern vector if needed
        if len(pat_vec) < len(bp_vec):
            pat_vec = pat_vec + [0.0] * (len(bp_vec) - len(pat_vec))

        dot = sum(b * p for b, p in zip(bp_vec, pat_vec))
        norm_bp = math.sqrt(sum(v * v for v in bp_vec))
        norm_pat = math.sqrt(sum(v * v for v in pat_vec))

        if norm_bp == 0.0 or norm_pat == 0.0:
            return 0.0
        return dot / (norm_bp * norm_pat)

    @staticmethod
    def _pattern_structural_similarity(bp: BlueprintV2, pattern: PatternV2) -> float:
        """Structural similarity between blueprint and pattern dimensions."""
        scores: List[float] = []

        # Width/height similarity
        if pattern.width > 0 and bp.width > 0:
            w_sim = min(pattern.width * 3, bp.width) / max(pattern.width * 3, bp.width)
            scores.append(w_sim)
        if pattern.height > 0 and bp.height > 0:
            h_sim = min(pattern.height * 3, bp.height) / max(
                pattern.height * 3, bp.height
            )
            scores.append(h_sim)

        # Pattern elements vs blueprint regions
        if pattern.elements and bp.regions > 0:
            element_match = min(len(pattern.elements), bp.regions) / max(
                len(pattern.elements), bp.regions
            )
            scores.append(element_match)

        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    @staticmethod
    def _tag_overlap_with_pattern(bp: BlueprintV2, pattern: PatternV2) -> float:
        """Tag overlap between blueprint and pattern."""
        bp_tags = set(t.lower() for t in bp.tags)
        pat_tags = set(t.lower() for t in pattern.tags)

        if bp.type:
            bp_tags.add(bp.type.lower())

        if not bp_tags or not pat_tags:
            return 0.0

        intersection = bp_tags & pat_tags
        union = bp_tags | pat_tags
        return len(intersection) / len(union)
