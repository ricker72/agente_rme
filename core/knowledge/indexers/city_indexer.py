"""CityIndexer — index city entries with biome / service attributes."""

from __future__ import annotations

from typing import List, Tuple

from ..models import KnowledgeEntry
from .base_indexer import BaseIndexer


class CityIndexer(BaseIndexer):
    """Indexer specialized for cities (biome, services, layout)."""

    def __init__(self) -> None:
        super().__init__(name="city")

    def search(
        self,
        query: str,
        k: int = 5,
        *,
        min_score: float = 0.0,
        attrs=None,
    ) -> List[Tuple[KnowledgeEntry, float]]:
        return super().search(query, k=k, min_score=min_score, attrs=attrs)
