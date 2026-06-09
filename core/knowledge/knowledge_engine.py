"""
KnowledgeEngine — the public API for the knowledge subsystem.

This is the entry point used by the rest of the agent (and the CLI) to
query the catalog of previously seen maps.

Example:
    engine = KnowledgeEngine()
    engine.load("output/knowledge_dataset.json")
    print(engine.find_similar_hunts("Roshamuul"))
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .dataset_builder import DatasetBuilder
from .knowledge_catalog import KnowledgeCatalog
from .knowledge_index import KnowledgeIndex
from .knowledge_query import KnowledgeQuery
from .knowledge_ranker import KnowledgeRanker
from .knowledge_recommender import KnowledgeRecommender
from .knowledge_search import KnowledgeSearch
from .models import (
    EntryType,
    KnowledgeDataset,
    KnowledgeEntry,
    KnowledgeQueryResult,
)


class KnowledgeEngine:
    """
    The high-level knowledge engine.

    Holds the dataset + indexes + ranker + recommender + search facade and
    exposes the API described in HITO 28.
    """

    DEFAULT_DATASET_PATH = "output/knowledge_dataset.json"

    def __init__(
        self,
        dataset: Optional[KnowledgeDataset] = None,
        index: Optional[KnowledgeIndex] = None,
    ) -> None:
        self.dataset = dataset or KnowledgeDataset()
        self.index = index or KnowledgeIndex()
        self.index.sync(self.dataset)
        self.ranker = KnowledgeRanker()
        self.recommender = KnowledgeRecommender(self.index, self.ranker)
        self.search = KnowledgeSearch(self.index, self.ranker)
        self.query = KnowledgeQuery(self.index)
        self.catalog: Optional[KnowledgeCatalog] = None

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: str) -> "KnowledgeEngine":
        """Create an engine preloaded from a JSON dataset file."""
        dataset = KnowledgeDataset.read(path)
        return cls(dataset=dataset)

    def reload(self) -> None:
        """Re-sync the index from the current dataset."""
        self.index.sync(self.dataset)

    def save(self, path: Optional[str] = None) -> str:
        path = path or self.DEFAULT_DATASET_PATH
        return self.dataset.write(path)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    @classmethod
    def build_from_sources(
        cls,
        sources: List[Any],
        save_path: Optional[str] = None,
    ) -> "KnowledgeEngine":
        """Build a dataset from a list of sources and return a new engine."""
        builder = DatasetBuilder()
        dataset = builder.build_from_sources(sources)
        engine = cls(dataset=dataset)
        if save_path:
            engine.save(save_path)
        return engine

    # ------------------------------------------------------------------
    # Public API — find similar
    # ------------------------------------------------------------------

    def find_similar_hunts(self, name: str, k: int = 5) -> List[Dict[str, Any]]:
        return self._find_similar(EntryType.HUNT, name, k)

    def find_similar_cities(self, name: str, k: int = 5) -> List[Dict[str, Any]]:
        return self._find_similar(EntryType.CITY, name, k)

    def find_similar_boss_rooms(self, name: str, k: int = 5) -> List[Dict[str, Any]]:
        return self._find_similar(EntryType.BOSS_ROOM, name, k)

    def find_similar_regions(self, name: str, k: int = 5) -> List[Dict[str, Any]]:
        return self._find_similar(EntryType.REGION, name, k)

    def find_similar_raids(self, name: str, k: int = 5) -> List[Dict[str, Any]]:
        return self._find_similar(EntryType.RAID, name, k)

    def find_similar_quests(self, name: str, k: int = 5) -> List[Dict[str, Any]]:
        return self._find_similar(EntryType.QUEST, name, k)

    def _find_similar(
        self,
        entry_type: EntryType,
        name: str,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Return a list of `{name, score}` dicts.

        If the engine has the exact entry, the result is a list of
        similar entries ranked by hybrid similarity.  If the engine does
        not have the exact entry, falls back to a name search.
        """
        indexer = self.index.indexer_for(entry_type)
        if indexer is None or len(indexer) == 0:
            return []
        # Try direct lookup with case-insensitive comparison
        direct = indexer.get(name)
        if direct is not None:
            res = self.search.find_similar(direct, k=k)
            out: List[Dict[str, Any]] = [{
                "name": direct.name,
                "score": 1.0,
                "biome": direct.biome,
                "entry_type": direct.entry_type.value,
                "min_level": direct.min_level,
                "max_level": direct.max_level,
                "match_type": "exact",
            }]
            for m in res.matches[:k]:
                if m.entry.id == direct.id:
                    continue
                out.append({
                    "name": m.entry.name,
                    "score": round(float(m.score), 4),
                    "biome": m.entry.biome,
                    "entry_type": m.entry.entry_type.value,
                    "min_level": m.entry.min_level,
                    "max_level": m.entry.max_level,
                    "match_type": m.match_type,
                })
            return out[:k]
        # Fall back to text search
        res = self.search.find_by_text(name, k=k)
        out2: List[Dict[str, Any]] = []
        for m in res.matches[:k]:
            out2.append({
                "name": m.entry.name,
                "score": round(float(m.score), 4),
                "biome": m.entry.biome,
                "entry_type": m.entry.entry_type.value,
                "min_level": m.entry.min_level,
                "max_level": m.entry.max_level,
                "match_type": m.match_type,
            })
        return out2

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query_text(self, text: str, k: int = 5) -> KnowledgeQueryResult:
        return self.query.text(text, k=k)

    def query_structured(
        self,
        entry_type: EntryType,
        k: int = 10,
        **filters: Any,
    ) -> KnowledgeQueryResult:
        return self.query.structured(entry_type=entry_type, k=k, **filters)

    # ------------------------------------------------------------------
    # Catalog / metrics
    # ------------------------------------------------------------------

    def build_catalog(self, top_n: int = 5) -> KnowledgeCatalog:
        self.catalog = KnowledgeCatalog.build(self.dataset, top_n=top_n)
        return self.catalog

    def get_catalog(self) -> KnowledgeCatalog:
        if self.catalog is None:
            self.catalog = KnowledgeCatalog.build(self.dataset)
        return self.catalog

    def write_catalog(self, path: str) -> str:
        cat = self.get_catalog()
        return cat.write(path)

    # ------------------------------------------------------------------
    # Prompt-driven knowledge lookup (the new generation pipeline)
    # ------------------------------------------------------------------

    def lookup_for_prompt(self, prompt: str, k: int = 5) -> Dict[str, Any]:
        """
        Extract knowledge hints from a prompt.

        Returns a dict with detected biome, level range, theme, and a list
        of similar entries to inspire the generation.
        """
        from .knowledge_query import parse_query
        parsed = parse_query(prompt)
        out: Dict[str, Any] = {
            "prompt": prompt,
            "entry_type": parsed.entry_type.value if parsed.entry_type else None,
            "biome": parsed.biome,
            "difficulty": parsed.difficulty,
            "min_level": parsed.min_level,
            "max_level": parsed.max_level,
            "attrs": parsed.attrs,
            "similar": [],
        }
        if parsed.entry_type is not None:
            res = self.search.search(
                prompt, k=k, entry_type=parsed.entry_type,
                min_level=parsed.min_level,
                max_level=parsed.max_level,
                biome=parsed.biome,
            )
            out["similar"] = [
                {
                    "name": m.entry.name,
                    "score": round(m.score, 4),
                    "biome": m.entry.biome,
                    "min_level": m.entry.min_level,
                    "max_level": m.entry.max_level,
                }
                for m in res.matches[:k]
            ]
        return out
