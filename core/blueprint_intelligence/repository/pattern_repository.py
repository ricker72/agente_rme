"""BI-3 Pattern Repository — store, retrieve, filter, and search patterns."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.blueprint_intelligence.models.pattern import Pattern


class PatternRepository:
    """Persistent storage and retrieval for reusable structural patterns.

    Responsibilities:
        Store patterns
        Retrieve patterns
        Filter patterns
        Search by category
        Search by source

    Deterministic: Same data always produces same repository state.
    """

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self._patterns: dict[str, Pattern] = {}
        self._storage_path: Path | None = (
            Path(storage_path) if storage_path else None
        )

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def add(self, pattern: Pattern) -> None:
        """Store a single pattern indexed by pattern_id."""
        if pattern.pattern_id in self._patterns:
            raise ValueError(
                f"Pattern with pattern_id '{pattern.pattern_id}' already exists"
            )
        self._patterns[pattern.pattern_id] = pattern

    def get(self, pattern_id: str) -> Pattern | None:
        """Retrieve a pattern by its pattern_id."""
        return self._patterns.get(pattern_id)

    def all(self) -> list[Pattern]:
        """Return all stored patterns in insertion order."""
        return list(self._patterns.values())

    def count(self) -> int:
        """Return the number of stored patterns."""
        return len(self._patterns)

    # ------------------------------------------------------------------
    # Search / filter
    # ------------------------------------------------------------------

    def find_by_source(self, source: str) -> list[Pattern]:
        """Return all patterns originating from *source* (case-sensitive)."""
        if not source:
            return []
        return [p for p in self._patterns.values() if p.source == source]

    def find_by_category(self, category: str) -> list[Pattern]:
        """Return all patterns matching *category* (case-sensitive)."""
        if not category:
            return []
        return [p for p in self._patterns.values() if p.category == category]

    def find_by_tag(self, tag: str) -> list[Pattern]:
        """Return all patterns that contain *tag* in their tags list."""
        if not tag:
            return []
        return [p for p in self._patterns.values() if tag in p.tags]

    def find_by_confidence(
        self, min_conf: float = 0.0, max_conf: float = 1.0
    ) -> list[Pattern]:
        """Return all patterns whose confidence is in [min_conf, max_conf]."""
        return [
            p
            for p in self._patterns.values()
            if min_conf <= p.confidence <= max_conf
        ]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path | None = None) -> str:
        """Serialize all patterns to JSON.

        Returns the path the file was written to.
        """
        output_path = Path(path) if path else self._storage_path
        if output_path is None:
            raise ValueError("No storage path configured — pass a path argument")

        output_path = output_path.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {
            "version": "BI-3.0",
            "patterns": [p.to_dict() for p in self._patterns.values()],
        }
        output_path.write_text(
            json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8",
        )
        return str(output_path)

    def load(self, path: str | Path | None = None) -> int:
        """Deserialize patterns from JSON.

        Returns the number of patterns loaded.
        Existing patterns are *not* cleared — loaded patterns are merged.
        """
        source_path = Path(path) if path else self._storage_path
        if source_path is None or not source_path.exists():
            return 0

        data = json.loads(source_path.read_text(encoding="utf-8"))
        patterns_data: list[dict[str, Any]] = data.get("patterns", [])
        count = 0
        for pd in patterns_data:
            pattern = Pattern.from_dict(pd)
            # Allow overwrite on load to support repository restoration
            self._patterns[pattern.pattern_id] = pattern
            count += 1
        return count

    def clear(self) -> None:
        """Remove all patterns from the repository."""
        self._patterns.clear()

    # ------------------------------------------------------------------
    # Bulk operations
    # ------------------------------------------------------------------

    def add_batch(self, patterns: list[Pattern]) -> None:
        """Store multiple patterns atomically.

        Raises ValueError if any pattern_id duplicates an existing one.
        """
        for pattern in patterns:
            if pattern.pattern_id in self._patterns:
                raise ValueError(
                    f"Pattern with pattern_id '{pattern.pattern_id}' already exists"
                )
        for pattern in patterns:
            self._patterns[pattern.pattern_id] = pattern


__all__ = ["PatternRepository"]
