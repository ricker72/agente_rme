"""QuestIndexer — index quest entries by style, theme, difficulty."""

from __future__ import annotations

from ..models import EntryType
from .base_indexer import BaseIndexer


class QuestIndexer(BaseIndexer):
    """Indexer specialized for quests."""

    def __init__(self) -> None:
        super().__init__(name="quest")

    def by_difficulty(self, difficulty: str) -> list:
        d = difficulty.lower()
        return [e for e in self.entries
                if e.entry_type == EntryType.QUEST
                and (e.attributes or {}).get("difficulty", "").lower() == d]
