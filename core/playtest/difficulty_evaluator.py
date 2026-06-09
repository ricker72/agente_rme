"""
Difficulty Evaluator — Rates zone difficulty and balance.

Evaluates spawn density, monster level appropriateness, zone pacing,
and overall difficulty curve across a world.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class DifficultyReport:
    """Difficulty evaluation for a world or zone."""
    overall_difficulty: str  # "trivial", "easy", "medium", "hard", "extreme"
    difficulty_score: float  # 0.0 - 10.0
    spawn_density: float  # monsters per 100 tiles
    level_ratio: float  # avg monster level / player level
    time_to_clear: float  # estimated seconds to clear zone
    risk_reward_ratio: float  # xp gain / risk factor
    zone_difficulties: Dict[str, float]  # zone -> score
    issues: List[str]
    recommendations: List[str]


class DifficultyEvaluator:
    """Evaluates difficulty balance for hunt areas and dungeons."""

    # Optimal spawn density per 100 tiles
    OPTIMAL_DENSITY = 5.0
    MIN_DENSITY = 1.0
    MAX_DENSITY = 15.0

    # Level ratio thresholds
    IDEAL_LEVEL_RATIO = 1.0
    MIN_LEVEL_RATIO = 0.5
    MAX_LEVEL_RATIO = 2.0

    # Difficulty score ranges
    DIFFICULTY_BANDS = {
        (0.0, 2.0): "trivial",
        (2.0, 4.0): "easy",
        (4.0, 6.0): "medium",
        (6.0, 8.0): "hard",
        (8.0, 10.0): "extreme",
    }

    def __init__(self, seed: Optional[int] = None):
        self._seed = seed

    def evaluate_zone(
        self,
        zone_name: str,
        spawn_count: int,
        total_tiles: int,
        monster_avg_level: int,
        player_level: int,
        has_boss: bool = False,
        has_healing: bool = False,
    ) -> Tuple[float, str, List[str]]:
        """
        Evaluate difficulty for a single zone.

        Returns:
            (score, difficulty_label, issues)
        """
        issues = []

        # ── Spawn Density Score ──
        density = (spawn_count / max(total_tiles, 1)) * 100
        if density < self.MIN_DENSITY:
            density_score = 1.0
            issues.append(f"Zone '{zone_name}' has very low spawn density ({density:.1f}/100 tiles)")
        elif density > self.MAX_DENSITY:
            density_score = 10.0
            issues.append(f"Zone '{zone_name}' has excessive spawn density ({density:.1f}/100 tiles)")
        else:
            # Linear scale 1-10 based on density
            density_score = 1.0 + (density - self.MIN_DENSITY) / (
                self.MAX_DENSITY - self.MIN_DENSITY
            ) * 9.0

        # ── Level Ratio Score ──
        level_ratio = monster_avg_level / max(player_level, 1)
        if level_ratio < self.MIN_LEVEL_RATIO:
            level_score = 1.0
            issues.append(f"Monsters too weak for target level (ratio: {level_ratio:.2f})")
        elif level_ratio > self.MAX_LEVEL_RATIO:
            level_score = 10.0
            issues.append(f"Monsters too strong for target level (ratio: {level_ratio:.2f})")
        else:
            # Parabolic score centered on IDEAL_LEVEL_RATIO
            deviation = abs(level_ratio - self.IDEAL_LEVEL_RATIO)
            max_deviation = max(
                self.IDEAL_LEVEL_RATIO - self.MIN_LEVEL_RATIO,
                self.MAX_LEVEL_RATIO - self.IDEAL_LEVEL_RATIO,
            )
            level_score = 3.0 + (deviation / max_deviation) * 7.0

        # ── Boss Difficulty ──
        boss_bonus = 1.5 if has_boss else 0.0

        # ── Healing Availability ──
        healing_penalty = -1.0 if has_healing else 1.0

        # ── Composite Score ──
        score = (density_score * 0.4 + level_score * 0.5) + boss_bonus + healing_penalty
        score = max(0.0, min(10.0, score))

        # ── Difficulty Label ──
        label = "medium"
        for (low, high), name in self.DIFFICULTY_BANDS.items():
            if low <= score < high:
                label = name
                break

        return score, label, issues

    def evaluate_world(
        self,
        zones: Dict[str, Dict],
        player_level: int,
    ) -> DifficultyReport:
        """
        Evaluate difficulty across all zones in a world.

        Args:
            zones: {
                zone_name: {
                    "spawn_count": int,
                    "total_tiles": int,
                    "monster_avg_level": int,
                    "has_boss": bool,
                    "has_healing": bool,
                    "monster_xp": int,
                }
            }
            player_level: Target player level
        """
        zone_difficulties: Dict[str, float] = {}
        all_issues: List[str] = []
        all_recommendations: List[str] = []
        total_score = 0.0

        for zone_name, info in zones.items():
            score, label, issues = self.evaluate_zone(
                zone_name=zone_name,
                spawn_count=info.get("spawn_count", 0),
                total_tiles=info.get("total_tiles", 2500),
                monster_avg_level=info.get("monster_avg_level", player_level),
                player_level=player_level,
                has_boss=info.get("has_boss", False),
                has_healing=info.get("has_healing", False),
            )
            zone_difficulties[zone_name] = score
            total_score += score
            all_issues.extend(issues)

        avg_score = total_score / max(len(zones), 1)

        # Overall difficulty label
        overall_label = "medium"
        for (low, high), name in self.DIFFICULTY_BANDS.items():
            if low <= avg_score < high:
                overall_label = name
                break

        # Aggregate metrics
        avg_density = 0.0
        avg_level_ratio = 0.0
        for info in zones.values():
            tiles = info.get("total_tiles", 2500)
            spawns = info.get("spawn_count", 0)
            avg_density += (spawns / max(tiles, 1)) * 100
            mlvl = info.get("monster_avg_level", player_level)
            avg_level_ratio += mlvl / max(player_level, 1)
        avg_density /= max(len(zones), 1)
        avg_level_ratio /= max(len(zones), 1)

        # Risk-reward
        total_xp = sum(info.get("monster_xp", 100) * info.get("spawn_count", 0) for info in zones.values())
        risk_reward = total_xp / max(avg_score * 1000, 1)

        # Time to clear estimation
        time_to_clear = avg_density * 10  # rough estimate: density * 10 seconds

        # Recommendations
        if avg_density > self.MAX_DENSITY:
            all_recommendations.append("Reduce overall spawn density for better pacing.")
        if avg_density < self.MIN_DENSITY:
            all_recommendations.append("Increase spawn density to keep players engaged.")
        if avg_level_ratio > 1.5:
            all_recommendations.append("Monster levels are too high. Reduce by 20-30%.")
        if avg_level_ratio < 0.5:
            all_recommendations.append("Monster levels too low for target audience.")
        if len(zones) > 1 and max(zone_difficulties.values()) - min(zone_difficulties.values()) > 5.0:
            all_recommendations.append("Large difficulty gaps between zones. Add transitional areas.")
        if not all_recommendations:
            all_recommendations.append("Difficulty balance is within acceptable range.")

        return DifficultyReport(
            overall_difficulty=overall_label,
            difficulty_score=avg_score,
            spawn_density=avg_density,
            level_ratio=avg_level_ratio,
            time_to_clear=time_to_clear,
            risk_reward_ratio=risk_reward,
            zone_difficulties=zone_difficulties,
            issues=all_issues,
            recommendations=all_recommendations,
        )

    def is_balanced(
        self,
        player_level: int,
        monster_min_level: int,
        monster_max_level: int,
        spawn_count: int,
        area_tiles: int,
    ) -> Tuple[bool, List[str]]:
        """
        Quick balance check for a hunt area.

        Returns:
            (is_balanced, list of issues)
        """
        issues = []
        avg_monster_level = (monster_min_level + monster_max_level) / 2
        ratio = avg_monster_level / max(player_level, 1)

        if ratio > 1.5:
            issues.append(f"Monster avg level ({avg_monster_level:.0f}) too high for level {player_level}")
        elif ratio < 0.5:
            issues.append(f"Monster avg level ({avg_monster_level:.0f}) too low for level {player_level}")

        density = (spawn_count / max(area_tiles, 1)) * 100
        if density > 12:
            issues.append(f"Spawn density ({density:.1f}) too high, may cause overwhelming spawns")
        elif density < 2:
            issues.append(f"Spawn density ({density:.1f}) too low, hunt will feel empty")

        return len(issues) == 0, issues

    @staticmethod
    def difficulty_color(score: float) -> str:
        """Return a color code for difficulty visualization."""
        if score < 2.0:
            return "#00ff00"  # Green - trivial
        elif score < 4.0:
            return "#88ff00"  # Light green - easy
        elif score < 6.0:
            return "#ffff00"  # Yellow - medium
        elif score < 8.0:
            return "#ff8800"  # Orange - hard
        else:
            return "#ff0000"  # Red - extreme