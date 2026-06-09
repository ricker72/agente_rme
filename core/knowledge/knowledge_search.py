"""
KnowledgeSearch — high-level search that combines query + recommender.

This is the entry point used by the CLI (`rme knowledge search ...`) and
by the prompt-to-knowledge integration in the knowledge engine.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .knowledge_index import KnowledgeIndex
from .knowledge_query import KnowledgeQuery, parse_query
from .knowledge_ranker import KnowledgeRanker
from .models import (
    EntryType,
    KnowledgeEntry,
    KnowledgeQueryResult,
    QueryMatch,
    hybrid_similarity,
)


class KnowledgeSearch:
    """
    Unified search facade.

    Provides:
      - `search(query, k, entry_type=...)` — text or structured.
      - `find_similar(entry, k)`           — entry-to-entry similarity.
      - `find_by_text(text, k)`           — text-only similarity.
      - `find_by_attrs(...)`              — filter by attributes.
    """

    def __init__(
        self,
        index: KnowledgeIndex,
        ranker: Optional[KnowledgeRanker] = None,
    ) -> None:
        self.index = index
        self.ranker = ranker or KnowledgeRanker()
        self.query = KnowledgeQuery(index)

    def search(
        self,
        query: str,
        k: int = 5,
        *,
        entry_type: Optional[EntryType] = None,
        min_level: Optional[int] = None,
        max_level: Optional[int] = None,
        biome: Optional[str] = None,
    ) -> KnowledgeQueryResult:
        """Convenience wrapper around KnowledgeQuery.text/.structured."""
        if entry_type is not None:
            r = self.query.structured(
                entry_type=entry_type,
                k=k,
                min_level=min_level,
                max_level=max_level,
                biome=biome,
            )
        else:
            r = self.query.text(query, k=k)
            # Apply optional level filter on top
            if min_level is not None or max_level is not None:
                r.matches = [
                    m for m in r.matches
                    if self.query._passes_level(m.entry, min_level, max_level)
                ]
                r.total = len(r.matches)
        return r

    def find_similar(
        self,
        entry: KnowledgeEntry,
        k: int = 5,
    ) -> KnowledgeQueryResult:
        """Find entries similar to a given entry."""
        result = KnowledgeQueryResult(query=f"similar:{entry.name}")
        indexer = self.index.indexer_for(entry.entry_type)
        if indexer is None:
            return result
        # Build a search text from the entry's name + signature
        search_text = f"{entry.name} {entry.signature}".strip()
        scored = indexer.search(search_text, k=k + 1)
        for e, score in scored:
            if e.id == entry.id:
                continue
            result.add(QueryMatch(
                entry=e, score=float(score),
                match_type="similarity",
                explanation=f"hybrid={score:.3f}",
            ))
        result.sort()
        return result

    def find_by_text(
        self,
        text: str,
        k: int = 5,
    ) -> KnowledgeQueryResult:
        return self.query.text(text, k=k)

    def find_by_attrs(
        self,
        entry_type: EntryType,
        k: int = 10,
        **filters: Any,
    ) -> KnowledgeQueryResult:
        """Find entries of a given type matching a set of attribute filters."""
        return self.query.structured(entry_type=entry_type, k=k, **filters)
