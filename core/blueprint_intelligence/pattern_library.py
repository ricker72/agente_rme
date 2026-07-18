"""BI-3 Pattern Library Engine — orchestration hub.

The PatternLibrary connects:
    - PatternRepository   (storage, retrieval, filtering)
    - Pattern Extractors  (city, hunt, dungeon)
    - Provenance tracking

Responsibilities:
    register_patterns()
    extract_patterns()
    query_patterns()
    load_repository()
    save_repository()

This is NOT generation, NOT similarity, NOT critic evaluation.
This is Pattern Discovery, Pattern Storage, Pattern Retrieval.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.blueprint_intelligence.models.blueprint import Blueprint
from core.blueprint_intelligence.models.pattern import Pattern
from core.blueprint_intelligence.pattern_extractors import (
    CityPatternExtractor,
    DungeonPatternExtractor,
    HuntPatternExtractor,
)
from core.blueprint_intelligence.repository.pattern_repository import (
    PatternRepository,
)

# Pattern library version
PATTERN_LIBRARY_VERSION = "BI-3.0"

# Default storage path
_DEFAULT_STORAGE = Path("core/blueprint_intelligence/pattern_library.json")


class PatternLibrary:
    """Pattern Library — the hub for pattern discovery, storage, and retrieval.

    Usage:
        lib = PatternLibrary()
        lib.register_patterns(patterns)
        lib.save_repository("patterns.json")

        lib2 = PatternLibrary()
        lib2.load_repository("patterns.json")
        results = lib2.query_patterns(source="Issavi")
    """

    def __init__(
        self,
        repository: PatternRepository | None = None,
        city_extractor: CityPatternExtractor | None = None,
        hunt_extractor: HuntPatternExtractor | None = None,
        dungeon_extractor: DungeonPatternExtractor | None = None,
    ) -> None:
        self._repository = repository or PatternRepository()
        self._city_extractor = city_extractor or CityPatternExtractor()
        self._hunt_extractor = hunt_extractor or HuntPatternExtractor()
        self._dungeon_extractor = dungeon_extractor or DungeonPatternExtractor()

    # ------------------------------------------------------------------
    # Pattern discovery — extract patterns from blueprints
    # ------------------------------------------------------------------

    def extract_patterns(self, blueprints: list[Blueprint]) -> list[Pattern]:
        """Extract patterns from a list of blueprints using the appropriate extractor.

        Each blueprint is dispatched to the matching extractor based on its type.

        Args:
            blueprints: One or more Blueprint objects.

        Returns:
            A flat list of all extracted Pattern objects.
        """
        all_patterns: list[Pattern] = []
        for blueprint in blueprints:
            if self._city_extractor.supports(blueprint):
                all_patterns.extend(self._city_extractor.extract(blueprint))
            elif self._hunt_extractor.supports(blueprint):
                all_patterns.extend(self._hunt_extractor.extract(blueprint))
            elif self._dungeon_extractor.supports(blueprint):
                all_patterns.extend(self._dungeon_extractor.extract(blueprint))
        return all_patterns

    # ------------------------------------------------------------------
    # Pattern registration — store patterns in the repository
    # ------------------------------------------------------------------

    def register_patterns(self, patterns: list[Pattern]) -> int:
        """Register patterns into the repository.

        Args:
            patterns: Patterns to register.

        Returns:
            Number of patterns registered.
        """
        for pattern in patterns:
            try:
                self._repository.add(pattern)
            except ValueError:
                # Skip duplicate pattern_ids gracefully during batch registration
                pass
        return len(patterns)

    def register_pattern(self, pattern: Pattern) -> None:
        """Register a single pattern into the repository.

        Raises ValueError if pattern_id already exists.
        """
        self._repository.add(pattern)

    # ------------------------------------------------------------------
    # Pattern query — search and filter patterns
    # ------------------------------------------------------------------

    def query_patterns(
        self,
        pattern_id: str | None = None,
        source: str | None = None,
        category: str | None = None,
        tag: str | None = None,
        min_confidence: float | None = None,
        max_confidence: float | None = None,
    ) -> list[Pattern]:
        """Query patterns by multiple optional filters.

        All supplied filters are applied together (AND logic).

        Args:
            pattern_id: Exact pattern_id lookup (returns at most one).
            source: Filter by source name.
            category: Filter by category.
            tag: Filter by tag presence.
            min_confidence: Minimum confidence threshold.
            max_confidence: Maximum confidence threshold.

        Returns:
            Filtered list of Pattern objects.
        """
        # Start from full repository list
        results: list[Pattern] = self._repository.all()

        # Exact ID lookup short-circuits all other filters
        if pattern_id is not None:
            single = self._repository.get(pattern_id)
            return [single] if single else []

        if source is not None:
            results = [p for p in results if p.source == source]
        if category is not None:
            results = [p for p in results if p.category == category]
        if tag is not None:
            results = [p for p in results if tag in p.tags]
        if min_confidence is not None:
            results = [p for p in results if p.confidence >= min_confidence]
        if max_confidence is not None:
            results = [p for p in results if p.confidence <= max_confidence]

        return results

    def list_patterns(self) -> list[Pattern]:
        """Return all registered patterns."""
        return self._repository.all()

    def get_pattern(self, pattern_id: str) -> Pattern | None:
        """Get a pattern by its pattern_id."""
        return self._repository.get(pattern_id)

    def count_patterns(self) -> int:
        """Return the total number of registered patterns."""
        return self._repository.count()

    # ------------------------------------------------------------------
    # Repository persistence
    # ------------------------------------------------------------------

    def save_repository(self, path: str | Path | None = None) -> str:
        """Persist the pattern repository to JSON.

        Args:
            path: File path for the JSON repository file.
                  Defaults to core/blueprint_intelligence/pattern_library.json

        Returns:
            The path the file was written to.
        """
        return self._repository.save(path or _DEFAULT_STORAGE)

    def load_repository(self, path: str | Path | None = None) -> int:
        """Load patterns from a JSON repository file.

        Args:
            path: File path to load from.
                  Defaults to core/blueprint_intelligence/pattern_library.json

        Returns:
            Number of patterns loaded.
        """
        return self._repository.load(path or _DEFAULT_STORAGE)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def list_sources(self) -> list[str]:
        """List all unique source names in the repository."""
        return list({p.source for p in self._repository.all()})

    def list_categories(self) -> list[str]:
        """List all unique category names in the repository."""
        return list({p.category for p in self._repository.all()})

    def clear(self) -> None:
        """Clear all patterns from the library and repository."""
        self._repository.clear()

    def to_dict(self) -> dict[str, Any]:
        """Export the full library state as a dictionary."""
        return {
            "library_version": PATTERN_LIBRARY_VERSION,
            "pattern_count": self._repository.count(),
            "patterns": [p.to_dict() for p in self._repository.all()],
        }

    def to_json(self) -> str:
        """Export the full library state as a JSON string."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)


__all__ = ["PatternLibrary"]
