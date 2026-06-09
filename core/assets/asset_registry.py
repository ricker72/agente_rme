"""
AssetRegistry — Fuente de verdad única para items, monsters y NPCs.

API:
    registry = AssetRegistry()
    registry.load()
    registry.get_item(9043)
    registry.item_exists(9043)
    registry.get_monster("Frazzlemaw")
    registry.monster_exists("Frazzlemaw")
    registry.get_grounds()
    registry.get_decorations()
    registry.get_walls()
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .item_indexer import ItemIndexer
from .monster_indexer import MonsterIndexer
from .npc_indexer import NpcIndexer
from .asset_cache import AssetCache


class AssetRegistry:
    """
    Registro central de assets de Tibia.
    Indexa items, monsters y NPCs desde archivos XML.
    """

    def __init__(self, cache_dir: str = "cache"):
        self._cache = AssetCache(cache_dir)
        self._item_indexer = ItemIndexer()
        self._monster_indexer = MonsterIndexer()
        self._npc_indexer = NpcIndexer()
        self._loaded = False
        self._grounds: Set[int] = set()
        self._walls: Set[int] = set()
        self._decorations: Set[int] = set()

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load(self, items_path: Optional[str] = None,
             monster_path: Optional[str] = None,
             npc_path: Optional[str] = None) -> bool:
        """
        Load all assets. Uses cache if available, otherwise indexes from XML.

        Args:
            items_path: Path to items.xml (optional).
            monster_path: Path to monster XML file or directory (optional).
            npc_path: Path to npc.xml (optional).

        Returns:
            True if loaded successfully.
        """
        # Try loading from cache first for dynamic data
        if self._cache.exists():
            self._load_from_cache()
            # Always ensure known items are present (cache may be stale)
            self._item_indexer.index_known_items()
            self._classify_all()
            self._loaded = True
            return True

        # Always index known items (built-in)
        self._item_indexer.index_known_items()

        # Index items from XML if available
        if items_path and os.path.exists(items_path):
            count = self._item_indexer.index_items_xml(items_path)
            print(f"Indexed {count} items from {items_path}")

        # Index monsters
        if monster_path and os.path.exists(monster_path):
            count = self._monster_indexer.index_monsters_xml(monster_path)
            print(f"Indexed {count} monsters from {monster_path}")
        else:
            # Try default paths
            default_paths = [
                "monster - npc/monster.xml",
                "monster.xml",
                "data/monster/monster.xml",
                "data/monster.xml",
            ]
            for dp in default_paths:
                if os.path.exists(dp):
                    count = self._monster_indexer.index_monsters_xml(dp)
                    print(f"Indexed {count} monsters from {dp}")
                    break
            else:
                self._monster_indexer.index_fallback_monsters()

        # Index NPCs
        if npc_path and os.path.exists(npc_path):
            count = self._npc_indexer.index_npcs_xml(npc_path)
            print(f"Indexed {count} NPCs from {npc_path}")
        else:
            default_npc_paths = [
                "monster - npc/npc.xml",
                "npc.xml",
                "data/npc/npc.xml",
                "data/npc.xml",
            ]
            for dp in default_npc_paths:
                if os.path.exists(dp):
                    count = self._npc_indexer.index_npcs_xml(dp)
                    print(f"Indexed {count} NPCs from {dp}")
                    break

        # Classify items into grounds, walls, decorations
        self._classify_all()

        # Save to cache
        self._save_to_cache()
        self._loaded = True
        return True

    def _classify_all(self):
        """Classify all indexed items into grounds, walls, decorations."""
        for item in self._item_indexer.all_items():
            cat = item.get("category", "unknown")
            item_id = item.get("id", 0)
            if cat == "ground":
                self._grounds.add(item_id)
            elif cat == "wall":
                self._walls.add(item_id)
            elif cat == "decoration":
                self._decorations.add(item_id)

    # ------------------------------------------------------------------
    # Items
    # ------------------------------------------------------------------

    def get_item(self, item_id: int) -> Optional[Dict]:
        """Get an item by ID."""
        return self._item_indexer.get_item(item_id)

    def item_exists(self, item_id: int) -> bool:
        """Check if an item ID exists in the registry."""
        return self._item_indexer.get_item(item_id) is not None

    def get_item_name(self, item_id: int) -> str:
        """Get item name by ID."""
        item = self.get_item(item_id)
        return item.get("name", "") if item else ""

    def get_grounds(self) -> List[int]:
        """Get all ground item IDs."""
        return sorted(self._grounds)

    def get_walls(self) -> List[int]:
        """Get all wall item IDs."""
        return sorted(self._walls)

    def get_decorations(self) -> List[int]:
        """Get all decoration item IDs."""
        return sorted(self._decorations)

    def is_ground(self, item_id: int) -> bool:
        """Check if an item ID is a ground type."""
        return item_id in self._grounds

    def is_wall(self, item_id: int) -> bool:
        """Check if an item ID is a wall type."""
        return item_id in self._walls

    def is_decoration(self, item_id: int) -> bool:
        """Check if an item ID is a decoration type."""
        return item_id in self._decorations

    # ------------------------------------------------------------------
    # Monsters
    # ------------------------------------------------------------------

    def get_monster(self, name: str) -> Optional[Dict]:
        """Get a monster by name."""
        return self._monster_indexer.get_monster(name)

    def monster_exists(self, name: str) -> bool:
        """Check if a monster name exists in the registry."""
        return self._monster_indexer.get_monster(name) is not None

    def get_all_monsters(self) -> List[str]:
        """Get all monster names."""
        return self._monster_indexer.all_monster_names()

    # ------------------------------------------------------------------
    # NPCs
    # ------------------------------------------------------------------

    def get_npc(self, name: str) -> Optional[Dict]:
        """Get an NPC by name."""
        return self._npc_indexer.get_npc(name)

    def npc_exists(self, name: str) -> bool:
        """Check if an NPC name exists in the registry."""
        return self._npc_indexer.get_npc(name) is not None

    # ------------------------------------------------------------------
    # Cache
    # ------------------------------------------------------------------

    def _save_to_cache(self):
        """Save indexed data to cache files."""
        self._cache.save_items(self._item_indexer.to_dict())
        self._cache.save_monsters(self._monster_indexer.to_dict())
        self._cache.save_npcs(self._npc_indexer.to_dict())
        self._cache.save_grounds(list(self._grounds))
        self._cache.save_walls(list(self._walls))
        self._cache.save_decorations(list(self._decorations))

    def _load_from_cache(self):
        """Load indexed data from cache files."""
        items_data = self._cache.load_items()
        if items_data:
            self._item_indexer.from_dict(items_data)

        monsters_data = self._cache.load_monsters()
        if monsters_data:
            self._monster_indexer.from_dict(monsters_data)

        npcs_data = self._cache.load_npcs()
        if npcs_data:
            self._npc_indexer.from_dict(npcs_data)

        grounds = self._cache.load_grounds()
        if grounds:
            self._grounds = set(grounds)

        walls = self._cache.load_walls()
        if walls:
            self._walls = set(walls)

        decorations = self._cache.load_decorations()
        if decorations:
            self._decorations = set(decorations)

    def is_loaded(self) -> bool:
        """Check if registry has been loaded."""
        return self._loaded

    def summary(self) -> Dict[str, Any]:
        """Return a summary of indexed assets."""
        return {
            "items": len(self._item_indexer.all_items()),
            "monsters": len(self._monster_indexer.all_monster_names()),
            "npcs": len(self._npc_indexer.all_npc_names()),
            "grounds": len(self._grounds),
            "walls": len(self._walls),
            "decorations": len(self._decorations),
            "cached": self._cache.exists(),
        }