"""
NpcIndexer — Indexa NPCs de Tibia desde npc.xml o lista conocida.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional


class NpcIndexer:
    """
    Indexa NPCs de Tibia.
    Lee npc.xml o usa lista conocida por defecto.
    """

    def __init__(self):
        self._npcs: Dict[str, Dict[str, Any]] = {}

    def index_npcs_xml(self, path: str) -> int:
        """Index NPCs from an NPC XML file."""
        tree = ET.parse(path)
        root = tree.getroot()
        count = 0

        for elem in root.findall("npc"):
            name = elem.get("name", "")
            if not name:
                continue

            npc = {
                "name": name,
                "file": elem.get("file", ""),
            }
            self._npcs[name] = npc
            count += 1

        return count

    def index_fallback_npcs(self) -> int:
        """Index a basic set of known NPCs."""
        fallback = ["Sam", "Rashid", "Gregor", "Yasir", "Telas"]
        for name in fallback:
            self._npcs[name] = {"name": name, "file": f"fallback/{name.lower()}.lua"}
        return len(self._npcs)

    def get_npc(self, name: str) -> Optional[Dict[str, Any]]:
        """Get an NPC by name (case-insensitive)."""
        if name in self._npcs:
            return self._npcs[name]
        for key, value in self._npcs.items():
            if key.lower() == name.lower():
                return value
        return None

    def all_npc_names(self) -> List[str]:
        """Get all NPC names."""
        return sorted(self._npcs.keys())

    def to_dict(self) -> Dict:
        """Serialize to dict for caching."""
        return {"npcs": self._npcs}

    def from_dict(self, data: Dict):
        """Deserialize from cached dict."""
        self._npcs = data.get("npcs", {})
