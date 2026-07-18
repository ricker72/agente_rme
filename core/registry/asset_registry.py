from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET


class AssetRegistry:
    """
    Indexes items.xml, monsters.xml, and npc.xml for fast lookups.

    Usage:
        reg = AssetRegistry()
        reg.load_items("path/to/items.xml")
        reg.load_monsters("path/to/monsters/")
        reg.load_npcs("path/to/npcs.xml")
        ground_ids = reg.get_grounds()
    """

    def __init__(self):
        self._items: Dict[int, Dict] = {}
        self._items_by_name: Dict[str, int] = {}
        self._monsters: List[str] = []
        self._npcs: List[str] = []
        self._grounds: List[int] = []
        self._walls: List[int] = []
        self._decorations: List[int] = []
        self._loaded = False

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_items(self, path: str | Path) -> int:
        """Load items.xml and index by ID and name. Returns count."""
        tree = ET.parse(str(path))
        root = tree.getroot()
        for item in root.iter("item"):
            try:
                item_id = int(item.get("id", item.get("clientId", "0")))
            except (ValueError, TypeError):
                continue
            name = item.get("name", "").lower()
            self._items[item_id] = {"id": item_id, "name": name, "element": item}
            if name:
                self._items_by_name[name] = item_id
            # Classify
            if any(
                kw in name
                for kw in [
                    "floor",
                    "ground",
                    "grass",
                    "stone",
                    "sand",
                    "marble",
                    "crystal",
                    "ice",
                    "snow",
                    "lava",
                    "water",
                    "cave",
                    "mountain",
                ]
            ):
                self._grounds.append(item_id)
            elif any(kw in name for kw in ["wall", "border", "fence"]):
                self._walls.append(item_id)
            elif any(
                kw in name
                for kw in [
                    "torch",
                    "lamp",
                    "statue",
                    "flower",
                    "blood",
                    "bones",
                    "skull",
                    "rubble",
                    "glow",
                    "crystal",
                ]
            ):
                self._decorations.append(item_id)
        return len(self._items)

    def load_monsters(self, path: str | Path) -> int:
        """Load monster XML files. Returns count."""
        p = Path(path)
        files = [p] if p.is_file() else list(p.glob("*.xml"))
        self._monsters = []
        for f in files:
            tree = ET.parse(str(f))
            for m in tree.iter("monster"):
                name = m.get("name", "")
                if name:
                    self._monsters.append(name)
        return len(self._monsters)

    def load_npcs(self, path: str | Path) -> int:
        """Load NPC XML files. Returns count."""
        p = Path(path)
        files = [p] if p.is_file() else list(p.glob("*.xml"))
        self._npcs = []
        for f in files:
            tree = ET.parse(str(f))
            for n in tree.iter("npc"):
                name = n.get("name", "")
                if name:
                    self._npcs.append(name)
        return len(self._npcs)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_grounds(self) -> List[int]:
        return list(self._grounds)

    def get_walls(self) -> List[int]:
        return list(self._walls)

    def get_decorations(self) -> List[int]:
        return list(self._decorations)

    def get_monsters(self) -> List[str]:
        return list(self._monsters)

    def get_npcs(self) -> List[str]:
        return list(self._npcs)

    def get_item_id(self, name: str) -> Optional[int]:
        return self._items_by_name.get(name.lower())

    def get_item_name(self, item_id: int) -> Optional[str]:
        item = self._items.get(item_id)
        return item["name"] if item else None

    def is_loaded(self) -> bool:
        return bool(self._items or self._monsters or self._npcs)

    def summary(self) -> Dict:
        return {
            "items": len(self._items),
            "monsters": len(self._monsters),
            "npcs": len(self._npcs),
            "grounds": len(self._grounds),
            "walls": len(self._walls),
            "decorations": len(self._decorations),
        }
