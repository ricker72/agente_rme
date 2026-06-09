"""
KnowledgeRanker — combines multiple quality signals into a single rank.

Inputs:
  - quality_score   (0..100)
  - critic_score    (0..100)
  - playtest_score  (0..100)
  - reuse_score     (0..100)
  - similarity      (0..1)
  - level_fit       (0..1) — how well the entry matches a target level

Output: a final score in [0, 1].
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .models import KnowledgeEntry


@dataclass
class RankerWeights:
    """Default weights for the four quality signals + similarity + level fit."""

    quality: float = 0.15
    critic: float = 0.30
    playtest: float = 0.25
    reuse: float = 0.10
    similarity: float = 0.15
    level_fit: float = 0.05

    def total(self) -> float:
        return (
            self.quality
            + self.critic
            + self.playtest
            + self.reuse
            + self.similarity
            + self.level_fit
        )


class KnowledgeRanker:
    """
    Compute a final ranking score in [0, 1] for an entry.

    Quality / critic / playtest / reuse scores are normalized from 0..100
    to 0..1. Similarity and level fit are already in [0, 1].
    """

    def __init__(self, weights: Optional[RankerWeights] = None) -> None:
        self.weights = weights or RankerWeights()

    def _normalize(self, value: Any) -> float:
        try:
            v = float(value)
        except (TypeError, ValueError):
            return 0.0
        if v < 0:
            return 0.0
        if v > 100.0:
            return 1.0
        if v > 1.0:
            # Assume 0..100
            return v / 100.0
        return v

    def level_fit(
        self,
        entry: KnowledgeEntry,
        target_min: Optional[int] = None,
        target_max: Optional[int] = None,
    ) -> float:
        """Return 1.0 if entry is within [target_min, target_max], else lower."""
        if target_min is None and target_max is None:
            return 1.0
        lo = target_min if target_min is not None else 0
        hi = target_max if target_max is not None else 9999
        if entry.max_level < lo or entry.min_level > hi:
            return 0.0
        # Partial overlap is acceptable
        overlap_lo = max(entry.min_level, lo)
        overlap_hi = min(entry.max_level, hi)
        overlap = max(0, overlap_hi - overlap_lo)
        span = max(1, entry.max_level - entry.min_level)
        return min(1.0, overlap / span + 0.25)

    def rank(
        self,
        entry: KnowledgeEntry,
        *,
        similarity: float = 0.0,
        target_min_level: Optional[int] = None,
        target_max_level: Optional[int] = None,
    ) -> float:
        """
        Return a final score in [0, 1].
        """
        w = self.weights
        total = w.total() or 1.0
        quality = self._normalize(entry.quality_score)
        critic = self._normalize(entry.critic_score)
        playtest = self._normalize(entry.playtest_score)
        reuse = self._normalize(entry.reuse_score)
        sim = max(0.0, min(1.0, float(similarity)))
        lf = self.level_fit(entry, target_min_level, target_max_level)
        score = (
            w.quality * quality
            + w.critic * critic
            + w.playtest * playtest
            + w.reuse * reuse
            + w.similarity * sim
            + w.level_fit * lf
        ) / total
        return max(0.0, min(1.0, score))

    def rank_many(
        self,
        entries_with_scores: list,
        *,
        target_min_level: Optional[int] = None,
        target_max_level: Optional[int] = None,
    ) -> list:
        """
        Rank a list of (entry, similarity) tuples.

        Returns the list sorted by final score (desc).
        """
        out = []
        for entry, sim in entries_with_scores:
            final = self.rank(
                entry,
                similarity=sim,
                target_min_level=target_min_level,
                target_max_level=target_max_level,
            )
            out.append((entry, sim, final))
        out.sort(key=lambda t: t[2], reverse=True)
        return out
