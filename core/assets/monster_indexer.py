"""
MonsterIndexer — Indexa monstruos de Tibia desde monster.xml o lista conocida.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Set

# Fallback monsters — usados si no hay monster.xml disponible
FALLBACK_MONSTERS: Set[str] = {
    "Crypt Warden",
    "Skeleton",
    "Demon Skeleton",
    "Priestess",
    "Death Priest",
    "Frazzlemaw",
    "Sphinx",
    "Cloak Of Terror",
    "Vexclaw",
    "Guzzlemaw",
    "Shrieker",
    "Dragon",
    "Dragon Lord",
    "Rat",
    "Demon",
    "Behemoth",
    "Cyclops",
    "Dwarf",
    "Elf",
    "Goblin",
    "Minotaur",
    "Orc",
    "Troll",
    "Wolf",
    "Bear",
    "Deer",
    "Chicken",
    "Rabbit",
    "Bat",
    "Spider",
    "Giant Spider",
    "Nightmare",
    "Silencer",
    "Nightmare Scion",
    "Ghastly Dragon",
    "Ferumbras",
    "Gaz'Haragoth",
}


class MonsterIndexer:
    """
    Indexa monstruos de Tibia.
    Lee monster.xml o usa lista conocida por defecto.
    """

    def __init__(self):
        self._monsters: Dict[str, Dict[str, Any]] = {}

    def index_monsters_xml(self, path: str) -> int:
        """Index monsters from a monster XML file."""
        tree = ET.parse(path)
        root = tree.getroot()
        count = 0

        for elem in root.findall("monster"):
            name = elem.get("name", "")
            if not name:
                continue

            monster = {
                "name": name,
                "file": elem.get("file", ""),
            }
            self._monsters[name] = monster
            count += 1

        # Ensure fallback monsters are always included
        for name in FALLBACK_MONSTERS:
            if name not in self._monsters:
                self._monsters[name] = {
                    "name": name,
                    "file": f"fallback/{name.lower().replace(' ', '_')}.lua",
                }

        return count

    def index_fallback_monsters(self) -> int:
        """Index the built-in fallback monster list."""
        for name in sorted(FALLBACK_MONSTERS):
            self._monsters[name] = {
                "name": name,
                "file": f"fallback/{name.lower().replace(' ', '_')}.lua",
            }
        return len(self._monsters)

    def get_monster(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a monster by name (case-insensitive)."""
        # Try exact match first
        if name in self._monsters:
            return self._monsters[name]
        # Try case-insensitive
        for key, value in self._monsters.items():
            if key.lower() == name.lower():
                return value
        return None

    def all_monster_names(self) -> List[str]:
        """Get all monster names."""
        return sorted(self._monsters.keys())

    def to_dict(self) -> Dict:
        """Serialize to dict for caching."""
        return {"monsters": self._monsters}

    def from_dict(self, data: Dict):
        """Deserialize from cached dict."""
        self._monsters = data.get("monsters", {})
