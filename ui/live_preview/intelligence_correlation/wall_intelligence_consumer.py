"""
Wall Intelligence Consumer for WG-20U-C-R.

Bridges WG20TC_WALL_CONNECTION_RULES.json into the appearance render pipeline
by mapping wall brush names + join types to correct appearance IDs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


class WallIntelligenceConsumer:
    """
    Consumes certified wall connection rules and maps them to appearance IDs
    per join type for correct visual rendering. Does NOT create new intelligence.
    """

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = Path(workspace_root or Path.cwd())
        self._join_overrides: Dict[str, Dict[str, int]] = {}
        self._brush_to_join_type: Dict[str, str] = {}
        self._loaded = False
        self._source_dataset = "WG20TC_WALL_CONNECTION_RULES.json"
        self._horizontal_wall_count = 0
        self._vertical_wall_count = 0
        self._junction_count = 0

    def load(self) -> "WallIntelligenceConsumer":
        """Load wall connection rules and build join overrides."""
        candidates = [
            self._source_dataset,
            "RME_WALL_CONNECTION_RULES.json",
        ]
        rules: Dict[str, Any] = {}
        for candidate in candidates:
            path = self.workspace_root / candidate
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    rules = json.load(f)
                self._source_dataset = candidate
                self._loaded = True
                break

        # Build join_overrides structure:
        # { "horizontal": { "alabaster wall": 7645 }, "vertical": { "alabaster wall": 7700 }, ... }
        for join_key, rule_key in [("horizontal", "horizontal_walls"),
                                   ("vertical", "vertical_walls"),
                                   ("junction", "junctions"),
                                   ("door", "door_connections")]:
            entries = rules.get(rule_key, [])
            for entry in entries:
                brush_name = entry.get("brush", "").lower().strip()
                members = entry.get("members", [])
                if brush_name and members:
                    self._join_overrides.setdefault(join_key, {})
                    self._join_overrides[join_key][brush_name] = int(members[0])
                    self._brush_to_join_type[brush_name] = join_key

        self._horizontal_wall_count = len(rules.get("horizontal_walls", []))
        self._vertical_wall_count = len(rules.get("vertical_walls", []))
        self._junction_count = len(rules.get("junctions", []))

        return self

    def get_join_overrides(self) -> Dict[str, Dict[str, int]]:
        """Get the join overrides for the render adapter."""
        return dict(self._join_overrides)

    def resolve_wall_appearance(self, brush_name: str, join_type: str) -> int:
        """Resolve the appearance_id for a wall brush + join type."""
        key = brush_name.lower().strip()
        join_key = join_type.lower().strip()
        overrides = self._join_overrides.get(join_key, {})
        if key in overrides:
            return overrides[key]
        # Fallback: try any join type
        for jk, ov in self._join_overrides.items():
            if key in ov:
                return ov[key]
        return 0

    def audit(self) -> Dict[str, Any]:
        """Audit the wall intelligence consumer state."""
        return {
            "wall_consumer_ready": self._loaded,
            "source_dataset": self._source_dataset,
            "horizontal_wall_count": self._horizontal_wall_count,
            "vertical_wall_count": self._vertical_wall_count,
            "junction_count": self._junction_count,
            "join_overrides_count": sum(len(v) for v in self._join_overrides.values()),
            "duplicate_intelligence_created": False,
        }