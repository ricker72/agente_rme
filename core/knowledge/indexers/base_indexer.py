"""
BaseIndexer — in-memory inverted index for a single entity type.

Each indexer holds:
  - the entries it indexes;
  - a vector dict (TF-IDF) per entry;
  - a corpus-wide IDF dictionary;
  - a method `search(query, k)` that returns ranked matches.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Iterable, List, Tuple

from ..models import KnowledgeEntry, hybrid_similarity


class BaseIndexer:
    """
    In-memory index over a list of `KnowledgeEntry`.

    Uses a hybrid of cosine + jaccard + pattern similarity.
    """

    def __init__(self, name: str = "base") -> None:
        self.name = name
        self._entries: List[KnowledgeEntry] = []
        self._idf: Dict[str, float] = {}
        self._dirty: bool = True

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, entry: KnowledgeEntry) -> None:
        """Add an entry. If an entry with the same id exists, replace it."""
        for i, e in enumerate(self._entries):
            if e.id == entry.id:
                self._entries[i] = entry
                self._dirty = True
                return
        self._entries.append(entry)
        self._dirty = True

    def add_many(self, entries: Iterable[KnowledgeEntry]) -> int:
        n = 0
        for e in entries:
            self.add(e)
            n += 1
        return n

    def clear(self) -> None:
        self._entries = []
        self._idf = {}
        self._dirty = True

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    @property
    def entries(self) -> List[KnowledgeEntry]:
        return list(self._entries)

    def get(self, name: str) -> KnowledgeEntry | None:
        n = name.lower()
        for e in self._entries:
            if e.name.lower() == n:
                return e
        return None

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def _tokenize(self, entry: KnowledgeEntry) -> List[str]:
        """Tokenize an entry into a list of words for similarity."""
        if entry.signature:
            return entry.signature.split()
        # Fallback: derive a signature on the fly
        return (entry.name + " " + " ".join(entry.tags)).lower().split()

    def _ensure_idf(self) -> None:
        if not self._dirty:
            return
        docs: List[List[str]] = [self._tokenize(e) for e in self._entries]
        n = len(docs)
        df: Counter = Counter()
        for d in docs:
            for tok in set(d):
                df[tok] += 1
        import math
        idf: Dict[str, float] = {}
        for tok, dfreq in df.items():
            idf[tok] = math.log((n + 1.0) / (dfreq + 1.0)) + 1.0
        self._idf = idf
        self._dirty = False

    def _vector(self, entry: KnowledgeEntry) -> Dict[str, float]:
        toks = self._tokenize(entry)
        if not toks:
            return {}
        c = Counter(toks)
        total = float(len(toks))
        v: Dict[str, float] = {}
        for tok, cnt in c.items():
            tf = cnt / total
            idf = self._idf.get(tok, 1.0)
            v[tok] = tf * idf
        return v

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        k: int = 5,
        *,
        min_score: float = 0.0,
        attrs: Dict[str, Any] | None = None,
    ) -> List[Tuple[KnowledgeEntry, float]]:
        """
        Return up to `k` (entry, score) tuples ranked by hybrid similarity.

        `attrs` lets the caller pass attribute hints (e.g. level range) to
        blend into the pattern similarity.
        """
        self._ensure_idf()
        results: List[Tuple[KnowledgeEntry, float]] = []
        q_tokens = query.lower().split()
        q_attrs = dict(attrs or {})
        for e in self._entries:
            score = self._score(query, q_tokens, q_attrs, e)
            if score < min_score:
                continue
            results.append((e, score))
        results.sort(key=lambda t: t[1], reverse=True)
        return results[:k]

    def _score(
        self,
        query: str,
        q_tokens: List[str],
        q_attrs: Dict[str, Any],
        entry: KnowledgeEntry,
    ) -> float:
        # If a name match, give a strong baseline
        if query.strip().lower() == entry.name.strip().lower():
            return 1.0
        # Substring match -> partial boost
        if query.strip() and query.strip().lower() in entry.name.lower():
            return max(
                0.6,
                hybrid_similarity(
                    query, entry.signature or entry.name,
                    q_attrs, entry.attributes, idf=self._idf,
                ),
            )
        return hybrid_similarity(
            query, entry.signature or entry.name,
            q_attrs, entry.attributes, idf=self._idf,
        )
