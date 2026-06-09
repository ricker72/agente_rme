from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.world.world_model import WorldModel
from core.world.region import Region
from core.balance.spawn_balancer import SpawnBalancer, SpawnBalanceResult
from core.balance.xp_balancer import XPBalancer, XPBalanceResult
from core.balance.loot_balancer import LootBalancer, LootBalanceResult
from core.balance.difficulty_balancer import DifficultyBalancer, DifficultyBalanceResult
from core.balance.risk_balancer import RiskBalancer, RiskBalanceResult, RiskAssessment
from core.balance.xp_analyzer import XPAnalyzer, XPAnalysis
from core.balance.loot_analyzer import LootAnalyzer, LootAnalysis
from core.balance.difficulty_analyzer import DifficultyAnalyzer, DifficultyAnalysis


@dataclass
class ZoneBalanceReport:
    """Balance report for a single zone."""
    zone_name: str = ""
    spawn_result: Optional[SpawnBalanceResult] = None
    xp_result: Optional[XPBalanceResult] = None
    loot_result: Optional[LootBalanceResult] = None
    difficulty_result: Optional[DifficultyBalanceResult] = None
    risk_result: Optional[RiskBalanceResult] = None
    xp_analysis: Optional[XPAnalysis] = None
    loot_analysis: Optional[LootAnalysis] = None
    difficulty_analysis: Optional[DifficultyAnalysis] = None
    risk_assessment: Optional[RiskAssessment] = None
    was_modified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "was_modified": self.was_modified,
            "spawn_result": self.spawn_result.to_dict() if self.spawn_result else None,
            "xp_result": self.xp_result.to_dict() if self.xp_result else None,
            "loot_result": self.loot_result.to_dict() if self.loot_result else None,
            "difficulty_result": self.difficulty_result.to_dict() if self.difficulty_result else None,
            "risk_result": self.risk_result.to_dict() if self.risk_result else None,
        }


@dataclass
class BalanceReport:
    """Complete balance report for the entire world."""
    zones: List[ZoneBalanceReport] = field(default_factory=list)
    total_adjustments: int = 0
    zones_modified: int = 0
    world_balanced: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zones": [z.to_dict() for z in self.zones],
            "total_adjustments": self.total_adjustments,
            "zones_modified": self.zones_modified,
            "world_balanced": self.world_balanced,
        }


class BalanceEngine:
    """
    Master orchestrator for world balancing.

    Coordinates all sub-balancers (spawn, XP, loot, difficulty, risk)
    to produce a fully balanced WorldModel.

    Integration:
      - PlaytestEngine: Uses playtest results to identify imbalanced zones
      - WorldModel: Reads and modifies tile/spawn data
      - MapAnalyzer: Uses zone classification for balancing strategy
      - EvolutionEngine: Produces balanced world for further evolution

    Usage:
        engine = BalanceEngine()
        balanced_world, report = engine.balance(world)
    """

    def __init__(self, player_level: int = 150):
        self._spawn_balancer = SpawnBalancer()
        self._xp_balancer = XPBalancer()
        self._loot_balancer = LootBalancer()
        self._difficulty_balancer = DifficultyBalancer()
        self._risk_balancer = RiskBalancer()
        self._player_level = player_level

    def balance(self, world: WorldModel) -> tuple:
        """
        Balance the entire world.

        Args:
            world: WorldModel to balance (modified in-place).

        Returns:
            Tuple of (balanced WorldModel, BalanceReport).
        """
        report = BalanceReport()

        if not world.regions:
            # No regions — balance globally using all spawns as one zone
            global_region = Region(name="__global__", min_level=1, max_level=999)
            zone_report = self._balance_zone(world, global_region)
            report.zones.append(zone_report)
        else:
            for region in world.regions:
                zone_report = self._balance_zone(world, region)
                report.zones.append(zone_report)

        # Compute totals
        total_adj = 0
        zones_mod = 0
        for zr in report.zones:
            if zr.was_modified:
                zones_mod += 1
                total_adj += self._count_adjustments(zr)

        report.total_adjustments = total_adj
        report.zones_modified = zones_mod
        report.world_balanced = True

        return world, report

    def _balance_zone(self, world: WorldModel, region: Region) -> ZoneBalanceReport:
        """Balance a single zone through all sub-balancers."""
        zone_report = ZoneBalanceReport(zone_name=region.name)

        # Step 1: Analyze current state (before any modifications)
        zone_report.xp_analysis = self._xp_balancer.analyze_zone_xp(
            world, region, player_level=self._player_level
        )
        zone_report.loot_analysis = self._loot_balancer.analyze_zone_loot(
            world, region, target_level=self._player_level
        )
        zone_report.difficulty_analysis = self._difficulty_balancer.analyze_zone_difficulty(
            world, region, player_level=self._player_level
        )
        zone_report.risk_assessment = self._risk_balancer.assess_risk(
            world, region, player_level=self._player_level
        )

        # Step 2: Balance spawns first (affects all other metrics)
        zone_report.spawn_result = self._spawn_balancer.balance(world, region)

        # Step 3: Balance difficulty (replace deadly/trivial monsters)
        zone_report.difficulty_result = self._difficulty_balancer.balance(
            world, region, player_level=self._player_level
        )

        # Step 4: Balance XP (adjust spawn counts)
        zone_report.xp_result = self._xp_balancer.balance(
            world, region, player_level=self._player_level
        )

        # Step 5: Balance loot (adjust spawn composition)
        zone_report.loot_result = self._loot_balancer.balance(
            world, region, target_level=self._player_level
        )

        # Step 6: Balance risk (final safety check)
        zone_report.risk_result = self._risk_balancer.balance(
            world, region, player_level=self._player_level
        )

        # Determine if zone was modified
        zone_report.was_modified = self._zone_was_modified(zone_report)

        return zone_report

    def _zone_was_modified(self, zr: ZoneBalanceReport) -> bool:
        """Check if any sub-balancer modified this zone."""
        if zr.spawn_result and zr.spawn_result.spawns_added > 0:
            return True
        if zr.spawn_result and zr.spawn_result.spawns_removed > 0:
            return True
        if zr.xp_result and zr.xp_result.total_monsters_adjusted > 0:
            return True
        if zr.loot_result and zr.loot_result.total_adjustments > 0:
            return True
        if zr.difficulty_result and len(zr.difficulty_result.adjustments) > 0:
            return True
        if zr.risk_result and len(zr.risk_result.adjustments) > 0:
            return True
        return False

    def _count_adjustments(self, zr: ZoneBalanceReport) -> int:
        """Count total adjustments in a zone report."""
        count = 0
        if zr.spawn_result:
            count += zr.spawn_result.spawns_added + zr.spawn_result.spawns_removed
            count += zr.spawn_result.radii_adjusted + zr.spawn_result.respawns_adjusted
        if zr.xp_result:
            count += zr.xp_result.total_monsters_adjusted
        if zr.loot_result:
            count += zr.loot_result.total_adjustments
        if zr.difficulty_result:
            count += len(zr.difficulty_result.adjustments)
        if zr.risk_result:
            count += len(zr.risk_result.adjustments)
        return count

    def analyze(self, world: WorldModel) -> BalanceReport:
        """
        Analyze the world without modifying it.

        Returns:
            BalanceReport with analysis data only.
        """
        report = BalanceReport()

        regions = world.regions if world.regions else [Region(name="__global__")]

        for region in regions:
            zone_report = ZoneBalanceReport(zone_name=region.name)
            zone_report.xp_analysis = self._xp_balancer.analyze_zone_xp(
                world, region, player_level=self._player_level
            )
            zone_report.loot_analysis = self._loot_balancer.analyze_zone_loot(
                world, region, target_level=self._player_level
            )
            zone_report.difficulty_analysis = self._difficulty_balancer.analyze_zone_difficulty(
                world, region, player_level=self._player_level
            )
            zone_report.risk_assessment = self._risk_balancer.assess_risk(
                world, region, player_level=self._player_level
            )
            report.zones.append(zone_report)

        return report