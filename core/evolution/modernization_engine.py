from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MapVersion(Enum):
    V8_6 = "8.6"
    V10_X = "10.x"
    V12_X = "12.x"
    V13_X = "13.x"
    V14_X = "14.x"
    CUSTOM = "custom"


@dataclass
class ModernizationReport:
    original_version: MapVersion
    target_version: str
    changes_applied: List[str] = field(default_factory=list)
    items_updated: int = 0
    spawns_updated: int = 0
    tiles_reformatted: int = 0
    warnings: List[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_version": self.original_version.value,
            "target_version": self.target_version,
            "changes_applied": self.changes_applied,
            "items_updated": self.items_updated,
            "spawns_updated": self.spawns_updated,
            "tiles_reformatted": self.tiles_reformatted,
            "warnings": self.warnings,
            "summary": self.summary,
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class ModernizationEngine:
    """
    Updates legacy Tibia maps (8.6, 10.x, etc.) to modern standards.

    Capabilities:
      - Item ID migration (8.6 → 13.x/14.x mapping)
      - Monster name normalization across versions
      - Tile flag modernization (PZ, no-logout, etc.)
      - OTBM header version bump
      - Ground and wall sprite ID updating
      - Spawn format conversion (old radius-based → modern)
      - Deprecated item removal / replacement
      - Map structure normalization
    """

    # Version-specific OTBM version numbers
    OTBM_VERSIONS = {
        MapVersion.V8_6: 2,
        MapVersion.V10_X: 3,
        MapVersion.V12_X: 3,
        MapVersion.V13_X: 4,
        MapVersion.V14_X: 4,
    }

    # Item ID migration map: old IDs (8.6/10.x) → modern IDs (13.x+)
    # These are commonly-changed item IDs between versions
    ITEM_MIGRATION = {
        # Ground tiles
        101: 102,  # old dirt → new dirt
        103: 103,  # grass (unchanged but verified)
        231: 231,  # cobblestone
        1284: 1284,  # stone
        1294: 1294,  # gravel
        # Walls
        1000: 1126,  # old stone wall → new stone wall
        1002: 1127,  # old wooden wall → new wooden wall
        398: 398,  # cave wall
        # Decorations
        1447: 1447,  # torch (preserved)
        2050: 2050,  # wall torch
        2052: 2052,  # wall torch variant
        # Containers
        1740: 1740,  # chest
        1753: 1753,  # large chest
        1764: 1764,  # box
        # Furniture
        1770: 1770,  # table
        1779: 1779,  # chair
        1786: 1786,  # bed
        1775: 1775,  # barrel
        1738: 1738,  # crate
        # Nature
        1304: 1304,  # small stone
        2705: 2705,  # bush
        2104: 2104,  # flower
        1499: 1499,  # fern
        1507: 1507,  # mushroom
        # Statues & Pillars
        1510: 1510,  # statue
        1545: 1545,  # pillar
        # Special
        1386: 1386,  # ladder
        # Old deprecated items that should be replaced
        104: 102,  # old soil → dirt
        105: 103,  # old grass tile → grass
        106: 231,  # old pavement → cobblestone
        400: 398,  # old cave wall → cave wall
        401: 398,  # old underground wall → cave wall
        430: 1284,  # old stone floor → stone
    }

    # Monster name migrations across versions
    MONSTER_MIGRATION = {
        # Renamed monsters
        "Rat": "Rat",
        "Cave Rat": "Cave Rat",
        "Troll": "Troll",
        "Orc": "Orc",
        "Orc Warrior": "Orc Warrior",
        "Orc Berserker": "Orc Berserker",
        "Minotaur": "Minotaur",
        "Minotaur Guard": "Minotaur Guard",
        "Minotaur Mage": "Minotaur Mage",
        "Cyclops": "Cyclops",
        "Cyclops Drone": "Cyclops Drone",
        "Cyclops Smith": "Cyclops Smith",
        "Dragon": "Dragon",
        "Dragon Lord": "Dragon Lord",
        "Dwarf": "Dwarf",
        "Dwarf Soldier": "Dwarf Soldier",
        "Dwarf Guard": "Dwarf Guard",
        "Dwarf Geomancer": "Dwarf Geomancer",
        "Hydra": "Hydra",
        "Serpent Spawn": "Serpent Spawn",
        "Behemoth": "Behemoth",
        "Hero": "Hero",
        "Necromancer": "Necromancer",
        "Demon": "Demon",
        "Demon Skeleton": "Demon Skeleton",
        "Fire Elemental": "Fire Elemental",
        "Fire Devil": "Fire Devil",
        # 8.6 → modern renames
        "Orc Spearman": "Orc Spearman",
        "Orc Shaman": "Orc Shaman",
        "Orc Leader": "Orc Leader",
        "Orc Warlord": "Orc Warlord",
        "Rotworm": "Rotworm",
        "Carrion Worm": "Carrion Worm",
        "Larva": "Larva",
        "Scarab": "Scarab",
        "Ancient Scarab": "Ancient Scarab",
        "Giant Spider": "Giant Spider",
        "Tarantula": "Tarantula",
        "Wasp": "Wasp",
        "Poison Spider": "Poison Spider",
        "Spider": "Spider",
        "Crocodile": "Crocodile",
        "Blood Crab": "Blood Crab",
        "Crab": "Crab",
        "Tortoise": "Tortoise",
        "Thornback Tortoise": "Thornback Tortoise",
        "Skeleton": "Skeleton",
        "Ghoul": "Ghoul",
        "Mummy": "Mummy",
        "Vampire": "Vampire",
        "Ghost": "Ghost",
        "Lich": "Lich",
        "Warlock": "Warlock",
        "Black Knight": "Black Knight",
        "Monk": "Monk",
        "Dark Monk": "Dark Monk",
        "Priestess": "Priestess",
        "Witch": "Witch",
        "Amazon": "Amazon",
        "Valkyrie": "Valkyrie",
        "Hunter": "Hunter",
        "Poacher": "Poacher",
        "Wild Warrior": "Wild Warrior",
        "Assassin": "Assassin",
        "Bandit": "Bandit",
        "Smuggler": "Smuggler",
        "Pirate Marauder": "Pirate Marauder",
        "Pirate Corsair": "Pirate Corsair",
        "Pirate Cutthroat": "Pirate Cutthroat",
        "Pirate Buccaneer": "Pirate Buccaneer",
        # Bosses
        "Ferumbras": "Ferumbras",
        "Orshabaal": "Orshabaal",
        "Morgaroth": "Morgaroth",
        "Ghazbaran": "Ghazbaran",
        "Demodras": "Demodras",
        "The Old Widow": "The Old Widow",
        "Zugurosh": "Zugurosh",
        "The Horned Fox": "The Horned Fox",
        "General Murius": "General Murius",
        "The Evil Eye": "The Evil Eye",
        "The Blightfather": "The Blightfather",
        "Countess Sorrow": "Countess Sorrow",
        "Dracola": "Dracola",
        "Mr. Punish": "Mr. Punish",
        "The Handmaiden": "The Handmaiden",
        "The Imperor": "The Imperor",
        "Massacre": "Massacre",
        "The Plasmother": "The Plasmother",
        "Shlorg": "Shlorg",
        "Zoralurk": "Zoralurk",
        "Furyosa": "Furyosa",
    }

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def modernize(
        self,
        otbm_data: Dict[str, Any],
        from_version: Optional[MapVersion] = None,
        to_version: str = "14.x",
    ) -> tuple:
        """
        Modernize an OTBM map from an older version to a modern standard.

        Args:
            otbm_data: Deserialized OTBM structure.
            from_version: Source version. Auto-detected if None.
            to_version: Target version string (e.g., '13.x', '14.x').

        Returns:
            Tuple of (modernized_data, ModernizationReport).
        """
        if from_version is None:
            from_version = self._detect_version(otbm_data)

        report = ModernizationReport(
            original_version=from_version,
            target_version=to_version,
        )

        data = otbm_data

        # Apply migrations in order
        data = self._migrate_items(data, report)
        data = self._migrate_monsters(data, report)
        data = self._migrate_tile_flags(data, report, from_version)
        data = self._update_otbm_header(data, report, to_version)
        data = self._remove_deprecated_items(data, report)
        data = self._normalize_spawn_structure(data, report)

        report.summary = (
            f"Modernización {from_version.value} → {to_version}: "
            f"{report.items_updated} items actualizados, "
            f"{report.spawns_updated} spawns actualizados, "
            f"{report.tiles_reformatted} tiles reformateados. "
            f"{len(report.warnings)} advertencias."
        )

        return data, report

    def detect_version(self, otbm_data: Dict[str, Any]) -> MapVersion:
        """Detect the map version from OTBM data."""
        return self._detect_version(otbm_data)

    # ------------------------------------------------------------------
    # Version detection
    # ------------------------------------------------------------------

    def _detect_version(self, otbm_data: Dict[str, Any]) -> MapVersion:
        """Auto-detect the source map version."""
        # Check OTBM header version
        otbm_version = otbm_data.get("otbm_version", otbm_data.get("version", 2))
        client_version = otbm_data.get("client_version", 860)

        if client_version >= 1400 or otbm_version >= 4:
            return MapVersion.V14_X
        elif client_version >= 1300:
            return MapVersion.V13_X
        elif client_version >= 1200:
            return MapVersion.V12_X
        elif client_version >= 1000:
            return MapVersion.V10_X
        elif client_version >= 860:
            return MapVersion.V8_6

        return MapVersion.V8_6  # Default to oldest handled

    # ------------------------------------------------------------------
    # Item migration
    # ------------------------------------------------------------------

    def _migrate_items(
        self, data: Dict[str, Any], report: ModernizationReport
    ) -> Dict[str, Any]:
        """Migrate item IDs from old to modern standards."""
        tiles = self._get_tiles(data)
        updated = 0

        for tile in tiles:
            for item in tile.get("items", []):
                old_id = item.get("id", 0)
                if old_id in self.ITEM_MIGRATION:
                    new_id = self.ITEM_MIGRATION[old_id]
                    if old_id != new_id:
                        item["id"] = new_id
                        updated += 1

        if updated > 0:
            report.changes_applied.append(
                f"Migrados {updated} item IDs a versiones modernas"
            )
        report.items_updated += updated

        return self._set_tiles(data, tiles)

    # ------------------------------------------------------------------
    # Monster migration
    # ------------------------------------------------------------------

    def _migrate_monsters(
        self, data: Dict[str, Any], report: ModernizationReport
    ) -> Dict[str, Any]:
        """Migrate monster names to modern naming conventions."""
        spawns = self._get_spawns(data)
        updated = 0

        for spawn in spawns:
            for monster in spawn.get("monsters", []):
                old_name = monster.get("name", "")
                if old_name in self.MONSTER_MIGRATION:
                    new_name = self.MONSTER_MIGRATION[old_name]
                    if old_name != new_name:
                        monster["name"] = new_name
                        updated += 1

        if updated > 0:
            report.changes_applied.append(
                f"Actualizados {updated} nombres de monstruos"
            )
        report.spawns_updated += updated

        return self._set_spawns(data, spawns)

    # ------------------------------------------------------------------
    # Tile flag migration
    # ------------------------------------------------------------------

    def _migrate_tile_flags(
        self,
        data: Dict[str, Any],
        report: ModernizationReport,
        from_version: MapVersion,
    ) -> Dict[str, Any]:
        """Migrate tile flags to modern standard values."""
        tiles = self._get_tiles(data)
        reformatted = 0

        for tile in tiles:
            old_flags = tile.get("flags", 0)

            # 8.6 used different flag bitmasks in some cases
            if from_version in (MapVersion.V8_6, MapVersion.V10_X):
                new_flags = self._convert_flags_v86(old_flags)
                if new_flags != old_flags:
                    tile["flags"] = new_flags
                    reformatted += 1

        if reformatted > 0:
            report.changes_applied.append(
                f"Reformateados {reformatted} tiles con flags modernos"
            )
        report.tiles_reformatted += reformatted

        return self._set_tiles(data, tiles)

    def _convert_flags_v86(self, flags: int) -> int:
        """Convert 8.6 flag bitmask to modern equivalent."""
        # Protection zone mapping
        result = 0
        if flags & 1:  # PZ in 8.6
            result |= 1  # TILESTATE_PROTECTIONZONE
        if flags & 2:  # NoLogout in 8.6
            result |= 4  # TILESTATE_NOLOGOUT
        if flags & 4:  # PvP zone in 8.6
            result |= 8  # TILESTATE_PVPZONE
        if flags & 8:  # NoPvP zone in 8.6
            result |= 2  # TILESTATE_NOPVPZONE
        if flags & 16:  # Refresh in 8.6
            result |= 32  # TILESTATE_REFRESH
        if flags & 64:  # Trashed / blocked
            result |= 64

        return result

    # ------------------------------------------------------------------
    # Header update
    # ------------------------------------------------------------------

    def _update_otbm_header(
        self, data: Dict[str, Any], report: ModernizationReport, to_version: str
    ) -> Dict[str, Any]:
        """Update the OTBM header version information."""
        target_otbm = 4  # Default modern

        if "13.x" in to_version:
            target_otbm = 4
        elif "12.x" in to_version:
            target_otbm = 3
        elif "14.x" in to_version:
            target_otbm = 4

        old_otbm = data.get("otbm_version", data.get("version", 2))
        data["otbm_version"] = target_otbm
        data["version"] = target_otbm

        if old_otbm != target_otbm:
            report.changes_applied.append(
                f"OTBM header actualizado: v{old_otbm} → v{target_otbm}"
            )

        # Update client version if present
        if "14.x" in to_version:
            data["client_version"] = 1440
        elif "13.x" in to_version:
            data["client_version"] = 1340
        elif "12.x" in to_version:
            data["client_version"] = 1220

        return data

    # ------------------------------------------------------------------
    # Deprecated item removal
    # ------------------------------------------------------------------

    def _remove_deprecated_items(
        self, data: Dict[str, Any], report: ModernizationReport
    ) -> Dict[str, Any]:
        """Remove or replace items that no longer exist in modern versions."""
        # Known deprecated item IDs
        deprecated_ids = {
            104,
            105,
            106,
            400,
            401,
            430,
        }  # Already mapped in ITEM_MIGRATION

        tiles = self._get_tiles(data)
        removed = 0

        for tile in tiles:
            original_items = tile.get("items", [])
            filtered_items = []
            for item in original_items:
                item_id = item.get("id", 0)
                if item_id in deprecated_ids:
                    removed += 1
                else:
                    filtered_items.append(item)
            tile["items"] = filtered_items

        if removed > 0:
            report.changes_applied.append(f"Eliminados {removed} items deprecados")
        report.items_updated += removed

        return self._set_tiles(data, tiles)

    # ------------------------------------------------------------------
    # Spawn structure normalization
    # ------------------------------------------------------------------

    def _normalize_spawn_structure(
        self, data: Dict[str, Any], report: ModernizationReport
    ) -> Dict[str, Any]:
        """Normalize spawn data to modern format."""
        spawns = self._get_spawns(data)
        normalized = 0

        for spawn in spawns:
            # Ensure monsters is a list of dicts with standard keys
            monsters = spawn.get("monsters", [])
            if isinstance(monsters, list):
                new_monsters = []
                for m in monsters:
                    if isinstance(m, str):
                        new_monsters.append({"name": m, "count": 1})
                        normalized += 1
                    elif isinstance(m, dict):
                        # Ensure standard keys exist
                        m.setdefault("count", 1)
                        if "name" not in m and "monster" in m:
                            m["name"] = m.pop("monster")
                            normalized += 1
                    new_monsters.append(m)
                spawn["monsters"] = new_monsters

            # Normalize spawn area radius
            if "spawn_radius" in spawn:
                spawn["radius"] = spawn.pop("spawn_radius")
                normalized += 1
            spawn.setdefault("radius", 8)

            # Normalize position format
            pos = spawn.get("center_position", spawn.get("position"))
            if pos is not None:
                if len(pos) == 2:
                    spawn["center_position"] = (pos[0], pos[1], 7)
                    normalized += 1
                elif len(pos) == 3:
                    spawn["center_position"] = tuple(pos)

        if normalized > 0:
            report.changes_applied.append(
                f"Normalizados {normalized} elementos de spawn"
            )
        report.spawns_updated += normalized

        return self._set_spawns(data, spawns)

    # ------------------------------------------------------------------
    # Additional modernizations
    # ------------------------------------------------------------------

    def add_modern_features(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add modern features that old maps typically lack:
        - Proper town temple markers
        - Depot tile markers
        - Modern waypoint format
        """
        self._get_tiles(data)
        map_data = data.get("map_data", data)

        # Ensure towns have proper structure
        towns = map_data.get("towns", [])
        for town in towns:
            if "temple_position" not in town and "position" in town:
                pos = town["position"]
                town["temple_position"] = (
                    pos[0],
                    pos[1],
                    pos[2] if len(pos) > 2 else 7,
                )
            town.setdefault("name", f"Town_{id(town)}")

        # Add waypoints if missing
        if "waypoints" not in map_data:
            map_data["waypoints"] = []

        return data

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_tiles(self, data: Dict[str, Any]) -> List[Dict]:
        map_data = data.get("map_data", data)
        return map_data.get("tiles", [])

    def _set_tiles(self, data: Dict[str, Any], tiles: List[Dict]) -> Dict[str, Any]:
        if "map_data" in data:
            data["map_data"]["tiles"] = tiles
        else:
            data["tiles"] = tiles
        return data

    def _get_spawns(self, data: Dict[str, Any]) -> List[Dict]:
        map_data = data.get("map_data", data)
        return map_data.get("spawns", [])

    def _set_spawns(self, data: Dict[str, Any], spawns: List[Dict]) -> Dict[str, Any]:
        if "map_data" in data:
            data["map_data"]["spawns"] = spawns
        else:
            data["spawns"] = spawns
        return data
