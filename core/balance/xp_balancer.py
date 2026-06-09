from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel
from core.world.spawn import Spawn
from core.world.region import Region
from core.balance.xp_analyzer import XPAnalyzer, XPAnalysis


# Monster XP database (standard Tibia reference values)
MONSTER_XP_DB: Dict[str, int] = {
    "Rat": 20,
    "Spider": 25,
    "Cave Rat": 30,
    "Troll": 50,
    "Orc": 70,
    "Goblin": 50,
    "Skeleton": 100,
    "Dwarf": 120,
    "Lizard": 150,
    "Cyclops": 200,
    "Dragon": 700,
    "Dragon Lord": 2100,
    "Hydra": 1500,
    "Demon": 3000,
    "Demon Oak": 3500,
    "Vampire": 425,
    "Banshee": 1000,
    "Ghoul": 120,
    "Mummy": 400,
    "Giant Spider": 2400,
    "Warlock": 2500,
    "Stone Statue": 900,
    "Nightmare": 1800,
    "Hellfire Fighter": 2500,
    "Diabolic Imp": 1200,
    "Black Knight": 4000,
    "Hero": 3200,
    "Serpent Spawn": 4500,
    "Medusa": 4100,
    "Sea Serpent": 2200,
    "Behemoth": 2800,
    "Eternal Guardian": 3600,
    "Young Sea Serpent": 1100,
    "Worker Golem": 2000,
    "Iron Golem": 5000,
    "Damaged Worker Golem": 1800,
    "Glooth Blob": 1200,
    "Shaburak Demon": 2000,
    "Askara Demon": 3500,
}


@dataclass
class XPAdjustment:
    """Record of a single XP adjustment."""
    zone_name: str
    monster: str
    old_xp: int
    new_xp: int
    multiplier: float
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "monster": self.monster,
            "old_xp": self.old_xp,
            "new_xp": self.new_xp,
            "multiplier": self.multiplier,
            "reason": self.reason,
        }


@dataclass
class XPBalanceResult:
    """Result of XP balancing operation."""
    adjustments: List[XPAdjustment] = field(default_factory=list)
    zones_modified: List[str] = field(default_factory=list)
    total_monsters_adjusted: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adjustments": [a.to_dict() for a in self.adjustments],
            "zones_modified": self.zones_modified,
            "total_monsters_adjusted": self.total_monsters_adjusted,
        }


class XPBalancer:
    """
    Balances XP rates across hunt zones.

    Corrects:
      - XP too high (overpowered leveling zones)
      - XP too low (worthless hunt zones)
      - Inconsistent XP across similar-level zones

    Uses XPAnalyzer to measure current rates, then applies
    multipliers to spawn counts to adjust effective XP/hour.
    """

    TARGET_EFFICIENCY = 60.0  # Target efficiency score (0-100)
    MAX_XP_MULTIPLIER = 3.0
    MIN_XP_MULTIPLIER = 0.2

    def __init__(self):
        self._analyzer = XPAnalyzer()

    def balance(self, world: WorldModel, region: Region,
                monsters: Optional[Dict[str, int]] = None,
                player_level: int = 150) -> XPBalanceResult:
        """
        Balance XP for a region by adjusting spawn composition.

        Args:
            world: WorldModel to modify in-place.
            region: The region to balance.
            monsters: Dict mapping monster name to XP value.
                      If None, uses MONSTER_XP_DB.
            player_level: Target player level.

        Returns:
            XPBalanceResult with all adjustments made.
        """
        result = XPBalanceResult()
        monsters = monsters or MONSTER_XP_DB.copy()

        zone_spawns = self._collect_spawns(world, region)
        if not zone_spawns:
            return result

        spawn_dicts = [{"name": s.monster, "count": 1} for _, _, _, s in zone_spawns]

        analysis = self._analyzer.analyze_zone(region.name, spawn_dicts, monsters)

        multiplier = self._calc_xp_multiplier(analysis, player_level)

        if abs(multiplier - 1.0) < 0.05:
            return result

        adjustments_made = self._apply_xp_adjustment(
            world, region, zone_spawns, monsters, multiplier, result
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

    def _calc_xp_multiplier(self, analysis: XPAnalysis,
                            player_level: int) -> float:
        """Calculate the XP multiplier needed to reach target efficiency."""
        if analysis.efficiency_score == 0:
            return 1.0

        target_efficiency = self.TARGET_EFFICIENCY
        current_efficiency = analysis.efficiency_score

        if current_efficiency >= target_efficiency * 0.9:
            return 1.0

        ratio = target_efficiency / max(current_efficiency, 1)
        multiplier = max(self.MIN_XP_MULTIPLIER, min(self.MAX_XP_MULTIPLIER, ratio))
        return round(multiplier, 2)

    def _apply_xp_adjustment(self, world: WorldModel, region: Region,
                             zone_spawns: List[Tuple[int, int, int, Spawn]],
                             monsters: Dict[str, int],
                             multiplier: float,
                             result: XPBalanceResult) -> int:
        """
        Apply XP adjustments by removing or duplicating spawns.

        If multiplier > 1: duplicate some spawns (add more monsters).
        If multiplier < 1: remove some spawns (fewer monsters).
        """
        adjustments_made = 0

        if multiplier > 1.0:
            # Add extra spawns for each existing spawn
            target_adds = int(len(zone_spawns) * (multiplier - 1.0))
            target_adds = max(1, min(target_adds, len(zone_spawns)))

            tiles_in_region = [t for t in world.tiles.values()
                               if t.zone == region.name and t.spawn is None]

            for i, (x, y, z, spawn) in enumerate(zone_spawns):
                if i >= target_adds:
                    break
                if i < len(tiles_in_region):
                    tile = tiles_in_region[i]
                    new_spawn = Spawn(
                        monster=spawn.monster,
                        respawn=spawn.respawn,
                        radius=spawn.radius,
                    )
                    tile.spawn = new_spawn
                    adjustments_made += 1

                    result.adjustments.append(XPAdjustment(
                        zone_name=region.name,
                        monster=spawn.monster,
                        old_xp=monsters.get(spawn.monster, 0),
                        new_xp=monsters.get(spawn.monster, 0),
                        multiplier=multiplier,
                        reason=f"Added spawn to increase XP (efficiency too low)",
                    ))

        elif multiplier < 1.0:
            # Remove some spawns
            target_remove = int(len(zone_spawns) * (1.0 - multiplier))
            target_remove = max(1, min(target_remove, len(zone_spawns) // 2))

            for i in range(target_remove):
                if i >= len(zone_spawns):
                    break
                x, y, z, spawn = zone_spawns[i]
                tile = world.get_tile(x, y, z)
                if tile is not None:
                    tile.spawn = None
                    adjustments_made += 1

                    result.adjustments.append(XPAdjustment(
                        zone_name=region.name,
                        monster=spawn.monster,
                        old_xp=monsters.get(spawn.monster, 0),
                        new_xp=monsters.get(spawn.monster, 0),
                        multiplier=multiplier,
                        reason=f"Removed spawn to decrease XP (efficiency too high)",
                    ))

        result.total_monsters_adjusted += adjustments_made
        return adjustments_made

    def suggest_monster_replacement(self, current_monster: str,
                                    target_xp: int,
                                    monsters: Optional[Dict[str, int]] = None) -> Optional[str]:
        """
        Suggest a monster replacement to hit a target XP value.

        Args:
            current_monster: Name of the current monster.
            target_xp: Desired XP per kill.
            monsters: Monster XP database.

        Returns:
            Name of the suggested replacement, or None.
        """
        monsters = monsters or MONSTER_XP_DB
        current_xp = monsters.get(current_monster, 0)

        if current_xp == 0:
            return None

        best_match = None
        best_diff = float("inf")

        for name, xp in monsters.items():
            diff = abs(xp - target_xp)
            if diff < best_diff and name != current_monster:
                best_diff = diff
                best_match = name

        return best_match

    def analyze_zone_xp(self, world: WorldModel, region: Region,
                        monsters: Optional[Dict[str, int]] = None,
                        player_level: int = 150) -> XPAnalysis:
        """
        Analyze XP for a region without modifying it.

        Returns:
            XPAnalysis with current XP metrics.
        """
        monsters = monsters or MONSTER_XP_DB
        zone_spawns = self._collect_spawns(world, region)
        spawn_dicts = [{"name": s.monster, "count": 1} for _, _, _, s in zone_spawns]
        return self._analyzer.analyze_zone(region.name, spawn_dicts, monsters)