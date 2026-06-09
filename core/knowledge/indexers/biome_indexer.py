"""BiomeIndexer — index biomes for fast theme lookup."""

from __future__ import annotations

from typing import List

from ..models import EntryType, KnowledgeEntry
from .base_indexer import BaseIndexer


class BiomeIndexer(BaseIndexer):
    """Indexer specialized for biomes."""

    def __init__(self) -> None:
        super().__init__(name="biome")

    def by_climate(self, climate: str) -> List[KnowledgeEntry]:
        c = climate.lower()
        return [e for e in self.entries
                if e.entry_type == EntryType.BIOME
                and (e.attributes or {}).get("climate", "").lower() == c]

    def desert(self) -> List[KnowledgeEntry]:
        return [e for e in self.entries
                if e.entry_type == EntryType.BIOME and "desert" in (e.biome or "").lower()]
