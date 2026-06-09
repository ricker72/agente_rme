from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel
from core.world.spawn import Spawn
from core.world.region import Region
from core.balance.difficulty_analyzer import DifficultyAnalyzer, DifficultyAnalysis


# Monster difficulty classification
MONSTER_DIFFICULTY_MAP: Dict[str, str] = {
    "Rat": "easy", "Spider": "easy", "Cave Rat": "easy",
    "Troll": "easy", "Orc": "easy", "Goblin": "easy",
    "Skeleton": "easy", "Dwarf": "medium", "Lizard": "medium",
    "Cyclops": "medium", "Ghoul": "medium",
    "Dragon": "hard", "Hydra": "hard", "Giant Spider": "hard",
    "Warlock": "hard", "Nightmare": "hard", "Vampire": "medium",
    "Banshee": "medium", "Mummy": "medium", "Sea Serpent": "hard",
    "Dragon Lord": "very_hard", "Demon": "very_hard",
    "Black Knight": "very_hard", "Serpent Spawn": "very_hard",
    "Medusa": "very_hard", "Behemoth": "hard",
    "Eternal Guardian": "very_hard", "Hero": "very_hard",
    "Iron Golem": "very_hard", "Hellfire Fighter": "hard",
    "Diabolic Imp": "hard",
}

# Difficulty tier hierarchy
DIFFICULTY_TIERS = ["easy", "medium", "hard", "very_hard", "boss"]


@dataclass
class DifficultyAdjustment:
    """Record of a single difficulty adjustment."""
    zone_name: str
    monster: str
    action: str  # "downgrade", "upgrade", "remove", "add"
    old_difficulty: str = ""
    new_difficulty: str = ""
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "monster": self.monster,
            "action": self.action,
            "old_difficulty": self.old_difficulty,
            "new_difficulty": self.new_difficulty,
            "reason": self.reason,
        }


@dataclass
class DifficultyBalanceResult:
    """Result of difficulty balancing operation."""
    adjustments: List[DifficultyAdjustment] = field(default_factory=list)
    zones_modified: List[str] = field(default_factory=list)
    bosses_corrected: int = 0
    trivial_corrected: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "adjustments": [a.to_dict() for a in self.adjustments],
            "zones_modified": self.zones_modified,
            "bosses_corrected": self.bosses_corrected,
            "trivial_corrected": self.trivial_corrected,
        }


# Mapping of difficulty tiers to replacement monsters
TIER_REPLACEMENTS: Dict[str, List[str]] = {
    "easy_to_medium": ["Cyclops", "Lizard", "Dwarf"],
    "medium_to_hard": ["Dragon", "Hydra", "Giant Spider", "Warlock"],
    "hard_to_easy": ["Troll", "Orc", "Cyclops"],
    "very_hard_to_hard": ["Dragon", "Hydra", "Giant Spider", "Warlock", "Behemoth"],
    "hard_to_medium": ["Vampire", "Banshee", "Cyclops", "Lizard"],
}


class DifficultyBalancer:
    """
    Balances difficulty across hunt zones.

    Corrects:
      - Bosses that are impossible (death_chance > 0.5)
      - Bosses that are trivial (score < 10)
      - Zones with extreme difficulty spikes
      - Mixed difficulty in same zone

    Uses DifficultyAnalyzer to measure, then adjusts
    monster types in spawns to reach balanced difficulty.
    """

    TARGET_DIFFICULTY_SCORE = 45.0  # Target zone difficulty (0-100)
    MAX_DEATH_CHANCE = 0.15
    MIN_DIFFICULTY_SCORE = 15.0

    def __init__(self):
        self._analyzer = DifficultyAnalyzer()

    def balance(self, world: WorldModel, region: Region,
                player_level: int = 150) -> DifficultyBalanceResult:
        """
        Balance difficulty for a region.

        Args:
            world: WorldModel to modify in-place.
            region: The region to balance.
            player_level: Target player level.

        Returns:
            DifficultyBalanceResult with all adjustments made.
        """
        result = DifficultyBalanceResult()

        zone_spawns = self._collect_spawns(world, region)
        if not zone_spawns:
            return result

        spawn_dicts = [{"name": s.monster, "count": 1} for _, _, _, s in zone_spawns]
        difficulties = self._get_difficulty_map(zone_spawns)

        analysis = self._analyzer.analyze_zone(
            region.name, spawn_dicts, difficulties, player_level
        )

        # Handle impossible zones
        if analysis.has_deadly_zones or analysis.overall_score > 75:
            self._downgrade_deadly_monsters(world, region, analysis, difficulties, result)

        # Handle trivial zones
        elif analysis.has_too_easy_zones and analysis.overall_score < 15:
            self._upgrade_trivial_monsters(world, region, analysis, difficulties, result)

        # Handle mixed difficulty
        elif analysis.difficulty_spread > 40:
            self._normalize_spread(world, region, analysis, difficulties, result)

        if len(result.adjustments) > 0:
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

    def _get_difficulty_map(self, zone_spawns: List[Tuple[int, int, int, Spawn]]) -> Dict[str, str]:
        """Get difficulty map for monsters in zone."""
        diff_map: Dict[str, str] = {}
        for _, _, _, spawn in zone_spawns:
            if spawn.monster not in diff_map:
                diff_map[spawn.monster] = MONSTER_DIFFICULTY_MAP.get(spawn.monster, "medium")
        return diff_map

    def _downgrade_deadly_monsters(self, world: WorldModel, region: Region,
                                   analysis: DifficultyAnalysis,
                                   difficulties: Dict[str, str],
                                   result: DifficultyBalanceResult) -> None:
        """Replace deadly monsters with easier alternatives."""
        for monster_name, profile in analysis.monster_profiles.items():
            if profile.rating in ("impossible", "deadly"):
                current_diff = difficulties.get(monster_name, "medium")
                new_diff = self._lower_tier(current_diff)

                replacement = self._find_replacement(monster_name, current_diff, new_diff)
                if replacement:
                    self._replace_monster_in_world(world, region.name, monster_name, replacement)
                    result.adjustments.append(DifficultyAdjustment(
                        zone_name=region.name,
                        monster=monster_name,
                        action="downgrade",
                        old_difficulty=current_diff,
                        new_difficulty=new_diff,
                        reason=f"Monster rated '{profile.rating}' (score={profile.difficulty_score:.0f})",
                    ))
                    result.bosses_corrected += 1

    def _upgrade_trivial_monsters(self, world: WorldModel, region: Region,
                                  analysis: DifficultyAnalysis,
                                  difficulties: Dict[str, str],
                                  result: DifficultyBalanceResult) -> None:
        """Replace trivial monsters with harder alternatives."""
        for monster_name, profile in analysis.monster_profiles.items():
            if profile.rating == "trivial":
                current_diff = difficulties.get(monster_name, "easy")
                new_diff = self._raise_tier(current_diff)

                replacement = self._find_replacement(monster_name, current_diff, new_diff)
                if replacement:
                    self._replace_monster_in_world(world, region.name, monster_name, replacement)
                    result.adjustments.append(DifficultyAdjustment(
                        zone_name=region.name,
                        monster=monster_name,
                        action="upgrade",
                        old_difficulty=current_diff,
                        new_difficulty=new_diff,
                        reason=f"Monster rated 'trivial' (score={profile.difficulty_score:.0f})",
                    ))
                    result.trivial_corrected += 1

    def _normalize_spread(self, world: WorldModel, region: Region,
                          analysis: DifficultyAnalysis,
                          difficulties: Dict[str, str],
                          result: DifficultyBalanceResult) -> None:
        """Normalize difficulty spread by upgrading the weakest monsters."""
        for monster_name, profile in analysis.monster_profiles.items():
            if profile.rating in ("trivial", "easy") and analysis.avg_difficulty > 35:
                current_diff = difficulties.get(monster_name, "easy")
                new_diff = self._raise_tier(current_diff)

                replacement = self._find_replacement(monster_name, current_diff, new_diff)
                if replacement:
                    self._replace_monster_in_world(world, region.name, monster_name, replacement)
                    result.adjustments.append(DifficultyAdjustment(
                        zone_name=region.name,
                        monster=monster_name,
                        action="upgrade",
                        old_difficulty=current_diff,
                        new_difficulty=new_diff,
                        reason=f"Normalizing spread (avg={analysis.avg_difficulty:.0f})",
                    ))

    def _replace_monster_in_world(self, world: WorldModel, zone_name: str,
                                  old_monster: str, new_monster: str) -> int:
        """Replace all instances of a monster in a zone."""
        count = 0
        for tile in world.tiles.values():
            if tile.zone == zone_name and tile.spawn is not None:
                if tile.spawn.monster == old_monster:
                    tile.spawn.monster = new_monster
                    count += 1
        return count

    def _find_replacement(self, current_monster: str,
                          current_diff: str, target_diff: str) -> Optional[str]:
        """Find a replacement monster at the target difficulty."""
        key = f"{current_diff}_to_{target_diff}"
        candidates = TIER_REPLACEMENTS.get(key, [])

        if not candidates:
            # Try direct tier mapping
            if target_diff == "medium":
                candidates = ["Cyclops", "Vampire", "Banshee", "Lizard"]
            elif target_diff == "hard":
                candidates = ["Dragon", "Hydra", "Giant Spider", "Warlock"]
            elif target_diff == "easy":
                candidates = ["Troll", "Orc", "Spider", "Skeleton"]

        # Avoid recommending the same monster
        candidates = [m for m in candidates if m != current_monster]
        return candidates[0] if candidates else None

    def _lower_tier(self, current: str) -> str:
        """Get one tier lower."""
        idx = DIFFICULTY_TIERS.index(current) if current in DIFFICULTY_TIERS else 2
        return DIFFICULTY_TIERS[max(0, idx - 1)]

    def _raise_tier(self, current: str) -> str:
        """Get one tier higher."""
        idx = DIFFICULTY_TIERS.index(current) if current in DIFFICULTY_TIERS else 1
        return DIFFICULTY_TIERS[min(len(DIFFICULTY_TIERS) - 1, idx + 1)]

    def analyze_zone_difficulty(self, world: WorldModel, region: Region,
                                player_level: int = 150) -> DifficultyAnalysis:
        """
        Analyze difficulty for a region without modifying it.

        Returns:
            DifficultyAnalysis with current difficulty metrics.
        """
        zone_spawns = self._collect_spawns(world, region)
        spawn_dicts = [{"name": s.monster, "count": 1} for _, _, _, s in zone_spawns]
        difficulties = self._get_difficulty_map(zone_spawns)
        return self._analyzer.analyze_zone(
            region.name, spawn_dicts, difficulties, player_level
        )