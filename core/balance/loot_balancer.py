from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel
from core.world.spawn import Spawn
from core.world.region import Region
from core.balance.loot_analyzer import LootAnalyzer, LootAnalysis


# Loot table reference: monster → list of drops
DEFAULT_LOOT_TABLES: Dict[str, List[Dict[str, Any]]] = {
    "Rat": [
        {"id": 3031, "name": "Gold Coin", "chance": 0.8, "value": 100, "count": 1},
    ],
    "Spider": [
        {"id": 3031, "name": "Gold Coin", "chance": 0.6, "value": 100, "count": 1},
        {"id": 3152, "name": "Spider Silk", "chance": 0.15, "value": 500, "count": 1},
    ],
    "Troll": [
        {"id": 3031, "name": "Gold Coin", "chance": 0.7, "value": 100, "count": 2},
        {"id": 3318, "name": "Troll Green", "chance": 0.2, "value": 200, "count": 1},
    ],
    "Dragon": [
        {"id": 3031, "name": "Gold Coin", "chance": 1.0, "value": 100, "count": 8},
        {"id": 3035, "name": "Gold Ingot", "chance": 0.1, "value": 1000, "count": 1},
        {"id": 3066, "name": "Green Dragon Scale", "chance": 0.12, "value": 500, "count": 1},
    ],
    "Dragon Lord": [
        {"id": 3031, "name": "Gold Coin", "chance": 1.0, "value": 100, "count": 20},
        {"id": 3035, "name": "Gold Ingot", "chance": 0.15, "value": 1000, "count": 2},
        {"id": 3066, "name": "Green Dragon Scale", "chance": 0.1, "value": 500, "count": 1},
    ],
    "Demon": [
        {"id": 3031, "name": "Gold Coin", "chance": 1.0, "value": 100, "count": 30},
        {"id": 3035, "name": "Gold Ingot", "chance": 0.2, "value": 1000, "count": 3},
        {"id": 3482, "name": "Demonic Essence", "chance": 0.05, "value": 5000, "count": 1},
    ],
    "Vampire": [
        {"id": 3031, "name": "Gold Coin", "chance": 0.9, "value": 100, "count": 5},
        {"id": 3035, "name": "Gold Ingot", "chance": 0.08, "value": 1000, "count": 1},
        {"id": 3098, "name": "Vampire Leather", "chance": 0.15, "value": 300, "count": 1},
    ],
    "Hydra": [
        {"id": 3031, "name": "Gold Coin", "chance": 1.0, "value": 100, "count": 15},
        {"id": 3035, "name": "Gold Ingot", "chance": 0.12, "value": 1000, "count": 2},
        {"id": 3402, "name": "Hydra Head", "chance": 0.04, "value": 8000, "count": 1},
    ],
    "Giant Spider": [
        {"id": 3031, "name": "Gold Coin", "chance": 1.0, "value": 100, "count": 18},
        {"id": 3035, "name": "Gold Ingot", "chance": 0.1, "value": 1000, "count": 2},
        {"id": 3152, "name": "Spider Silk", "chance": 0.2, "value": 500, "count": 2},
    ],
    "Warlock": [
        {"id": 3031, "name": "Gold Coin", "chance": 1.0, "value": 100, "count": 25},
        {"id": 3035, "name": "Gold Ingot", "chance": 0.18, "value": 1000, "count": 2},
        {"id": 3492, "name": "Wand of Dark Arts", "chance": 0.03, "value": 12000, "count": 1},
    ],
    "Cyclops": [
        {"id": 3031, "name": "Gold Coin", "chance": 0.8, "value": 100, "count": 3},
        {"id": 3035, "name": "Gold Ingot", "chance": 0.05, "value": 1000, "count": 1},
    ],
    "Skeleton": [
        {"id": 3031, "name": "Gold Coin", "chance": 0.6, "value": 100, "count": 2},
    ],
    "Orc": [
        {"id": 3031, "name": "Gold Coin", "chance": 0.5, "value": 100, "count": 1},
    ],
    "Banshee": [
        {"id": 3031, "name": "Gold Coin", "chance": 0.9, "value": 100, "count": 6},
        {"id": 3035, "name": "Gold Ingot", "chance": 0.07, "value": 1000, "count": 1},
    ],
}


@dataclass
class LootAdjustment:
    """Record of a single loot adjustment."""
    zone_name: str
    monster: str
    action: str  # "add_spawn", "remove_spawn", "replace_monster"
    old_value: Any = None
    new_value: Any = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "monster": self.monster,
            "action": self.action,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
        }


@dataclass
class LootBalanceResult:
    """Result of loot balancing operation."""
    adjustments: List[LootAdjustment] = field(default_factory=list)
    zones_modified: List[str] = field(default_factory=list)
    total_adjustments: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adjustments": [a.to_dict() for a in self.adjustments],
            "zones_modified": self.zones_modified,
            "total_adjustments": self.total_adjustments,
        }


class LootBalancer:
    """
    Balances loot economy across hunt zones.

    Corrects:
      - Loot too high (inflation-prone zones)
      - Loot too low (unprofitable zones)
      - Imbalanced profit curves across level brackets

    Uses LootAnalyzer to measure current economy, then adjusts
    spawn composition to reach target profit ranges.
    """

    TARGET_RATING = "balanced"

    def __init__(self):
        self._analyzer = LootAnalyzer()

    def balance(self, world: WorldModel, region: Region,
                monsters: Optional[Dict[str, int]] = None,
                loot_tables: Optional[Dict[str, List[Dict]]] = None,
                target_level: int = 150) -> LootBalanceResult:
        """
        Balance loot for a region.

        Args:
            world: WorldModel to modify in-place.
            region: The region to balance.
            monsters: Monster XP dict (used for zone analysis).
            loot_tables: Loot table dict (monster → drops).
            target_level: Target player level.

        Returns:
            LootBalanceResult with all adjustments made.
        """
        result = LootBalanceResult()
        loot_tables = loot_tables or DEFAULT_LOOT_TABLES

        zone_spawns = self._collect_spawns(world, region)
        if not zone_spawns:
            return result

        spawn_dicts = [{"name": s.monster, "count": 1} for _, _, _, s in zone_spawns]
        difficulties = self._estimate_difficulties(zone_spawns)

        analysis = self._analyzer.analyze_zone(
            region.name, spawn_dicts, loot_tables, difficulties
        )

        adjustment = self._analyzer.suggest_loot_adjustment(analysis, target_level)

        if adjustment.get("adjustment") == "none":
            return result

        loot_multiplier = adjustment.get("loot_multiplier", 1.0)

        adjustments_made = self._apply_loot_adjustment(
            world, region, zone_spawns, loot_tables, loot_multiplier, result
        )

        if adjustments_made > 0:
            result.zones_modified.append(region.name)

        return result

    def _collect_spawns(self, world: WorldModel,
                        region: Region) -> List[Tuple[int, int, int, Spawn]]:
        """Collect spawns in region."""
        spawns: List[Tuple[int, int, int, Spawn]] = []
        for tile in world.tiles.values():
            if tile.zone == region.name and tile.spawn is not None:
                spawns.append((tile.x, tile.y, tile.z, tile.spawn))
        return spawns

    def _estimate_difficulties(self, zone_spawns: List[Tuple[int, int, int, Spawn]]) -> Dict[str, str]:
        """Estimate difficulty tags based on common monsters."""
        difficulty_map: Dict[str, str] = {}
        for _, _, _, spawn in zone_spawns:
            if spawn.monster not in difficulty_map:
                difficulty_map[spawn.monster] = self._guess_difficulty(spawn.monster)
        return difficulty_map

    def _guess_difficulty(self, monster: str) -> str:
        """Guess difficulty tier for a monster."""
        easy_monsters = {"Rat", "Spider", "Cave Rat", "Troll", "Orc", "Goblin", "Skeleton"}
        medium_monsters = {"Cyclops", "Lizard", "Dwarf", "Ghoul", "Mummy", "Vampire", "Banshee"}
        hard_monsters = {"Dragon", "Hydra", "Giant Spider", "Warlock", "Nightmare", "Sea Serpent"}
        very_hard_monsters = {"Dragon Lord", "Demon", "Black Knight", "Serpent Spawn", "Medusa", "Behemoth"}

        if monster in easy_monsters:
            return "easy"
        elif monster in medium_monsters:
            return "medium"
        elif monster in hard_monsters:
            return "hard"
        elif monster in very_hard_monsters:
            return "very_hard"
        return "medium"

    def _apply_loot_adjustment(self, world: WorldModel, region: Region,
                               zone_spawns: List[Tuple[int, int, int, Spawn]],
                               loot_tables: Dict[str, List[Dict]],
                               loot_multiplier: float,
                               result: LootBalanceResult) -> int:
        """
        Apply loot adjustments by changing spawn composition.

        If loot is too low: add spawns of more profitable monsters.
        If loot is too high: remove spawns or replace with less profitable ones.
        """
        adjustments_made = 0

        if loot_multiplier > 1.2:
            target_adds = min(int(len(zone_spawns) * (loot_multiplier - 1.0)), 5)
            profitable = self._find_more_profitable_monsters(zone_spawns, loot_tables)

            empty_tiles = [t for t in world.tiles.values()
                           if t.zone == region.name and t.spawn is None]

            for i in range(min(target_adds, len(empty_tiles), len(profitable))):
                tile = empty_tiles[i]
                monster = profitable[i % len(profitable)]
                new_spawn = Spawn(monster=monster, respawn=60, radius=5)
                tile.spawn = new_spawn
                adjustments_made += 1

                result.adjustments.append(LootAdjustment(
                    zone_name=region.name,
                    monster=monster,
                    action="add_spawn",
                    old_value=None,
                    new_value=new_spawn.to_dict(),
                    reason=f"Zone profit too low (multiplier={loot_multiplier})",
                ))

        elif loot_multiplier < 0.8:
            target_remove = min(int(len(zone_spawns) * (1.0 - loot_multiplier)), 3)
            target_remove = max(1, target_remove)

            for i in range(target_remove):
                if i >= len(zone_spawns):
                    break
                x, y, z, spawn = zone_spawns[i]
                tile = world.get_tile(x, y, z)
                if tile is not None:
                    tile.spawn = None
                    adjustments_made += 1

                    result.adjustments.append(LootAdjustment(
                        zone_name=region.name,
                        monster=spawn.monster,
                        action="remove_spawn",
                        old_value=spawn.to_dict(),
                        new_value=None,
                        reason=f"Zone profit too high (multiplier={loot_multiplier})",
                    ))

        result.total_adjustments += adjustments_made
        return adjustments_made

    def _find_more_profitable_monsters(self, zone_spawns: List[Tuple[int, int, int, Spawn]],
                                       loot_tables: Dict[str, List[Dict]]) -> List[str]:
        """Find monsters not in the zone that would increase profit."""
        current_monsters = {s.monster for _, _, _, s in zone_spawns}
        candidates = ["Demon", "Dragon Lord", "Warlock", "Serpent Spawn",
                       "Hydra", "Giant Spider", "Black Knight"]
        return [m for m in candidates if m not in current_monsters]

    def analyze_zone_loot(self, world: WorldModel, region: Region,
                          loot_tables: Optional[Dict[str, List[Dict]]] = None,
                          target_level: int = 150) -> LootAnalysis:
        """
        Analyze loot for a region without modifying it.

        Returns:
            LootAnalysis with current economy metrics.
        """
        loot_tables = loot_tables or DEFAULT_LOOT_TABLES
        zone_spawns = self._collect_spawns(world, region)
        spawn_dicts = [{"name": s.monster, "count": 1} for _, _, _, s in zone_spawns]
        difficulties = self._estimate_difficulties(zone_spawns)
        return self._analyzer.analyze_zone(
            region.name, spawn_dicts, loot_tables, difficulties
        )