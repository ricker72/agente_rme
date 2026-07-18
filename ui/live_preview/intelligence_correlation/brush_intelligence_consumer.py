"""
Brush Intelligence Consumer for WG-20U-C-R.

Bridges RME_BRUSH_INTELLIGENCE_CATALOG.json into the appearance render pipeline
by mapping brush names + roles to correct appearance IDs.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


class BrushIntelligenceConsumer:
    """
    Consumes certified brush intelligence and maps it to appearance IDs
    for correct visual rendering. Does NOT create new intelligence.
    """

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = Path(workspace_root or Path.cwd())
        self._brush_to_appearance: Dict[str, int] = {}
        self._brush_roles: Dict[str, str] = {}
        self._loaded = False
        self._source_dataset = "RME_BRUSH_INTELLIGENCE_CATALOG.json"
        self._load_attempts: list[str] = []

    def load(self) -> "BrushIntelligenceConsumer":
        """Load brush intelligence and build appearance mappings."""
        candidates = [
            self._source_dataset,
            "WG20TE_BRUSH_INTELLIGENCE_CATALOG.json",
            "WG20TC_BRUSH_INTELLIGENCE_CATALOG.json",
        ]
        catalog: Dict[str, Any] = {}
        for candidate in candidates:
            path = self.workspace_root / candidate
            self._load_attempts.append(candidate)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    catalog = json.load(f)
                self._source_dataset = candidate
                self._loaded = True
                break

        brushes = catalog.get("brushes", {})
        for brush_name, brush_info in brushes.items():
            brush_name_lower = brush_name.lower()
            roles = brush_info.get("roles", [])
            # Convert lookid from string to int if needed
            raw_lookid = brush_info.get("lookid")
            lookid = None
            if raw_lookid is not None:
                try:
                    lookid = int(str(raw_lookid))
                except (ValueError, TypeError):
                    lookid = None
            if roles:
                self._brush_roles[brush_name_lower] = roles[0].upper() if isinstance(roles, list) else roles.upper()

            brush_type = brush_info.get("brush_type", "")
            if brush_type == "wall":
                self._brush_roles[brush_name_lower] = "WALL"
            elif brush_type == "ground":
                self._brush_roles.setdefault(brush_name_lower, "GROUND")
            elif brush_type == "doodad":
                family = brush_info.get("brush_family", "").lower()
                if family == "nature":
                    self._brush_roles.setdefault(brush_name_lower, "NATURE")
                elif family == "decoration":
                    self._brush_roles.setdefault(brush_name_lower, "DECORATION")
                elif family == "mountain":
                    self._brush_roles.setdefault(brush_name_lower, "GROUND")
                else:
                    self._brush_roles.setdefault(brush_name_lower, "DECORATION")

            # Map lookid → appearance_id
            if lookid is not None and lookid > 0:
                self._brush_to_appearance[brush_name_lower] = lookid

            # Map tileset members → appearance_id
            tilesets = brush_info.get("tilesets", {})
            if isinstance(tilesets, dict):
                for tileset_id, tileset_info in tilesets.items():
                    if isinstance(tileset_info, dict):
                        raw_ts = tileset_info.get("lookid")
                        lookid_ts = None
                        if raw_ts is not None:
                            try:
                                lookid_ts = int(str(raw_ts))
                            except (ValueError, TypeError):
                                lookid_ts = None
                        if lookid_ts is not None and lookid_ts > 0:
                            member_names = tileset_info.get("member_names", [])
                            for member in member_names:
                                if isinstance(member, str):
                                    self._brush_to_appearance[member.lower()] = lookid_ts

            # Use friend_brushes for cross-referencing
            friend_brushes = brush_info.get("friend_brushes", [])
            if isinstance(friend_brushes, list):
                for friend in friend_brushes:
                    if isinstance(friend, str) and lookid is not None and lookid > 0:
                        self._brush_to_appearance.setdefault(friend.lower(), lookid)

        return self

    def resolve_brush_appearance(self, brush_name: str, role: str = "") -> int:
        """Resolve the appearance_id for a given brush name."""
        key = brush_name.lower().strip()
        if key in self._brush_to_appearance:
            return self._brush_to_appearance[key]
        return 0

    def get_brush_role(self, brush_name: str) -> str:
        """Get the semantic role for a brush."""
        return self._brush_roles.get(brush_name.lower().strip(), "")

    def audit(self) -> Dict[str, Any]:
        """Audit the brush intelligence consumer state."""
        return {
            "brush_consumer_ready": self._loaded,
            "source_dataset": self._source_dataset,
            "load_attempts": self._load_attempts,
            "brushes_mapped_to_appearance": len(self._brush_to_appearance),
            "brush_roles_mapped": len(self._brush_roles),
            "duplicate_intelligence_created": False,
        }