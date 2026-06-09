from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.world.world_model import WorldModel
from core.world.spawn import Spawn
from core.world.region import Region


@dataclass
class RiskAssessment:
    """Risk profile for a zone."""
    zone_name: str = ""
    risk_score: float = 0.0  # 0-100 (0=safe, 100=lethal)
    risk_level: str = ""  # "safe", "low", "medium", "high", "extreme"
    death_probability: float = 0.0
    supply_drain_rate: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "death_probability": self.death_probability,
            "supply_drain_rate": self.supply_drain_rate,
            "risk_factors": self.risk_factors,
            "recommendations": self.recommendations,
        }


@dataclass
class RiskAdjustment:
    """Record of a single risk adjustment."""
    zone_name: str
    action: str  # "reduce_density", "add_safe_zone", "adjust_spawn"
    old_value: Any = None
    new_value: Any = None
    reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "action": self.action,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "reason": self.reason,
        }


@dataclass
class RiskBalanceResult:
    """Result of risk balancing operation."""
    assessments: List[RiskAssessment] = field(default_factory=list)
    adjustments: List[RiskAdjustment] = field(default_factory=list)
    zones_modified: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessments": [a.to_dict() for a in self.assessments],
            "adjustments": [a.to_dict() for a in self.adjustments],
            "zones_modified": self.zones_modified,
        }


# Monster danger ratings
MONSTER_DANGER: Dict[str, float] = {
    "Rat": 5, "Spider": 5, "Cave Rat": 5,
    "Troll": 10, "Orc": 10, "Goblin": 8, "Skeleton": 12,
    "Dwarf": 15, "Lizard": 18, "Cyclops": 22, "Ghoul": 14,
    "Mummy": 20, "Vampire": 28,
    "Dragon": 45, "Hydra": 50, "Giant Spider": 48,
    "Warlock": 55, "Nightmare": 52, "Banshee": 30,
    "Sea Serpent": 42,
    "Dragon Lord": 75, "Demon": 85, "Black Knight": 80,
    "Serpent Spawn": 82, "Medusa": 80, "Behemoth": 65,
    "Eternal Guardian": 78, "Hero": 72, "Iron Golem": 90,
    "Hellfire Fighter": 60, "Diabolic Imp": 55,
}


class RiskBalancer:
    """
    Assesses and balances risk profiles across hunt zones.

    Corrects:
      - Zones with extreme death probability
      - Unbalanced risk/reward ratios
      - Zones too dangerous for their intended level range
      - Missing safe areas in dangerous zones
    """

    TARGET_RISK_SCORE = 40.0
    MAX_RISK_SCORE = 70.0
    MIN_RISK_SCORE = 10.0
    MAX_DEATH_PROBABILITY = 0.2

    def balance(self, world: WorldModel, region: Region,
                player_level: int = 150) -> RiskBalanceResult:
        """
        Assess and balance risk for a region.

        Args:
            world: WorldModel to modify in-place.
            region: The region to balance.
            player_level: Target player level.

        Returns:
            RiskBalanceResult with assessments and adjustments.
        """
        result = RiskBalanceResult()

        assessment = self._assess_risk(world, region, player_level)
        result.assessments.append(assessment)

        if assessment.risk_score > self.MAX_RISK_SCORE:
            self._reduce_risk(world, region, assessment, result)
        elif assessment.risk_score < self.MIN_RISK_SCORE:
            self._increase_risk_interest(world, region, assessment, result)

        return result

    def _assess_risk(self, world: WorldModel, region: Region,
                     player_level: int) -> RiskAssessment:
        """Calculate risk profile for a zone."""
        zone_spawns = self._collect_spawns(world, region)
        total_danger = 0.0
        spawn_count = len(zone_spawns)
        risk_factors: List[str] = []
        recommendations: List[str] = []

        for _, _, _, spawn in zone_spawns:
            danger = MONSTER_DANGER.get(spawn.monster, 25)
            total_danger += danger

        avg_danger = total_danger / max(spawn_count, 1)

        # Scale risk by player level
        level_factor = max(0.5, 2.0 - player_level / 300)
        risk_score = min(100, avg_danger * level_factor * (1 + spawn_count * 0.02))

        # Death probability estimation
        death_prob = min(1.0, risk_score / 150)

        # Supply drain estimation
        supply_drain = spawn_count * avg_danger * 0.1

        # Risk factors
        if spawn_count > 10:
            risk_factors.append("High spawn density")
        if avg_danger > 50:
            risk_factors.append("Dangerous monster types")
        if death_prob > 0.3:
            risk_factors.append("High death probability")
        if supply_drain > 200:
            risk_factors.append("High supply consumption")

        # Recommendations
        if risk_score > self.MAX_RISK_SCORE:
            recommendations.append("Reduce spawn density or downgrade monsters")
        if death_prob > self.MAX_DEATH_PROBABILITY:
            recommendations.append("Add safe zones or reduce monster counts")
        if spawn_count < 3 and risk_score > 40:
            recommendations.append("Consider adding more spawns for variety")

        # Classify risk level
        if risk_score < 15:
            risk_level = "safe"
        elif risk_score < 30:
            risk_level = "low"
        elif risk_score < 50:
            risk_level = "medium"
        elif risk_score < 75:
            risk_level = "high"
        else:
            risk_level = "extreme"

        return RiskAssessment(
            zone_name=region.name,
            risk_score=round(risk_score, 1),
            risk_level=risk_level,
            death_probability=round(death_prob, 3),
            supply_drain_rate=round(supply_drain, 1),
            risk_factors=risk_factors,
            recommendations=recommendations,
        )

    def _collect_spawns(self, world: WorldModel,
                        region: Region) -> List[Tuple[int, int, int, Spawn]]:
        """Collect spawns in region."""
        spawns: List[Tuple[int, int, int, Spawn]] = []
        for tile in world.tiles.values():
            if tile.zone == region.name and tile.spawn is not None:
                spawns.append((tile.x, tile.y, tile.z, tile.spawn))
        return spawns

    def _reduce_risk(self, world: WorldModel, region: Region,
                     assessment: RiskAssessment,
                     result: RiskBalanceResult) -> None:
        """Reduce risk by removing excess spawns."""
        zone_spawns = self._collect_spawns(world, region)
        target_remove = max(1, len(zone_spawns) // 3)

        # Remove spawns with highest danger
        sorted_spawns = sorted(
            zone_spawns,
            key=lambda s: MONSTER_DANGER.get(s[3].monster, 25),
            reverse=True,
        )

        removed = 0
        for x, y, z, spawn in sorted_spawns:
            if removed >= target_remove:
                break
            tile = world.get_tile(x, y, z)
            if tile is not None:
                tile.spawn = None
                removed += 1
                result.adjustments.append(RiskAdjustment(
                    zone_name=region.name,
                    action="reduce_density",
                    old_value=spawn.to_dict(),
                    new_value=None,
                    reason=f"Risk score too high ({assessment.risk_score} > {self.MAX_RISK_SCORE})",
                ))

        if removed > 0:
            result.zones_modified.append(region.name)

    def _increase_risk_interest(self, world: WorldModel, region: Region,
                                assessment: RiskAssessment,
                                result: RiskBalanceResult) -> None:
        """Add some danger to a completely safe zone."""
        zone_spawns = self._collect_spawns(world, region)
        empty_tiles = [t for t in world.tiles.values()
                       if t.zone == region.name and t.spawn is None]

        if not empty_tiles:
            return

        # Add one slightly challenging spawn
        target_monster = "Dragon"
        tile = empty_tiles[0]
        new_spawn = Spawn(monster=target_monster, respawn=60, radius=5)
        tile.spawn = new_spawn
        result.adjustments.append(RiskAdjustment(
            zone_name=region.name,
            action="adjust_spawn",
            old_value=None,
            new_value=new_spawn.to_dict(),
            reason=f"Zone too safe (risk={assessment.risk_score}, min={self.MIN_RISK_SCORE})",
        ))
        result.zones_modified.append(region.name)

    def assess_risk(self, world: WorldModel, region: Region,
                    player_level: int = 150) -> RiskAssessment:
        """
        Assess risk without modifying the world.

        Returns:
            RiskAssessment with current risk metrics.
        """
        return self._assess_risk(world, region, player_level)