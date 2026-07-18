"""HuntIndexer — index hunt entries with biome / route / circular hints."""

from __future__ import annotations

from typing import List, Tuple

from ..models import KnowledgeEntry, EntryType
from .base_indexer import BaseIndexer


class HuntIndexer(BaseIndexer):
    """Indexer specialized for hunts (circular, route, monsters)."""

    def __init__(self) -> None:
        super().__init__(name="hunt")

    def find_circular(self, k: int = 10) -> List[Tuple[KnowledgeEntry, float]]:
        """Return hunts whose attributes indicate a circular route."""
        out: List[Tuple[KnowledgeEntry, float]] = []
        for e in self.entries:
            if e.entry_type != EntryType.HUNT:
                continue
            attrs = e.attributes or {}
            score = 0.0
            if attrs.get("circular"):
                score = max(score, 0.9)
            if attrs.get("route") == "circular":
                score = max(score, 0.8)
            if "circular" in (e.signature or "").lower():
                score = max(score, 0.7)
            if score > 0:
                out.append((e, score))
        out.sort(key=lambda t: t[1], reverse=True)
        return out[:k]

    def by_level(self, min_level: int, max_level: int) -> List[KnowledgeEntry]:
        return [
            e
            for e in self.entries
            if e.entry_type == EntryType.HUNT
            and e.max_level >= min_level
            and e.min_level <= max_level
        ]
