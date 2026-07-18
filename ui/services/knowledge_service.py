"""Knowledge service contract."""

from __future__ import annotations

from typing import Protocol

from ui.models.knowledge_dto import (
    KnowledgeMetricsDTO,
    KnowledgeQueryDTO,
    KnowledgeResultDTO,
)


class KnowledgeService(Protocol):
    """Contract between UI pages and future knowledge adapters."""

    def search(self, query: KnowledgeQueryDTO) -> list[KnowledgeResultDTO]:
        """Search the knowledge index."""
        ...

    def find_similar(self, name: str, entry_type: str) -> list[KnowledgeResultDTO]:
        """Find entries similar to a named entry."""
        ...

    def get_metrics(self) -> KnowledgeMetricsDTO:
        """Return knowledge index metrics."""
        ...
