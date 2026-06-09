"""
KnowledgeDataset — the on-disk / in-memory dataset produced by DatasetBuilder.

Holds every catalogued entry organized by type. Provides serialization
to/from the `knowledge_dataset.json` format.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .knowledge_entry import EntryType, KnowledgeEntry


@dataclass
class KnowledgeDataset:
    """
    Aggregated knowledge dataset.

    Stores entries grouped by type. The schema matches the requested
    `knowledge_dataset.json` shape:

        {
            "cities": [...],
            "hunts": [...],
            "boss_rooms": [...],
            "raids": [...],
            "quests": [...],
            "regions": [...],
            "biomes": [...],
            "spawns": [...],
            "waypoints": [...]
        }
    """

    cities: List[KnowledgeEntry] = field(default_factory=list)
    hunts: List[KnowledgeEntry] = field(default_factory=list)
    boss_rooms: List[KnowledgeEntry] = field(default_factory=list)
    raids: List[KnowledgeEntry] = field(default_factory=list)
    quests: List[KnowledgeEntry] = field(default_factory=list)
    regions: List[KnowledgeEntry] = field(default_factory=list)
    biomes: List[KnowledgeEntry] = field(default_factory=list)
    spawns: List[KnowledgeEntry] = field(default_factory=list)
    waypoints: List[KnowledgeEntry] = field(default_factory=list)

    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    sources: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def add(self, entry: KnowledgeEntry) -> None:
        """Append an entry to the correct type bucket (deduplicated by id)."""
        bucket = self._bucket_for(entry.entry_type)
        if any(e.id == entry.id for e in bucket):
            return
        bucket.append(entry)
        if entry.source and entry.source not in self.sources:
            self.sources.append(entry.source)

    def add_many(self, entries: Iterable[KnowledgeEntry]) -> int:
        """Add many entries; returns the number of new entries added."""
        n = 0
        for e in entries:
            before = self.total()
            self.add(e)
            after = self.total()
            if after > before:
                n += 1
        return n

    def remove(self, entry_id: str) -> bool:
        """Remove an entry by id from every bucket. Returns True if found."""
        for bucket in self._all_buckets():
            for i, e in enumerate(bucket):
                if e.id == entry_id:
                    bucket.pop(i)
                    return True
        return False

    def clear(self) -> None:
        for bucket in self._all_buckets():
            bucket.clear()
        self.sources.clear()

    def all_entries(self) -> List[KnowledgeEntry]:
        out: List[KnowledgeEntry] = []
        for bucket in self._all_buckets():
            out.extend(bucket)
        return out

    def total(self) -> int:
        return sum(len(b) for b in self._all_buckets())

    def by_type(self, entry_type: EntryType) -> List[KnowledgeEntry]:
        return list(self._bucket_for(entry_type))

    def by_id(self, entry_id: str) -> Optional[KnowledgeEntry]:
        for bucket in self._all_buckets():
            for e in bucket:
                if e.id == entry_id:
                    return e
        return None

    def by_name(self, name: str) -> Optional[KnowledgeEntry]:
        needle = name.lower()
        for bucket in self._all_buckets():
            for e in bucket:
                if e.name.lower() == needle:
                    return e
        return None

    # ------------------------------------------------------------------
    # Aggregation helpers
    # ------------------------------------------------------------------

    def counts(self) -> Dict[str, int]:
        return {
            "cities": len(self.cities),
            "hunts": len(self.hunts),
            "boss_rooms": len(self.boss_rooms),
            "raids": len(self.raids),
            "quests": len(self.quests),
            "regions": len(self.regions),
            "biomes": len(self.biomes),
            "spawns": len(self.spawns),
            "waypoints": len(self.waypoints),
        }

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cities": [e.to_dict() for e in self.cities],
            "hunts": [e.to_dict() for e in self.hunts],
            "boss_rooms": [e.to_dict() for e in self.boss_rooms],
            "raids": [e.to_dict() for e in self.raids],
            "quests": [e.to_dict() for e in self.quests],
            "regions": [e.to_dict() for e in self.regions],
            "biomes": [e.to_dict() for e in self.biomes],
            "spawns": [e.to_dict() for e in self.spawns],
            "waypoints": [e.to_dict() for e in self.waypoints],
            "_meta": {
                "created_at": self.created_at,
                "total_entries": self.total(),
                "sources": list(self.sources),
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def write(self, path: str) -> str:
        """Write the dataset to disk as JSON; returns the path written."""
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.to_json(), encoding="utf-8")
        return str(out)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeDataset":
        ds = cls()
        ds.cities = [KnowledgeEntry.from_dict(d) for d in data.get("cities", []) or []]
        ds.hunts = [KnowledgeEntry.from_dict(d) for d in data.get("hunts", []) or []]
        ds.boss_rooms = [KnowledgeEntry.from_dict(d) for d in data.get("boss_rooms", []) or []]
        ds.raids = [KnowledgeEntry.from_dict(d) for d in data.get("raids", []) or []]
        ds.quests = [KnowledgeEntry.from_dict(d) for d in data.get("quests", []) or []]
        ds.regions = [KnowledgeEntry.from_dict(d) for d in data.get("regions", []) or []]
        ds.biomes = [KnowledgeEntry.from_dict(d) for d in data.get("biomes", []) or []]
        ds.spawns = [KnowledgeEntry.from_dict(d) for d in data.get("spawns", []) or []]
        ds.waypoints = [KnowledgeEntry.from_dict(d) for d in data.get("waypoints", []) or []]
        meta = data.get("_meta", {}) or {}
        ds.created_at = meta.get("created_at", ds.created_at)
        ds.sources = list(meta.get("sources", []) or [])
        return ds

    @classmethod
    def read(cls, path: str) -> "KnowledgeDataset":
        """Read a dataset from a JSON file."""
        p = Path(path)
        if not p.exists():
            return cls()
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _bucket_for(self, entry_type: EntryType) -> List[KnowledgeEntry]:
        return {
            EntryType.CITY: self.cities,
            EntryType.HUNT: self.hunts,
            EntryType.BOSS_ROOM: self.boss_rooms,
            EntryType.RAID: self.raids,
            EntryType.QUEST: self.quests,
            EntryType.REGION: self.regions,
            EntryType.BIOME: self.biomes,
            EntryType.SPAWN: self.spawns,
            EntryType.WAYPOINT: self.waypoints,
            EntryType.STRUCTURE: self.regions,  # structures index as regions
            EntryType.DUNGEON: self.regions,    # dungeons index as regions
            EntryType.NPC: self.cities,         # npcs grouped with cities
        }[entry_type]

    def _all_buckets(self) -> List[List[KnowledgeEntry]]:
        return [
            self.cities,
            self.hunts,
            self.boss_rooms,
            self.raids,
            self.quests,
            self.regions,
            self.biomes,
            self.spawns,
            self.waypoints,
        ]
