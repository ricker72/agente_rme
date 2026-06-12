"""Knowledge service DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class KnowledgeQueryDTO:
    """Search request for future knowledge adapters."""

    text: str = ""
    limit: int = 10
    entry_types: list[str] = field(default_factory=list)


@dataclass(slots=True)
class KnowledgeResultDTO:
    """Single knowledge search result."""

    identifier: str = ""
    title: str = ""
    entry_type: str = ""
    excerpt: str = ""
    tags: list[str] = field(default_factory=list)
    source: str = ""
    relevance: float = 0.0


@dataclass(slots=True)
class KnowledgeMetricsDTO:
    """Knowledge index metrics for UI display."""

    total_entries: int = 0
    indexed_sources: int = 0
    status: str = "Service not connected"
    success: bool = False
    error_message: str = ""


KnowledgeDTO = KnowledgeResultDTO
