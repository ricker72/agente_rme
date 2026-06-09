"""
Survival Analyzer — Evaluates player survival across zones.

Analyzes death risk, escape routes, healing sufficiency, and safe zones
for each vocation in all areas of a generated world.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .combat_simulator import CombatSimulator, MonsterStats
from .player_bot import Vocation
from .pathfinder import Pathfinder

logger = logging.getLogger(__name__)


@dataclass
class ZoneSurvival:
    """Survival metrics for a specific zone."""
    zone_name: str
    avg_deaths_per_hour: float
    survival_rate: float  # 0.0 - 1.0
    time_to_escape: float  # seconds
    escape_reachable: bool
    safe_zone_distance: float  # distance to nearest safe area
    healing_sufficient: bool
    risk_level: str  # "safe", "moderate", "dangerous", "deadly"
    deaths_by_vocation: Dict[str, int]


@dataclass
class SurvivalReport:
    """Overall survival analysis for a world."""
    overall_survival_rate: float
    total_deaths: int
    death_zones: List[str]  # zones with high death rate
    safe_zones: List[str]
    worst_vocation: str
    best_vocation: str
    zone_reports: List[ZoneSurvival]
    recommendations: List[str]


class SurvivalAnalyzer:
    """Analyzes survival probability across world zones."""

    DEATH_RATE_THRESHOLDS = {
        "safe": 0.01,
        "moderate": 0.05,
        "dangerous": 0.15,
        "deadly": 0.30,
    }

    def __init__(self, seed: Optional[int] = None):
        self._combat = CombatSimulator(seed)
        self._seed = seed

    def analyze_zone(
        self,
        zone_name: str,
        monsters: List[MonsterStats],
        level: int,
        pathfinder: Optional[Pathfinder] = None,
        spawn_pos: Optional[Tuple[int, int, int]] = None,
    ) -> ZoneSurvival:
        """
        Analyze survival in a single zone for all vocations.

        Args:
            zone_name: Name of the zone
            monsters: Monsters present in the zone
            level: Simulated player level
            pathfinder: Pathfinder for escape route analysis
            spawn_pos: Player spawn/entry position
        """
        deaths_by_vocation: Dict[str, int] = {}
        total_fights = 0

        for vocation in Vocation:
            vocation_deaths = 0
            encounter = self._combat.simulate_hunt_rotation(
                vocation=vocation,
                level=level,
                monsters=monsters,
                rotation_time_minutes=60.0,
            )
            vocation_deaths = encounter.deaths
            deaths_by_vocation[vocation.name.lower()] = vocation_deaths
            total_fights += encounter.monsters_killed + vocation_deaths

        total_deaths = sum(deaths_by_vocation.values())
        avg_deaths = total_deaths / max(len(Vocation), 1)

        # Survival rate = fights without death / total fights
        survival_rate = 1.0 - (total_deaths / max(total_fights, 1))

        # Escape analysis
        escape_time = 0.0
        escape_reachable = True
        safe_distance = float('inf')

        if pathfinder and spawn_pos:
            # Check if there's a path from any tile to a safe zone
            distance_map = pathfinder.distance_map(spawn_pos, max_steps=50)
            if distance_map:
                safe_distance = max(distance_map.values()) if distance_map else 0.0
                escape_time = safe_distance  # 1 step ≈ 1 second
            else:
                escape_reachable = False
                escape_time = float('inf')
        else:
            safe_distance = 10.0  # Default assumption
            escape_time = 10.0

        # Healing sufficiency (healers survive more)
        healing_sufficient = (
            deaths_by_vocation.get("druid", 0) == 0
            or deaths_by_vocation.get("sorcerer", 0) == 0
        )

        # Risk level
        death_rate = avg_deaths / max(total_fights, 1) if total_fights > 0 else 0
        risk_level = "safe"
        for level_name, threshold in sorted(
            self.DEATH_RATE_THRESHOLDS.items(),
            key=lambda x: x[1], reverse=True,
        ):
            if death_rate >= threshold:
                risk_level = level_name
                break

        return ZoneSurvival(
            zone_name=zone_name,
            avg_deaths_per_hour=avg_deaths,
            survival_rate=survival_rate,
            time_to_escape=escape_time,
            escape_reachable=escape_reachable,
            safe_zone_distance=safe_distance,
            healing_sufficient=healing_sufficient,
            risk_level=risk_level,
            deaths_by_vocation=deaths_by_vocation,
        )

    def analyze_world(
        self,
        zones: Dict[str, List[MonsterStats]],
        level: int,
        pathfinder: Optional[Pathfinder] = None,
        spawn_pos: Optional[Tuple[int, int, int]] = None,
    ) -> SurvivalReport:
        """
        Analyze survival across all zones in a world.

        Args:
            zones: {zone_name: [monsters]}
            level: Simulated player level
            pathfinder: For escape analysis
            spawn_pos: Entry point
        """
        zone_reports: List[ZoneSurvival] = []
        total_deaths = 0
        all_deaths_by_voc: Dict[str, int] = {v.name.lower(): 0 for v in Vocation}

        for zone_name, monsters in zones.items():
            report = self.analyze_zone(
                zone_name=zone_name,
                monsters=monsters,
                level=level,
                pathfinder=pathfinder,
                spawn_pos=spawn_pos,
            )
            zone_reports.append(report)
            total_deaths += int(report.avg_deaths_per_hour)
            for voc, deaths in report.deaths_by_vocation.items():
                all_deaths_by_voc[voc] = all_deaths_by_voc.get(voc, 0) + deaths

        # Find best/worst vocations
        best_voc = min(all_deaths_by_voc, key=all_deaths_by_voc.get)
        worst_voc = max(all_deaths_by_voc, key=all_deaths_by_voc.get)

        death_zones = [z.zone_name for z in zone_reports if z.risk_level in ("dangerous", "deadly")]
        safe_zones = [z.zone_name for z in zone_reports if z.risk_level == "safe"]

        overall_survival = (
            sum(z.survival_rate for z in zone_reports) / max(len(zone_reports), 1)
        )

        recommendations = self._generate_recommendations(zone_reports, all_deaths_by_voc)

        return SurvivalReport(
            overall_survival_rate=overall_survival,
            total_deaths=total_deaths,
            death_zones=death_zones,
            safe_zones=safe_zones,
            worst_vocation=worst_voc,
            best_vocation=best_voc,
            zone_reports=zone_reports,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        zones: List[ZoneSurvival],
        voc_deaths: Dict[str, int],
    ) -> List[str]:
        """Generate survival improvement recommendations."""
        recs = []

        deadly_zones = [z for z in zones if z.risk_level == "deadly"]
        if deadly_zones:
            names = ", ".join(z.zone_name for z in deadly_zones)
            recs.append(f"Zones marked deadly ({names}) need reduced monster density or weaker spawns.")

        no_escape = [z for z in zones if not z.escape_reachable]
        if no_escape:
            names = ", ".join(z.zone_name for z in no_escape)
            recs.append(f"Zones with no escape route ({names}) need teleport exits or safe paths.")

        poor_healing = [z for z in zones if not z.healing_sufficient]
        if poor_healing:
            names = ", ".join(z.zone_name for z in poor_healing)
            recs.append(f"Insufficient healing in ({names}). Add healing NPCs or reduce pressure.")

        worst_voc = max(voc_deaths, key=voc_deaths.get) if voc_deaths else "unknown"
        if voc_deaths.get(worst_voc, 0) > len(zones) * 2:
            recs.append(f"{worst_voc.capitalize()} has excessive deaths. Consider class-specific balance.")

        if not recs:
            recs.append("All zones pass survival checks. World is playable.")

        return recs

    def quick_risk_assessment(
        self,
        monster_level: int,
        player_level: int,
        monster_count: int,
    ) -> str:
        """Quick risk level estimation without full simulation."""
        level_ratio = monster_level / max(player_level, 1)
        density_factor = monster_count / 50.0  # 50 monsters = baseline

        risk_score = level_ratio * density_factor

        if risk_score < 0.3:
            return "safe"
        elif risk_score < 0.8:
            return "moderate"
        elif risk_score < 1.5:
            return "dangerous"
        else:
            return "deadly"