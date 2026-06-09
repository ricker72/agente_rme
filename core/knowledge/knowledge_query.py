"""
KnowledgeQuery — parses free-text and structured queries.

Supports three query modes:
  - text query  : "boss rooms level 500"
  - structured  : entry_type=boss, level=300-500, biome=desert
  - filter      : by minimum score, biome, level range, etc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    EntryType,
    KnowledgeEntry,
    KnowledgeQueryResult,
    QueryMatch,
    hybrid_similarity,
)


# Map of free-text hints -> EntryType
_TYPE_HINTS: List[Tuple[List[str], EntryType]] = [
    (["city", "cities", "town", "village", "hub"], EntryType.CITY),
    (["hunt", "hunts", "spawn", "farm", "cave", "sewer"], EntryType.HUNT),
    (["boss", "boss room", "arena", "throne", "lair"], EntryType.BOSS_ROOM),
    (["raid", "inquisition", "ferumbras", "encounter"], EntryType.RAID),
    (["quest", "mission", "task"], EntryType.QUEST),
    (["region", "zone", "area", "continent", "island"], EntryType.REGION),
    (["biome", "climate", "wilderness", "terrain"], EntryType.BIOME),
    (["waypoint", "tp", "teleport"], EntryType.WAYPOINT),
    (["spawn", "monster spawn"], EntryType.SPAWN),
    (["dungeon", "crypt", "tomb", "pyramid"], EntryType.DUNGEON),
    (["npc"], EntryType.NPC),
    (["structure"], EntryType.STRUCTURE),
]

# Map of free-text hints -> biome
_BIOME_HINTS = (
    "desert", "jungle", "ice", "snow", "forest", "swamp", "cave",
    "fire", "roshamuul", "issavi", "yalahar", "venore", "thais",
    "ab'dendriel", "carlin", "ankrahmun", "darashia", "edron",
)

# Map of free-text hints -> difficulty
_DIFF_HINTS = {
    "trivial": "trivial", "easy": "easy",
    "medium": "medium", "hard": "hard", "extreme": "extreme",
}

# Map of free-text hints -> structural
_STRUCT_HINTS = {
    "circular": ("route", "circular"),
    "linear": ("route", "linear"),
    "branching": ("route", "branching"),
    "rectangular": ("shape", "rectangular"),
    "open": ("layout", "open"),
    "dense": ("layout", "dense"),
    "maze": ("layout", "maze"),
    "arena": ("shape", "circular"),
}


@dataclass
class ParsedQuery:
    """Structured representation of a free-text query."""

    raw: str
    cleaned: str
    entry_type: Optional[EntryType] = None
    biome: Optional[str] = None
    difficulty: Optional[str] = None
    min_level: Optional[int] = None
    max_level: Optional[int] = None
    attrs: Dict[str, Any] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)


def parse_query(query: str) -> ParsedQuery:
    """Parse a free-text query into a structured form."""
    q = (query or "").strip()
    if not q:
        return ParsedQuery(raw=query or "", cleaned="", keywords=[])
    lower = q.lower()
    # Strip level phrases
    min_level = None
    max_level = None
    lvl_range = re.search(r"level[s]?\s+(\d+)\s*[-to]+\s*(\d+)", lower)
    if lvl_range:
        min_level = int(lvl_range.group(1))
        max_level = int(lvl_range.group(2))
    else:
        lvl_min = re.search(r"(?:min|>=|over|above)\s*(\d+)", lower)
        lvl_max = re.search(r"(?:max|<=|under|below)\s*(\d+)", lower)
        lvl_eq = re.search(r"level[s]?\s+(\d+)", lower)
        if lvl_eq:
            v = int(lvl_eq.group(1))
            min_level = v
            max_level = v
        if lvl_min:
            min_level = int(lvl_min.group(1))
        if lvl_max:
            max_level = int(lvl_max.group(1))

    # Detect type
    entry_type: Optional[EntryType] = None
    for hints, et in _TYPE_HINTS:
        for h in hints:
            if re.search(r"\b" + re.escape(h) + r"s?\b", lower):
                entry_type = et
                break
        if entry_type:
            break

    # Detect biome
    biome = None
    for b in _BIOME_HINTS:
        if b in lower:
            biome = b
            break

    # Detect difficulty
    difficulty = None
    for k, v in _DIFF_HINTS.items():
        if re.search(r"\b" + k + r"\b", lower):
            difficulty = v
            break

    # Detect structural hints
    attrs: Dict[str, Any] = {}
    for k, (kk, vv) in _STRUCT_HINTS.items():
        if re.search(r"\b" + re.escape(k) + r"\b", lower):
            attrs[kk] = vv

    # Keywords: remove type / biome words
    keywords: List[str] = []
    for tok in re.findall(r"[A-Za-z][A-Za-z0-9_]+", lower):
        if tok in ("level", "levels", "with", "and", "the", "a", "an",
                   "of", "in", "to", "for", "biome", "route", "routes",
                   "rooms", "room"):
            continue
        keywords.append(tok)
    return ParsedQuery(
        raw=query,
        cleaned=lower,
        entry_type=entry_type,
        biome=biome,
        difficulty=difficulty,
        min_level=min_level,
        max_level=max_level,
        attrs=attrs,
        keywords=keywords,
    )


class KnowledgeQuery:
    """
    Executes a query against an index and returns a `KnowledgeQueryResult`.

    The query engine supports three modes:
      - text(query)    — free-text, falls back to similarity search.
      - structured(**) — explicit entry_type + filters.
      - filter(func)   — python callable filter on entries.
    """

    def __init__(self, index) -> None:
        self.index = index

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def text(self, query: str, k: int = 5) -> KnowledgeQueryResult:
        """Execute a free-text query."""
        from .models import KnowledgeQueryResult, QueryMatch
        import time

        t0 = time.perf_counter()
        parsed = parse_query(query)
        result = KnowledgeQueryResult(query=query)
        if not parsed.cleaned:
            return result
        indexer = None
        if parsed.entry_type is not None:
            indexer = self.index.indexer_for(parsed.entry_type)
        # A search with an entirely-unknown token should return 0.
        # Detect this by checking that the query has at least one
        # alpha token; if not, return empty.
        if not any(c.isalpha() for c in parsed.cleaned):
            result.took_ms = (time.perf_counter() - t0) * 1000.0
            return result

        if indexer is not None and len(indexer) > 0:
            search_attrs = dict(parsed.attrs)
            if parsed.biome:
                search_attrs["biome"] = parsed.biome
            scored = indexer.search(
                parsed.cleaned,
                k=k,
                attrs=search_attrs,
            )
            for e, score in scored:
                if not self._matches_filters(e, parsed):
                    continue
                # Discard pure-zero matches so "no match" queries return empty.
                if score <= 0.0:
                    continue
                result.add(QueryMatch(
                    entry=e, score=float(score),
                    match_type="text",
                    explanation=self._explain(parsed, e),
                ))
        else:
            # Search across all indexers
            for et, idx in self.index._by_type.items():  # noqa: SLF001
                if idx is None or len(idx) == 0:
                    continue
                scored = idx.search(parsed.cleaned, k=k,
                                    attrs=parsed.attrs)
                for e, score in scored:
                    if e.entry_type != et:
                        continue
                    if not self._matches_filters(e, parsed):
                        continue
                    if score <= 0.0:
                        continue
                    result.add(QueryMatch(
                        entry=e, score=float(score),
                        match_type="text",
                        explanation=self._explain(parsed, e),
                    ))
        result.sort()
        result.took_ms = (time.perf_counter() - t0) * 1000.0
        return result

    def structured(
        self,
        entry_type: EntryType,
        k: int = 10,
        min_level: Optional[int] = None,
        max_level: Optional[int] = None,
        biome: Optional[str] = None,
        attrs: Optional[Dict[str, Any]] = None,
    ) -> KnowledgeQueryResult:
        """Execute a structured query against one entry type."""
        import time

        t0 = time.perf_counter()
        result = KnowledgeQueryResult(query=f"structured:{entry_type.value}")
        indexer = self.index.indexer_for(entry_type)
        if indexer is None:
            return result
        q_attrs: Dict[str, Any] = dict(attrs or {})
        if biome:
            q_attrs["biome"] = biome
        # Use a generic name to force a similarity pass
        for entry in indexer.entries:
            if not self._passes_level(entry, min_level, max_level):
                continue
            if biome and (entry.biome or "").lower() != biome.lower():
                continue
            score = hybrid_similarity(
                f"{entry_type.value} {biome or ''} {min_level or ''}",
                entry.signature or entry.name,
                q_attrs, entry.attributes,
            )
            # Substring match boost
            if biome and biome.lower() in (entry.signature or "").lower():
                score = min(1.0, score + 0.1)
            if min_level is not None and entry.max_level < min_level:
                score *= 0.5
            if max_level is not None and entry.min_level > max_level:
                score *= 0.5
            result.add(QueryMatch(
                entry=entry, score=float(score),
                match_type="filter",
                explanation=f"entry_type={entry_type.value}",
            ))
        result.sort()
        result.matches = result.matches[:k]
        result.total = len(result.matches)
        result.took_ms = (time.perf_counter() - t0) * 1000.0
        return result

    def filter(
        self,
        entry_type: EntryType,
        predicate,
        k: int = 100,
    ) -> KnowledgeQueryResult:
        """Filter entries by an arbitrary python callable."""
        import time

        t0 = time.perf_counter()
        result = KnowledgeQueryResult(query=f"filter:{entry_type.value}")
        indexer = self.index.indexer_for(entry_type)
        if indexer is None:
            return result
        for entry in indexer.entries:
            try:
                if predicate(entry):
                    result.add(QueryMatch(
                        entry=entry, score=1.0,
                        match_type="filter",
                        explanation="user predicate",
                    ))
            except Exception:
                continue
        result.matches = result.matches[:k]
        result.total = len(result.matches)
        result.took_ms = (time.perf_counter() - t0) * 1000.0
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _passes_level(
        self,
        entry: KnowledgeEntry,
        min_level: Optional[int],
        max_level: Optional[int],
    ) -> bool:
        if min_level is not None and entry.max_level < min_level:
            return False
        if max_level is not None and entry.min_level > max_level:
            return False
        return True

    def _matches_filters(
        self,
        entry: KnowledgeEntry,
        parsed: ParsedQuery,
    ) -> bool:
        if not self._passes_level(entry, parsed.min_level, parsed.max_level):
            return False
        if parsed.biome and parsed.biome not in (entry.biome or "").lower() \
                and parsed.biome not in (entry.signature or "").lower():
            return False
        if parsed.difficulty and \
                (entry.attributes or {}).get("difficulty", "").lower() != parsed.difficulty:
            # Allow non-strict — still keep results
            pass
        for k, v in parsed.attrs.items():
            if (entry.attributes or {}).get(k) != v and \
                    v not in (entry.signature or "").lower():
                return False
        return True

    def _explain(self, parsed: ParsedQuery, entry: KnowledgeEntry) -> str:
        parts: List[str] = []
        if parsed.entry_type:
            parts.append(f"type={parsed.entry_type.value}")
        if parsed.biome:
            parts.append(f"biome={parsed.biome}")
        if parsed.difficulty:
            parts.append(f"difficulty={parsed.difficulty}")
        if parsed.min_level is not None or parsed.max_level is not None:
            parts.append(f"level={parsed.min_level}-{parsed.max_level}")
        for k, v in parsed.attrs.items():
            parts.append(f"{k}={v}")
        return ", ".join(parts) or "similarity"
