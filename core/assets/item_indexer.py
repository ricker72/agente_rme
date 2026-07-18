"""
ItemIndexer — Indexa items de Tibia desde items.xml o lista conocida.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

KNOWN_ITEMS = {
    # grounds
    415: {"id": 415, "name": "grass", "category": "ground"},
    817: {"id": 817, "name": "sand", "category": "ground"},
    395: {"id": 395, "name": "rock", "category": "ground"},
    393: {"id": 393, "name": "stone floor", "category": "ground"},
    406: {"id": 406, "name": "wooden floor", "category": "ground"},
    420: {"id": 420, "name": "cobblestone", "category": "ground"},
    103: {"id": 103, "name": "mud", "category": "ground"},
    106: {"id": 106, "name": "dirt", "category": "ground"},
    392: {"id": 392, "name": "pavement", "category": "ground"},
    394: {"id": 394, "name": "gravel", "category": "ground"},
    396: {"id": 396, "name": "marble floor", "category": "ground"},
    410: {"id": 410, "name": "ice", "category": "ground"},
    114: {"id": 114, "name": "water", "category": "ground"},
    # walls
    1495: {"id": 1495, "name": "stone wall", "category": "wall"},
    1497: {"id": 1497, "name": "dark wall", "category": "wall"},
    1498: {"id": 1498, "name": "fence", "category": "wall"},
    112: {"id": 112, "name": "dirt wall", "category": "wall"},
    111: {"id": 111, "name": "cave wall", "category": "wall"},
    113: {"id": 113, "name": "wooden wall", "category": "wall"},
    # decorations
    1700: {"id": 1700, "name": "shrub", "category": "decoration"},
    1701: {"id": 1701, "name": "vase", "category": "decoration"},
    1702: {"id": 1702, "name": "rock", "category": "decoration"},
    1703: {"id": 1703, "name": "bones", "category": "decoration"},
    1510: {"id": 1510, "name": "statue", "category": "decoration"},
    1512: {"id": 1512, "name": "altar", "category": "decoration"},
    1545: {"id": 1545, "name": "torch", "category": "decoration"},
    1765: {"id": 1765, "name": "fireplace", "category": "decoration"},
    1803: {"id": 1803, "name": "lamp", "category": "decoration"},
    2052: {"id": 2052, "name": "crystal decoration", "category": "decoration"},
    2064: {"id": 2064, "name": "holy fire", "category": "decoration"},
    2153: {"id": 2153, "name": "pillar", "category": "decoration"},
    2160: {"id": 2160, "name": "gold coin", "category": "item"},
    9034: {"id": 9034, "name": "candle", "category": "decoration"},
    9043: {"id": 9043, "name": "flower", "category": "decoration"},
}


class ItemIndexer:
    """
    Indexa items de Tibia.
    Lee items.xml o usa una lista conocida por defecto.
    """

    def __init__(self):
        self._items: Dict[int, Dict[str, Any]] = {}
        self._items_by_name: Dict[str, int] = {}

    def index_items_xml(self, path: str) -> int:
        """Index items from an items.xml file."""
        tree = ET.parse(path)
        root = tree.getroot()
        count = 0

        for elem in root.findall("item"):
            try:
                item_id = int(elem.get("id", elem.get("clientId", "0")))
            except (ValueError, TypeError):
                continue
            if item_id == 0:
                continue

            name = elem.get("name", "")
            type_name = elem.get("type", "")

            # Classify
            category = self._classify(name.lower(), type_name.lower())

            item = {
                "id": item_id,
                "name": name,
                "type": type_name,
                "category": category,
            }
            self._items[item_id] = item
            if name:
                self._items_by_name[name.lower()] = item_id
            count += 1

        return count

    def index_known_items(self) -> int:
        """Index the built-in known items list."""
        for item_id, item in KNOWN_ITEMS.items():
            self._items[item_id] = item
            name = item.get("name", "")
            if name:
                self._items_by_name[name.lower()] = item_id
        return len(self._items)

    def get_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Get an item by ID."""
        return self._items.get(item_id)

    def get_item_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get an item by name (case-insensitive)."""
        item_id = self._items_by_name.get(name.lower())
        if item_id:
            return self._items.get(item_id)
        return None

    def all_items(self) -> List[Dict[str, Any]]:
        """Get all indexed items."""
        return list(self._items.values())

    def to_dict(self) -> Dict:
        """Serialize to dict for caching."""
        return {
            "items": self._items,
            "items_by_name": self._items_by_name,
        }

    def from_dict(self, data: Dict):
        """Deserialize from cached dict."""
        self._items = data.get("items", {})
        self._items_by_name = data.get("items_by_name", {})

    @staticmethod
    def _classify(name: str, type_name: str) -> str:
        """Classify an item based on name and type."""
        # Check walls first (more specific)
        if any(kw in name for kw in ["wall", "fence", "gate", "bars", "pillar"]):
            return "wall"
        if type_name in ("ground", "floor"):
            return "ground"
        if any(
            kw in name
            for kw in [
                "floor",
                "ground",
                "grass",
                "dirt",
                "sand",
                "stone",
                "marble",
                "ice",
                "snow",
                "lava",
                "water",
                "pavement",
                "gravel",
                "cobblestone",
            ]
        ):
            return "ground"
        if any(
            kw in name
            for kw in [
                "torch",
                "lamp",
                "statue",
                "vase",
                "flower",
                "bone",
                "skull",
                "rock",
                "altar",
                "candle",
                "crystal",
                "shrub",
                "fireplace",
            ]
        ):
            return "decoration"
        return "item"
