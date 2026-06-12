"""BossIndexer — index boss rooms by arena_type / shape / level."""

from __future__ import annotations

from typing import List, Tuple

from ..models import KnowledgeEntry, EntryType
from .base_indexer import BaseIndexer


class BossIndexer(BaseIndexer):
    """Indexer specialized for boss rooms."""

    def __init__(self) -> None:
        super().__init__(name="boss")

    def find_circular_arena(self, k: int = 10) -> List[Tuple[KnowledgeEntry, float]]:
        """Return boss rooms with a circular arena."""
        out: List[Tuple[KnowledgeEntry, float]] = []
        for e in self.entries:
            if e.entry_type != EntryType.BOSS_ROOM:
                continue
            attrs = e.attributes or {}
            score = 0.0
            if attrs.get("shape") == "circular":
                score = max(score, 0.9)
            if attrs.get("arena_type") in ("throne", "coliseum", "circular"):
                score = max(score, 0.85)
            if (
                "arena" in (e.signature or "").lower()
                and "circular" in (e.signature or "").lower()
            ):
                score = max(score, 0.8)
            if score > 0:
                out.append((e, score))
        out.sort(key=lambda t: t[1], reverse=True)
        return out[:k]
