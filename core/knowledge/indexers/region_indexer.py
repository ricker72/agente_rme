"""RegionIndexer — index generic region / dungeon / structure entries."""

from __future__ import annotations

from typing import List

from ..models import EntryType, KnowledgeEntry
from .base_indexer import BaseIndexer


class RegionIndexer(BaseIndexer):
    """Indexer for regions, dungeons and structures."""

    def __init__(self) -> None:
        super().__init__(name="region")

    def dungeons(self) -> List[KnowledgeEntry]:
        return [e for e in self.entries if e.entry_type == EntryType.DUNGEON]

    def structures(self) -> List[KnowledgeEntry]:
        return [e for e in self.entries if e.entry_type == EntryType.STRUCTURE]

    def regions(self) -> List[KnowledgeEntry]:
        return [e for e in self.entries if e.entry_type == EntryType.REGION]

    def by_level(self, min_level: int, max_level: int) -> List[KnowledgeEntry]:
        return [
            e
            for e in self.entries
            if e.max_level >= min_level and e.min_level <= max_level
        ]
