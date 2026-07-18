# mypy: ignore-errors
"""
Blueprint Intelligence 2.0 — Blueprint Repository.

Persistence layer for BlueprintV2 objects.
Handles save, load, list, search, and batch operations.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.blueprint_v2 import BlueprintV2


class BlueprintRepository:
    """
    Repository for BlueprintV2 persistence.

    Provides CRUD operations and search capabilities
    for stored blueprints.
    """

    def __init__(self, storage_path: str = "core/blueprint_intelligence/datasets/"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def save(self, bp: BlueprintV2, filename: Optional[str] = None) -> str:
        """
        Save a blueprint to disk.

        Args:
            bp: BlueprintV2 to save.
            filename: Custom filename (optional). Defaults to blueprint_id.

        Returns:
            Path to saved file.
        """
        name = filename or bp.blueprint_id or bp.name
        safe_name = name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        filepath = self.storage_path / f"{safe_name}.json"

        data = bp.to_dict()
        data["_saved_at"] = datetime.now().isoformat()

        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return str(filepath)

    def load(self, name: str) -> Optional[BlueprintV2]:
        """
        Load a blueprint from disk.

        Args:
            name: Blueprint name or ID (without extension).

        Returns:
            BlueprintV2 or None.
        """
        filepath = self.storage_path / f"{name}.json"
        if not filepath.exists():
            return None

        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
            return BlueprintV2.from_dict(data)
        except (json.JSONDecodeError, Exception):
            return None

    def delete(self, name: str) -> bool:
        """
        Delete a blueprint from disk.

        Args:
            name: Blueprint name or ID (without extension).

        Returns:
            True if deleted, False if not found.
        """
        filepath = self.storage_path / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------

    def list_all(self) -> List[BlueprintV2]:
        """
        Load all blueprints from the repository.

        Returns:
            List of BlueprintV2 instances.
        """
        blueprints: List[BlueprintV2] = []
        for filepath in sorted(self.storage_path.glob("*.json")):
            if filepath.stem == "__init__":
                continue
            bp = self.load(filepath.stem)
            if bp is not None:
                blueprints.append(bp)
        return blueprints

    def list_names(self) -> List[str]:
        """List all blueprint names in the repository."""
        return sorted(
            [f.stem for f in self.storage_path.glob("*.json") if f.stem != "__init__"]
        )

    def count(self) -> int:
        """Number of blueprints in the repository."""
        return len(self.list_names())

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_by_type(self, bp_type: str) -> List[BlueprintV2]:
        """Search blueprints by type."""
        return [bp for bp in self.list_all() if bp.type == bp_type]

    def search_by_tag(self, tag: str) -> List[BlueprintV2]:
        """Search blueprints by tag."""
        return [bp for bp in self.list_all() if tag in bp.tags]

    def search_by_source(self, source: str) -> List[BlueprintV2]:
        """Search blueprints by provenance source."""
        return [bp for bp in self.list_all() if bp.provenance.source == source]

    def search_by_score(
        self, min_score: float = 0.0, max_score: float = 100.0
    ) -> List[BlueprintV2]:
        """Search blueprints by blueprint_score range."""
        return [
            bp for bp in self.list_all() if min_score <= bp.blueprint_score <= max_score
        ]

    # ------------------------------------------------------------------
    # Batch operations
    # ------------------------------------------------------------------

    def save_batch(self, blueprints: List[BlueprintV2]) -> List[str]:
        """Save multiple blueprints at once."""
        return [self.save(bp) for bp in blueprints]

    def load_batch(self, names: List[str]) -> List[BlueprintV2]:
        """Load multiple blueprints by name."""
        return [bp for name in names if (bp := self.load(name)) is not None]

    # ------------------------------------------------------------------
    # Import / Export
    # ------------------------------------------------------------------

    def export_to_json(self, name: str) -> Optional[str]:
        """Export a blueprint as a JSON string."""
        bp = self.load(name)
        if bp is None:
            return None
        return json.dumps(bp.to_dict(), indent=2, ensure_ascii=False)

    def import_from_json(self, json_str: str) -> Optional[BlueprintV2]:
        """Import a blueprint from a JSON string."""
        try:
            data = json.loads(json_str)
            return BlueprintV2.from_dict(data)
        except (json.JSONDecodeError, Exception):
            return None

    # ------------------------------------------------------------------
    # Repository health
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        """Get a summary of the repository contents."""
        blueprints = self.list_all()
        types: Dict[str, int] = {}
        sources: Dict[str, int] = {}

        for bp in blueprints:
            types[bp.type] = types.get(bp.type, 0) + 1
            source = bp.provenance.source or "unknown"
            sources[source] = sources.get(source, 0) + 1

        return {
            "total": len(blueprints),
            "by_type": types,
            "by_source": sources,
            "avg_score": (
                sum(bp.blueprint_score for bp in blueprints) / len(blueprints)
                if blueprints
                else 0.0
            ),
        }
