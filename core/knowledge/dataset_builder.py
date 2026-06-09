"""
DatasetBuilder — orchestrates extraction + indexing + dataset generation.

It can process any combination of:
  - file paths (.otbm, .json);
  - WorldModel instances / dicts;
  - Blueprints (from the BlueprintExtractor pipeline);
  - Campaigns (from CampaignGenerator);
  - Playtest Reports;
  - Critic Reports.

It runs every registered extractor against every source, normalizes the
output, deduplicates, and writes a `KnowledgeDataset`.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

from .extractors import (
    BiomeExtractor,
    BossExtractor,
    CityExtractor,
    HuntExtractor,
    QuestExtractor,
    RaidExtractor,
    SpawnExtractor,
    StructureExtractor,
    WaypointExtractor,
)
from .knowledge_index import KnowledgeIndex
from .models import EntryType, KnowledgeDataset, KnowledgeEntry

logger = logging.getLogger(__name__)


@dataclass
class BuildStats:
    """Statistics for a single build run."""

    sources_processed: int = 0
    sources_failed: int = 0
    sources_skipped: int = 0
    entries_added: int = 0
    entries_dedup: int = 0
    per_extractor: Dict[str, int] = field(default_factory=dict)
    took_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sources_processed": self.sources_processed,
            "sources_failed": self.sources_failed,
            "sources_skipped": self.sources_skipped,
            "entries_added": self.entries_added,
            "entries_dedup": self.entries_dedup,
            "per_extractor": dict(self.per_extractor),
            "took_ms": round(self.took_ms, 2),
        }


class DatasetBuilder:
    """
    Build a `KnowledgeDataset` from a list of sources.

    Usage:
        builder = DatasetBuilder()
        dataset = builder.build_from_sources([
            "data/issavi.otbm",
            "data/blueprints/issavi_*.json",
            world_model,
            campaign,
        ])
        dataset.write("output/knowledge_dataset.json")
    """

    def __init__(
        self,
        *,
        extractors: Optional[Dict[str, Any]] = None,
        quality_default: float = 50.0,
        reuse_default: float = 30.0,
    ) -> None:
        if extractors is None:
            extractors = {
                "city": CityExtractor(),
                "hunt": HuntExtractor(),
                "boss": BossExtractor(),
                "raid": RaidExtractor(),
                "quest": QuestExtractor(),
                "spawn": SpawnExtractor(),
                "waypoint": WaypointExtractor(),
                "structure": StructureExtractor(),
                "biome": BiomeExtractor(),
            }
        self.extractors = extractors
        self.quality_default = quality_default
        self.reuse_default = reuse_default
        # Stats for the last build
        self.last_stats: BuildStats = BuildStats()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_from_sources(
        self,
        sources: Iterable[Any],
        dataset: Optional[KnowledgeDataset] = None,
    ) -> KnowledgeDataset:
        """Build (or extend) a dataset from a list of sources."""
        ds = dataset or KnowledgeDataset()
        stats = BuildStats()
        t0 = time.perf_counter()

        for src in sources:
            try:
                added = self._process_source(src, ds, stats)
                if added > 0:
                    stats.sources_processed += 1
                else:
                    stats.sources_skipped += 1
            except Exception as e:  # noqa: BLE001
                stats.sources_failed += 1
                logger.warning("Failed to process source %r: %s", src, e)

        stats.took_ms = (time.perf_counter() - t0) * 1000.0
        self.last_stats = stats
        return ds

    def build(
        self,
        sources: Iterable[Any],
        output_path: Optional[str] = None,
    ) -> KnowledgeDataset:
        """Build + write to JSON in one call."""
        ds = self.build_from_sources(sources)
        if output_path:
            ds.write(output_path)
        return ds

    def attach_scores(
        self,
        dataset: KnowledgeDataset,
        *,
        quality_report: Optional[Dict[str, float]] = None,
        critic_report: Optional[Dict[str, float]] = None,
        playtest_report: Optional[Dict[str, float]] = None,
        reuse_report: Optional[Dict[str, float]] = None,
    ) -> None:
        """
        Merge external score reports into a dataset's entries.

        Each report is `{entry_name: score_0_100}`.  If the entry exists,
        its `quality_score`, `critic_score`, `playtest_score` or
        `reuse_score` field is set.
        """
        for entry in dataset.all_entries():
            if quality_report and entry.name in quality_report:
                entry.quality_score = float(quality_report[entry.name])
            if critic_report and entry.name in critic_report:
                entry.critic_score = float(critic_report[entry.name])
            if playtest_report and entry.name in playtest_report:
                entry.playtest_score = float(playtest_report[entry.name])
            if reuse_report and entry.name in reuse_report:
                entry.reuse_score = float(reuse_report[entry.name])
        # Default scores for entries without one
        for entry in dataset.all_entries():
            if entry.quality_score == 0.0:
                entry.quality_score = self.quality_default
            if entry.reuse_score == 0.0:
                entry.reuse_score = self.reuse_default

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _process_source(
        self,
        source: Any,
        dataset: KnowledgeDataset,
        stats: BuildStats,
    ) -> int:
        """Run all extractors on a single source. Returns entries added."""
        label = self._label_of(source)
        before = dataset.total()
        for name, extractor in self.extractors.items():
            try:
                world = self._load_source(source, label)
                if world is None:
                    continue
                entries = extractor.extract(world, source=label)
                # Default scores
                for e in entries:
                    if e.quality_score == 0.0:
                        e.quality_score = self.quality_default
                    if e.reuse_score == 0.0:
                        e.reuse_score = self.reuse_default
                added = dataset.add_many(entries)
                stats.per_extractor[name] = stats.per_extractor.get(name, 0) + added
            except Exception as e:  # noqa: BLE001
                logger.warning("Extractor %s failed for %s: %s", name, label, e)
        after = dataset.total()
        new_entries = after - before
        stats.entries_added += new_entries
        if dataset.sources and label not in dataset.sources and new_entries > 0:
            dataset.sources.append(label)
        return new_entries

    def _load_source(self, source: Any, label: str) -> Optional[Dict[str, Any]]:
        """Normalize a source into a world dict for the extractors."""
        if source is None:
            return None
        # Strings/paths
        if isinstance(source, (str, Path)):
            for extractor in self.extractors.values():
                try:
                    return extractor.load(source)
                except Exception:  # noqa: BLE001
                    continue
            return None
        # Already a dict
        if isinstance(source, dict):
            return source
        # WorldModel-like — try .to_dict()
        if hasattr(source, "to_dict"):
            try:
                d = source.to_dict()
                if isinstance(d, dict):
                    return d
            except Exception:  # noqa: BLE001
                pass
        # Blueprint-like — flatten via to_dict
        if hasattr(source, "name") and hasattr(source, "theme") and hasattr(source, "category"):
            return {
                "name": getattr(source, "name", label),
                "theme": getattr(source, "theme", "generic"),
                "category": getattr(source, "category", "unknown"),
                "meta": {
                    "name": getattr(source, "name", label),
                    "theme": getattr(source, "theme", "generic"),
                    "category": getattr(source, "category", "unknown"),
                    "source": label,
                },
            }
        # Campaign-like — try to_dict, else to a generic dict
        if hasattr(source, "to_dict"):
            try:
                d = source.to_dict()
                if isinstance(d, dict):
                    d.setdefault("meta", {})
                    if isinstance(d["meta"], dict):
                        d["meta"].setdefault("source", label)
                    return d
            except Exception:  # noqa: BLE001
                pass
        return {
            "meta": {"source": label, "raw": str(source)},
            "tiles": [], "regions": [], "structures": [],
            "spawns": [], "cities": [], "waypoints": [],
        }

    def _label_of(self, source: Any) -> str:
        if isinstance(source, (str, Path)):
            p = Path(source)
            return p.name or str(source)
        if isinstance(source, dict):
            meta = source.get("meta", {}) or {}
            return str(meta.get("source") or meta.get("name") or "dict")
        for attr in ("name", "filename", "path", "source_name"):
            v = getattr(source, attr, None)
            if v:
                return str(v)
        return type(source).__name__
