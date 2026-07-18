"""Base interface for Blueprint Intelligence extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from core.blueprint_intelligence.models.blueprint import Blueprint


class BaseBlueprintExtractor(ABC):
    """Pure interface for converting supported sources into BI-1 Blueprints."""

    @abstractmethod
    def supports(self, source: str | Path) -> bool:
        """Return whether this extractor can handle the source."""

    @abstractmethod
    def extract(self, source: str | Path) -> list[Blueprint]:
        """Extract canonical BI-1 Blueprint objects from the source."""
