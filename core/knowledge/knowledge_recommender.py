"""
KnowledgeRecommender — produces recommendations based on ranker scores.

Given a reference entry, recommend similar / related entries to consider
for reuse during generation.
"""

from __future__ import annotations

from typing import Optional

from .knowledge_index import KnowledgeIndex
from .knowledge_ranker import KnowledgeRanker, RankerWeights
from .models import EntryType, KnowledgeEntry, KnowledgeQueryResult, QueryMatch


class KnowledgeRecommender:
    """
    Recommends entries to reuse for a generation task.

    Example:
        rec = KnowledgeRecommender(index, ranker)
        top = rec.recommend_for_entry(hunt_entry, k=5)
    """

    def __init__(
        self,
        index: KnowledgeIndex,
        ranker: Optional[KnowledgeRanker] = None,
        weights: Optional[RankerWeights] = None,
    ) -> None:
        self.index = index
        self.ranker = ranker or KnowledgeRanker(weights=weights or RankerWeights())

    def recommend_for_entry(
        self,
        entry: KnowledgeEntry,
        k: int = 5,
        *,
        target_min_level: Optional[int] = None,
        target_max_level: Optional[int] = None,
    ) -> KnowledgeQueryResult:
        """Recommend similar entries to a given one."""
        result = KnowledgeQueryResult(query=f"recommend:{entry.name}")
        indexer = self.index.indexer_for(entry.entry_type)
        if indexer is None:
            return result
        # Use a richer search text that combines name + biome + signature
        search_text = " ".join(
            [
                entry.name,
                entry.biome or "",
                entry.signature or "",
            ]
        ).strip()
        scored = indexer.search(search_text, k=max(k + 5, 10))
        # Remove the entry itself
        candidates = [(e, s) for e, s in scored if e.id != entry.id]
        ranked = self.ranker.rank_many(
            candidates,
            target_min_level=target_min_level,
            target_max_level=target_max_level,
        )
        for e, sim, final in ranked[:k]:
            result.add(
                QueryMatch(
                    entry=e,
                    score=float(final),
                    match_type="similarity",
                    explanation=(
                        f"similarity={sim:.2f}, quality={e.quality_score:.0f}, "
                        f"critic={e.critic_score:.0f}, playtest={e.playtest_score:.0f}, "
                        f"reuse={e.reuse_score:.0f}"
                    ),
                )
            )
        result.sort()
        return result

    def recommend_by_text(
        self,
        query: str,
        k: int = 5,
        *,
        entry_type: Optional[EntryType] = None,
        target_min_level: Optional[int] = None,
        target_max_level: Optional[int] = None,
    ) -> KnowledgeQueryResult:
        """Recommend entries matching a free-text query, ranked."""
        from .knowledge_query import KnowledgeQuery

        q = KnowledgeQuery(self.index)
        if entry_type is not None:
            r = q.structured(
                entry_type=entry_type,
                k=k,
                min_level=target_min_level,
                max_level=target_max_level,
            )
        else:
            r = q.text(query, k=k)
        # Re-rank using the ranker
        ranked = self.ranker.rank_many(
            [(m.entry, m.score) for m in r.matches],
            target_min_level=target_min_level,
            target_max_level=target_max_level,
        )
        new = KnowledgeQueryResult(query=query)
        for e, sim, final in ranked[:k]:
            new.add(
                QueryMatch(
                    entry=e,
                    score=float(final),
                    match_type="ranked",
                    explanation=f"final={final:.2f}, sim={sim:.2f}",
                )
            )
        new.sort()
        return new
