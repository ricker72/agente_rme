from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class BlueprintRegistry:
    """
    Loads reusable building blueprints from JSON files.

    Blueprints: temples, depots, markets, houses, bridges, boss_rooms.

    Usage:
        reg = BlueprintRegistry()
        reg.load_all("blueprints/")
        temple = reg.get_blueprint("temple", "issavi")
    """

    VALID_TYPES = {"temple", "depot", "market", "house", "bridge", "boss_room",
                   "plaza", "gate", "wall", "tower", "garrison"}

    def __init__(self):
        self._blueprints: Dict[str, Dict[str, Any]] = {}  # type -> name -> spec

    def load_all(self, directory: str | Path) -> int:
        """Load all JSON blueprints from a directory. Returns count loaded."""
        base = Path(directory)
        if not base.exists():
            return 0
        count = 0
        for f in base.rglob("*.json"):
            try:
                spec = json.loads(f.read_text(encoding="utf-8"))
                name = spec.get("name", f.stem)
                btype = spec.get("type", "unknown").lower()
                if btype not in self.VALID_TYPES:
                    btype = "unknown"
                self._blueprints.setdefault(btype, {})[name] = spec
                count += 1
            except (json.JSONDecodeError, KeyError):
                pass
        return count

    def register(self, name: str, btype: str, spec: Dict[str, Any]) -> None:
        """Register a single blueprint by type and name."""
        self._blueprints.setdefault(btype.lower(), {})[name] = spec

    def get_blueprint(self, btype: str, name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a blueprint by type, optionally filtered by name."""
        type_map = self._blueprints.get(btype.lower(), {})
        if name:
            return type_map.get(name)
        if type_map:
            return next(iter(type_map.values()))
        return None

    def get_all_of_type(self, btype: str) -> List[Dict[str, Any]]:
        """Get all blueprints of a given type."""
        return list(self._blueprints.get(btype.lower(), {}).values())

    def list_types(self) -> List[str]:
        """Return all registered blueprint types."""
        return sorted(self._blueprints.keys())

    def summary(self) -> Dict[str, int]:
        """Return count per blueprint type."""
        return {k: len(v) for k, v in self._blueprints.items()}