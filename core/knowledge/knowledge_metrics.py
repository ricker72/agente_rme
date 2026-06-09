"""
KnowledgeMetrics — coverage and quality metrics for a dataset.

Exposed as `knowledge_metrics.json`.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import EntryType, KnowledgeDataset, KnowledgeEntry


def _safe_avg(values: List[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


@dataclass
class KnowledgeMetrics:
    """Aggregated metrics for a knowledge dataset."""

    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_entries: int = 0
    entries_by_type: Dict[str, int] = field(default_factory=dict)
    entries_by_biome: Dict[str, int] = field(default_factory=dict)
    avg_quality_score: float = 0.0
    avg_critic_score: float = 0.0
    avg_playtest_score: float = 0.0
    avg_reuse_score: float = 0.0
    coverage_pct: float = 0.0
    source_count: int = 0
    level_coverage: Dict[str, int] = field(default_factory=dict)
    circular_hunts: int = 0
    circular_boss_rooms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "created_at": self.created_at,
            "total_entries": self.total_entries,
            "entries_by_type": dict(self.entries_by_type),
            "entries_by_biome": dict(self.entries_by_biome),
            "avg_quality_score": self.avg_quality_score,
            "avg_critic_score": self.avg_critic_score,
            "avg_playtest_score": self.avg_playtest_score,
            "avg_reuse_score": self.avg_reuse_score,
            "coverage_pct": self.coverage_pct,
            "source_count": self.source_count,
            "level_coverage": dict(self.level_coverage),
            "circular_hunts": self.circular_hunts,
            "circular_boss_rooms": self.circular_boss_rooms,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def write(self, path: str) -> str:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(self.to_json(), encoding="utf-8")
        return str(out)


def _bucket_level(min_lv: int, max_lv: int) -> str:
    if min_lv >= 600 or max_lv >= 600:
        return "600+"
    if min_lv >= 400 or max_lv >= 400:
        return "400-600"
    if min_lv >= 250 or max_lv >= 250:
        return "250-400"
    if min_lv >= 150 or max_lv >= 150:
        return "150-250"
    if min_lv >= 80 or max_lv >= 80:
        return "80-150"
    return "1-80"


def build_metrics(
    dataset: KnowledgeDataset,
    *,
    expected_types: Optional[List[EntryType]] = None,
) -> KnowledgeMetrics:
    """Compute metrics from a dataset."""
    metrics = KnowledgeMetrics()
    metrics.total_entries = dataset.total()
    metrics.source_count = len(dataset.sources)
    metrics.entries_by_type = dataset.counts()

    if expected_types is None:
        expected_types = [
            EntryType.CITY, EntryType.HUNT, EntryType.BOSS_ROOM,
            EntryType.QUEST, EntryType.RAID, EntryType.REGION,
            EntryType.BIOME,
        ]
    # Map from JSON bucket keys (plural) to EntryType (singular)
    _BUCKET_TO_TYPE = {
        "cities": EntryType.CITY,
        "hunts": EntryType.HUNT,
        "boss_rooms": EntryType.BOSS_ROOM,
        "raids": EntryType.RAID,
        "quests": EntryType.QUEST,
        "regions": EntryType.REGION,
        "biomes": EntryType.BIOME,
        "spawns": EntryType.SPAWN,
        "waypoints": EntryType.WAYPOINT,
    }
    present = {_BUCKET_TO_TYPE[k] for k, v in metrics.entries_by_type.items()
               if v > 0 and k in _BUCKET_TO_TYPE}
    coverage = len(present & set(expected_types)) / max(1, len(expected_types))
    metrics.coverage_pct = round(coverage * 100.0, 2)

    biome_counter: Counter = Counter()
    qualities: List[float] = []
    critics: List[float] = []
    playtests: List[float] = []
    reuses: List[float] = []
    levels: Counter = Counter()
    circular_hunts = 0
    circular_boss = 0

    for entry in dataset.all_entries():
        if entry.biome and entry.biome != "generic":
            biome_counter[entry.biome] += 1
        qualities.append(entry.quality_score)
        critics.append(entry.critic_score)
        playtests.append(entry.playtest_score)
        reuses.append(entry.reuse_score)
        levels[_bucket_level(entry.min_level, entry.max_level)] += 1
        if entry.entry_type == EntryType.HUNT and \
                (entry.attributes or {}).get("circular"):
            circular_hunts += 1
        if entry.entry_type == EntryType.BOSS_ROOM and \
                (entry.attributes or {}).get("shape") == "circular":
            circular_boss += 1

    metrics.entries_by_biome = dict(biome_counter.most_common())
    metrics.avg_quality_score = _safe_avg(qualities)
    metrics.avg_critic_score = _safe_avg(critics)
    metrics.avg_playtest_score = _safe_avg(playtests)
    metrics.avg_reuse_score = _safe_avg(reuses)
    metrics.level_coverage = dict(levels)
    metrics.circular_hunts = circular_hunts
    metrics.circular_boss_rooms = circular_boss
    return metrics
