"""
KnowledgeIndex — bundle of per-type indexers used by the engine.
"""

from __future__ import annotations

from typing import Dict, Optional

from .indexers import (
    BaseIndexer,
    CityIndexer,
    HuntIndexer,
    BossIndexer,
    QuestIndexer,
    RegionIndexer,
    BiomeIndexer,
)
from .models import EntryType, KnowledgeEntry


class KnowledgeIndex:
    """
    Holds the per-type indexers and dispatches operations to them.

    The indexers are kept in sync with a `KnowledgeDataset` (the source of
    truth) by calling `sync(dataset)`.
    """

    def __init__(self) -> None:
        self.city = CityIndexer()
        self.hunt = HuntIndexer()
        self.boss = BossIndexer()
        self.quest = QuestIndexer()
        self.region = RegionIndexer()
        self.biome = BiomeIndexer()
        # Dispatch table
        self._by_type: Dict[EntryType, BaseIndexer] = {
            EntryType.CITY: self.city,
            EntryType.HUNT: self.hunt,
            EntryType.BOSS_ROOM: self.boss,
            EntryType.QUEST: self.quest,
            EntryType.REGION: self.region,
            EntryType.STRUCTURE: self.region,
            EntryType.DUNGEON: self.region,
            EntryType.BIOME: self.biome,
            EntryType.RAID: self.region,
            EntryType.SPAWN: self.region,
            EntryType.WAYPOINT: self.region,
            EntryType.NPC: self.city,
        }

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    def sync(self, dataset) -> None:
        """Rebuild all indexers from a KnowledgeDataset."""
        for indexer in self._by_type.values():
            indexer.clear()
        for entry in dataset.all_entries():
            indexer = self._by_type.get(entry.entry_type)
            if indexer is not None:
                indexer.add(entry)

    def add(self, entry: KnowledgeEntry) -> None:
        indexer = self._by_type.get(entry.entry_type)
        if indexer is not None:
            indexer.add(entry)

    def indexer_for(self, entry_type: EntryType) -> Optional[BaseIndexer]:
        return self._by_type.get(entry_type)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, int]:
        return {
            "cities": len(self.city),
            "hunts": len(self.hunt),
            "boss_rooms": len(self.boss),
            "quests": len(self.quest),
            "regions": len(self.region),
            "biomes": len(self.biome),
            "total": sum(len(i) for i in self._by_type.values()),
        }
