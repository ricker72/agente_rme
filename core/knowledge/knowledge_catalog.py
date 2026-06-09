"""
KnowledgeCatalog — high-level metadata about the dataset.

The catalog describes the dataset in human-readable form (counts, sources,
themes, top entries per category) and is exported to `knowledge_catalog.json`.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .models import EntryType, KnowledgeDataset, KnowledgeEntry


def _entry_summary(entry: KnowledgeEntry) -> Dict[str, Any]:
    return {
        "name": entry.name,
        "id": entry.id,
        "source": entry.source,
        "biome": entry.biome,
        "min_level": entry.min_level,
        "max_level": entry.max_level,
        "tags": list(entry.tags),
    }


@dataclass
class KnowledgeCatalog:
    """In-memory description of the dataset."""

    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_entries: int = 0
    sources: List[str] = field(default_factory=list)
    counts_by_type: Dict[str, int] = field(default_factory=dict)
    counts_by_biome: Dict[str, int] = field(default_factory=dict)
    top_themes: List[Dict[str, Any]] = field(default_factory=list)
    top_cities: List[Dict[str, Any]] = field(default_factory=list)
    top_hunts: List[Dict[str, Any]] = field(default_factory=list)
    top_boss_rooms: List[Dict[str, Any]] = field(default_factory=list)
    top_quests: List[Dict[str, Any]] = field(default_factory=list)
    top_regions: List[Dict[str, Any]] = field(default_factory=list)
    top_biomes: List[Dict[str, Any]] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    @classmethod
    def build(
        cls,
        dataset: KnowledgeDataset,
        top_n: int = 5,
    ) -> "KnowledgeCatalog":
        """Build a catalog from a dataset."""
        cat = cls()
        cat.total_entries = dataset.total()
        cat.sources = list(dataset.sources)
        cat.counts_by_type = dataset.counts()

        biome_counter: Counter = Counter()
        for entry in dataset.all_entries():
            if entry.biome and entry.biome != "generic":
                biome_counter[entry.biome] += 1
        cat.counts_by_biome = dict(biome_counter.most_common())

        def _top(bucket: List[KnowledgeEntry], n: int) -> List[Dict[str, Any]]:
            return [_entry_summary(e) for e in bucket[:n]]

        cat.top_cities = _top(dataset.cities, top_n)
        cat.top_hunts = _top(dataset.hunts, top_n)
        cat.top_boss_rooms = _top(dataset.boss_rooms, top_n)
        cat.top_quests = _top(dataset.quests, top_n)
        cat.top_regions = _top(dataset.regions, top_n)
        cat.top_biomes = _top(dataset.biomes, top_n)

        # top_themes — most common biomes / themes
        cat.top_themes = [
            {"name": name, "count": cnt}
            for name, cnt in biome_counter.most_common(top_n)
        ]
        return cat

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "created_at": self.created_at,
            "total_entries": self.total_entries,
            "sources": list(self.sources),
            "counts_by_type": dict(self.counts_by_type),
            "counts_by_biome": dict(self.counts_by_biome),
            "top_themes": list(self.top_themes),
            "top_cities": list(self.top_cities),
            "top_hunts": list(self.top_hunts),
            "top_boss_rooms": list(self.top_boss_rooms),
            "top_quests": list(self.top_quests),
            "top_regions": list(self.top_regions),
            "top_biomes": list(self.top_biomes),
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def write(self, path: str) -> str:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.to_json(), encoding="utf-8")
        return str(out)
