"""
Progression Analyzer — Evaluates XP/hour, level progression, and game pacing.

Analyzes how quickly players progress through content, identifies dead zones,
and validates that the difficulty curve matches expected player growth.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .combat_simulator import CombatSimulator, MonsterStats
from .player_bot import Vocation

logger = logging.getLogger(__name__)


@dataclass
class ProgressionPoint:
    """A single point on the progression curve."""

    level: int
    xp_per_hour: float
    loot_per_hour: float
    deaths_per_hour: float
    time_to_next_level_hours: float
    hunt_efficiency: float  # xp / (deaths * 10000 + 1)


@dataclass
class ProgressionReport:
    """Full progression analysis for a world."""

    level_range: Tuple[int, int]
    xp_per_hour_min: float
    xp_per_hour_max: float
    xp_per_hour_avg: float
    loot_per_hour_min: float
    loot_per_hour_max: float
    total_deaths: int
    progression_points: List[ProgressionPoint]
    bottlenecks: List[str]  # levels where progression stalls
    dead_zones: List[str]  # zones with no useful content
    curve_smoothness: float  # 0.0-1.0, how smooth the XP curve is
    estimated_level_time_hours: Dict[int, float]  # level -> hours to reach
    recommendations: List[str]


class ProgressionAnalyzer:
    """Analyzes player progression through world content."""

    # XP required to level (Tibia-like formula)
    BASE_XP_PER_LEVEL = 1000

    def __init__(self, seed: Optional[int] = None):
        self._combat = CombatSimulator(seed)

    def xp_required_for_level(self, level: int) -> int:
        """Calculate XP required to advance from level to level+1."""
        return int(self.BASE_XP_PER_LEVEL * level * (1 + level / 100.0))

    def time_to_level(self, xp_per_hour: float, current_level: int) -> float:
        """Estimate hours to reach next level at given XP/hour."""
        xp_needed = self.xp_required_for_level(current_level)
        if xp_per_hour <= 0:
            return float("inf")
        return xp_needed / xp_per_hour

    def analyze_zone_progression(
        self,
        monsters: List[MonsterStats],
        player_level: int,
        rotation_minutes: float = 60.0,
    ) -> ProgressionPoint:
        """Analyze progression metrics for a single zone at a given level."""
        results_by_voc = self._combat.simulate_multi_vocation(
            level=player_level,
            monsters=monsters,
            rotation_minutes=rotation_minutes,
        )

        # Average across vocations
        avg_xp = sum(r.experience_per_hour for r in results_by_voc.values()) / len(
            results_by_voc
        )
        avg_deaths = sum(r.deaths for r in results_by_voc.values()) / len(
            results_by_voc
        )
        sum(r.total_time for r in results_by_voc.values()) / len(results_by_voc)

        # Loot estimate (simplified)
        avg_loot = avg_xp * 0.2  # rough gold/xp ratio

        time_to_next = self.time_to_level(avg_xp, player_level)
        efficiency = avg_xp / max(avg_deaths * 10000 + 1, 1)

        return ProgressionPoint(
            level=player_level,
            xp_per_hour=avg_xp,
            loot_per_hour=avg_loot,
            deaths_per_hour=avg_deaths,
            time_to_next_level_hours=time_to_next,
            hunt_efficiency=efficiency,
        )

    def analyze_progression_curve(
        self,
        zones: Dict[str, List[MonsterStats]],
        level_min: int,
        level_max: int,
        level_step: int = 50,
    ) -> ProgressionReport:
        """
        Analyze the full progression curve from level_min to level_max.

        Args:
            zones: {zone_name: [monsters]}
            level_min: Starting level
            level_max: Target level
            level_step: Level increments to simulate
        """
        points: List[ProgressionPoint] = []
        all_xp = []
        all_loot = []
        all_deaths = 0

        levels = list(range(level_min, level_max + 1, level_step))

        for level in levels:
            # Find the best zone for this level
            best_xp = 0.0
            best_point = None

            for zone_name, monsters in zones.items():
                point = self.analyze_zone_progression(monsters, level)
                if point.xp_per_hour > best_xp:
                    best_xp = point.xp_per_hour
                    best_point = point

            if best_point is None:
                best_point = ProgressionPoint(
                    level=level,
                    xp_per_hour=0,
                    loot_per_hour=0,
                    deaths_per_hour=0,
                    time_to_next_level_hours=float("inf"),
                    hunt_efficiency=0,
                )

            points.append(best_point)
            all_xp.append(best_point.xp_per_hour)
            all_loot.append(best_point.loot_per_hour)
            all_deaths += int(best_point.deaths_per_hour)

        # Calculate progression metrics
        xp_min = min(all_xp) if all_xp else 0
        xp_max = max(all_xp) if all_xp else 0
        xp_avg = sum(all_xp) / max(len(all_xp), 1)
        loot_min = min(all_loot) if all_loot else 0
        loot_max = max(all_loot) if all_loot else 0

        # Detect bottlenecks (levels where XP drops significantly)
        bottlenecks = []
        for i in range(1, len(points)):
            if points[i].xp_per_hour < points[i - 1].xp_per_hour * 0.7:
                bottlenecks.append(
                    f"Level {points[i].level}: XP/hour drops to {points[i].xp_per_hour:.0f}"
                )

        # Curve smoothness (coefficient of variation)
        if len(all_xp) > 1 and xp_avg > 0:
            variance = sum((x - xp_avg) ** 2 for x in all_xp) / len(all_xp)
            std_dev = math.sqrt(variance)
            cv = std_dev / xp_avg
            smoothness = max(0, 1.0 - cv)
        else:
            smoothness = 1.0

        # Estimate total time to level from min to max
        level_times = {}
        total_hours = 0.0
        for level in range(level_min, level_max):
            # Find closest point
            closest = min(points, key=lambda p: abs(p.level - level))
            t = self.time_to_level(closest.xp_per_hour, level)
            if t < float("inf"):
                total_hours += t
            level_times[level] = total_hours

        # Dead zones (zones that are never optimal for any level)
        all_zone_names = set(zones.keys())
        used_zones = set()
        for point in points:
            for zone_name, monsters in zones.items():
                if point.xp_per_hour > 0:
                    # Check if this zone contributed
                    zone_point = self.analyze_zone_progression(monsters, point.level)
                    if zone_point.xp_per_hour == point.xp_per_hour:
                        used_zones.add(zone_name)
        dead_zones = list(all_zone_names - used_zones)

        # Recommendations
        recommendations = []
        if bottlenecks:
            recommendations.append(
                f"{len(bottlenecks)} progression bottleneck(s) detected. Add intermediate zones."
            )
        if dead_zones:
            recommendations.append(
                f"Dead zones ({', '.join(dead_zones[:3])}) provide no value. Remove or rebalance."
            )
        if smoothness < 0.6:
            recommendations.append(
                "XP curve is erratic. Smooth monster level transitions."
            )
        if xp_avg < self.xp_required_for_level(level_min) * 0.1:
            recommendations.append("XP rates too low. Players will feel stuck.")
        if not recommendations:
            recommendations.append("Progression curve is balanced and smooth.")

        return ProgressionReport(
            level_range=(level_min, level_max),
            xp_per_hour_min=xp_min,
            xp_per_hour_max=xp_max,
            xp_per_hour_avg=xp_avg,
            loot_per_hour_min=loot_min,
            loot_per_hour_max=loot_max,
            total_deaths=all_deaths,
            progression_points=points,
            bottlenecks=bottlenecks,
            dead_zones=dead_zones,
            curve_smoothness=smoothness,
            estimated_level_time_hours=level_times,
            recommendations=recommendations,
        )

    def compare_vocation_progression(
        self,
        monsters: List[MonsterStats],
        level_min: int,
        level_max: int,
        level_step: int = 100,
    ) -> Dict[str, List[ProgressionPoint]]:
        """Compare progression curves for each vocation."""
        results = {v.name.lower(): [] for v in Vocation}

        for level in range(level_min, level_max + 1, level_step):
            for vocation in Vocation:
                encounter = self._combat.simulate_hunt_rotation(
                    vocation=vocation,
                    level=level,
                    monsters=monsters,
                    rotation_time_minutes=60.0,
                )
                time_to_next = self.time_to_level(encounter.experience_per_hour, level)
                efficiency = encounter.experience_per_hour / max(
                    encounter.deaths * 10000 + 1, 1
                )

                point = ProgressionPoint(
                    level=level,
                    xp_per_hour=encounter.experience_per_hour,
                    loot_per_hour=encounter.experience_per_hour * 0.2,
                    deaths_per_hour=encounter.deaths,
                    time_to_next_level_hours=time_to_next,
                    hunt_efficiency=efficiency,
                )
                results[vocation.name.lower()].append(point)

        return results

    def validate_level_range(
        self,
        zone_monster_min_level: int,
        zone_monster_max_level: int,
        target_player_min: int,
        target_player_max: int,
    ) -> Tuple[bool, List[str]]:
        """Validate that monster levels match the target player range."""
        issues = []

        avg_monster = (zone_monster_min_level + zone_monster_max_level) / 2
        avg_player = (target_player_min + target_player_max) / 2

        ratio = avg_monster / max(avg_player, 1)

        if ratio > 1.3:
            issues.append(
                f"Monster levels ({zone_monster_min_level}-{zone_monster_max_level}) "
                f"are too high for target players ({target_player_min}-{target_player_max})"
            )
        elif ratio < 0.4:
            issues.append(
                f"Monster levels ({zone_monster_min_level}-{zone_monster_max_level}) "
                f"are too low for target players ({target_player_min}-{target_player_max})"
            )

        spread = zone_monster_max_level - zone_monster_min_level
        if spread > (target_player_max - target_player_min) * 2:
            issues.append(
                f"Monster level spread ({spread}) is too wide for the player range"
            )

        return len(issues) == 0, issues
