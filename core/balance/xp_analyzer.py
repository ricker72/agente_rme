from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class XPAnalysis:
    """Analysis of XP rates for a hunt zone."""

    zone_name: str = ""
    xp_per_kill: Dict[str, int] = field(default_factory=dict)  # monster → XP
    kills_per_hour: float = 0.0
    xp_per_hour: float = 0.0
    xp_per_hour_solo: float = 0.0
    xp_per_hour_duo: float = 0.0
    xp_per_hour_party: float = 0.0
    efficiency_score: float = 0.0  # 0-100 based on XP vs level curve
    optimal_level_min: int = 0
    optimal_level_max: int = 0
    rating: str = ""  # "poor", "balanced", "great", "overpowered"
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "xp_per_hour": self.xp_per_hour,
            "xp_per_hour_solo": self.xp_per_hour_solo,
            "xp_per_hour_duo": self.xp_per_hour_duo,
            "xp_per_hour_party": self.xp_per_hour_party,
            "efficiency_score": self.efficiency_score,
            "optimal_level_range": [self.optimal_level_min, self.optimal_level_max],
            "rating": self.rating,
            "kills_per_hour": self.kills_per_hour,
            "warnings": self.warnings,
        }


class XPAnalyzer:
    """
    Analyzes XP rates for hunt zones.

    Calculates:
      - XP per kill per monster type
      - XP/hour for solo, duo, and party play
      - Optimal level range based on XP efficiency
      - Efficiency score compared to ideal XP curves

    Reference XP curves based on standard Tibia progression:
      Level 1-50:   50-150k XP/h (fast leveling)
      Level 50-100: 150-400k XP/h
      Level 100-200: 400-800k XP/h
      Level 200-400: 800-1500k XP/h
      Level 400+:    1500-3000k XP/h
    """

    # Reference XP curves (XP/h range per level bracket)
    XP_CURVES = {
        (0, 50): (50000, 150000),
        (50, 100): (150000, 400000),
        (100, 150): (400000, 600000),
        (150, 200): (600000, 800000),
        (200, 300): (800000, 1200000),
        (300, 400): (1200000, 1500000),
        (400, 500): (1500000, 2000000),
        (500, 700): (2000000, 2500000),
        (700, 1000): (2500000, 3000000),
        (1000, 9999): (3000000, 5000000),
    }

    # Kill rate assumptions per mode
    KILLS_PER_HOUR = {"solo": 80, "duo": 120, "party": 180}

    def __init__(self):
        self._analysis_cache: Dict[str, XPAnalysis] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_zone(
        self, zone_name: str, spawns: List[Dict[str, Any]], monsters: Dict[str, int]
    ) -> XPAnalysis:
        """
        Analyze XP rates for a hunt zone.

        Args:
            zone_name: Name of the zone.
            spawns: List of spawn dicts with "monster" and "count".
                    [{"name": "Dragon", "count": 3}, ...]
            monsters: Dict mapping monster name → XP value.
                      {"Dragon": 700, "Dragon Lord": 2100, ...}

        Returns:
            XPAnalysis with XP/h calculations and rating.
        """
        # Calculate weighted XP per kill
        xp_per_kill: Dict[str, int] = {}
        total_xp_weighted = 0.0
        total_count = 0

        for spawn in spawns:
            monster_name = spawn.get("name", spawn.get("monster", ""))
            count = spawn.get("count", 1)
            xp = monsters.get(monster_name, 0)

            xp_per_kill[monster_name] = xp
            total_xp_weighted += xp * count
            total_count += count

        if total_count == 0 or total_xp_weighted == 0:
            return XPAnalysis(
                zone_name=zone_name,
                rating="no_data",
                warnings=["No monster data available for analysis"],
            )

        avg_xp_per_kill = total_xp_weighted / total_count

        # Calculate XP/h for each mode
        kills_per_hour = self._estimate_kills_per_hour(total_count, avg_xp_per_kill)
        xp_hour_base = avg_xp_per_kill * kills_per_hour

        xp_solo = xp_hour_base * self.KILLS_PER_HOUR["solo"] / max(kills_per_hour, 1)
        xp_duo = xp_hour_base * self.KILLS_PER_HOUR["duo"] / max(kills_per_hour, 1)
        xp_party = xp_hour_base * self.KILLS_PER_HOUR["party"] / max(kills_per_hour, 1)

        # Determine optimal level range
        optimal_min, optimal_max = self._find_optimal_level(xp_solo, avg_xp_per_kill)

        # Efficiency score and rating
        efficiency = self._calc_efficiency(xp_solo, optimal_min, optimal_max)
        rating = self._rate_xp(xp_solo, optimal_min, optimal_max)
        warnings = self._generate_warnings(
            xp_solo, xp_duo, xp_party, efficiency, rating
        )

        analysis = XPAnalysis(
            zone_name=zone_name,
            xp_per_kill=xp_per_kill,
            kills_per_hour=kills_per_hour,
            xp_per_hour=xp_solo,
            xp_per_hour_solo=xp_solo,
            xp_per_hour_duo=xp_duo,
            xp_per_hour_party=xp_party,
            efficiency_score=efficiency,
            optimal_level_min=optimal_min,
            optimal_level_max=optimal_max,
            rating=rating,
            warnings=warnings,
        )

        self._analysis_cache[zone_name] = analysis
        return analysis

    def compare_zones(self, analyses: List[XPAnalysis]) -> Dict[str, Any]:
        """Compare XP rates across multiple zones."""
        if not analyses:
            return {}

        best = max(analyses, key=lambda a: a.xp_per_hour)
        worst = min(analyses, key=lambda a: a.xp_per_hour)
        avg_xp = sum(a.xp_per_hour for a in analyses) / len(analyses)

        return {
            "best_zone": best.zone_name,
            "best_xp_h": best.xp_per_hour,
            "worst_zone": worst.zone_name,
            "worst_xp_h": worst.xp_per_hour,
            "average_xp_h": avg_xp,
            "zone_count": len(analyses),
            "spread_ratio": best.xp_per_hour / max(worst.xp_per_hour, 1),
        }

    def suggest_xp_adjustment(self, analysis: XPAnalysis) -> Dict[str, Any]:
        """
        Suggest XP adjustments to make a zone balanced.

        Returns:
            Dict with suggested multipliers and new XP values.
        """
        optimal_min = analysis.optimal_level_min
        optimal_max = analysis.optimal_level_max
        current_xp = analysis.xp_per_hour

        # Find target XP for the optimal level bracket
        target_xp = self._target_xp_for_level(optimal_min)

        if target_xp == 0:
            return {"adjustment": "none", "reason": "Cannot determine target"}

        ratio = target_xp / max(current_xp, 1)
        ratio = max(0.1, min(10.0, ratio))  # Clamp to sane range

        adjustments = {}
        for monster_name, xp_kill in analysis.xp_per_kill.items():
            new_xp = int(xp_kill * ratio)
            adjustments[monster_name] = {"current_xp": xp_kill, "suggested_xp": new_xp}

        return {
            "adjustment": "multiply" if ratio != 1.0 else "none",
            "multiplier": round(ratio, 2),
            "target_xp_per_hour": int(target_xp),
            "current_xp_per_hour": int(current_xp),
            "optimal_level_range": [optimal_min, optimal_max],
            "monster_adjustments": adjustments,
        }

    # ------------------------------------------------------------------
    # Internal calculations
    # ------------------------------------------------------------------

    def _estimate_kills_per_hour(self, spawn_count: int, avg_xp: float) -> float:
        """Estimate realistic kills per hour based on spawn density and XP."""
        if spawn_count <= 3:
            base = 60
        elif spawn_count <= 8:
            base = 80
        else:
            base = 100

        # High XP monsters take longer to kill
        if avg_xp > 5000:
            base *= 0.6
        elif avg_xp > 2000:
            base *= 0.8

        return base

    def _find_optimal_level(
        self, xp_hour: float, avg_xp_per_kill: float
    ) -> Tuple[int, int]:
        """Find the optimal level range for this XP rate."""
        for (lo, hi), (min_xp, max_xp) in self.XP_CURVES.items():
            if min_xp <= xp_hour <= max_xp * 1.3:
                return lo, hi

        # Fallback: estimate from XP per kill
        if avg_xp_per_kill < 100:
            return 1, 30
        elif avg_xp_per_kill < 500:
            return 30, 80
        elif avg_xp_per_kill < 1500:
            return 80, 150
        elif avg_xp_per_kill < 3000:
            return 150, 250
        else:
            return 250, 500

    def _calc_efficiency(self, xp_hour: float, level_min: int, level_max: int) -> float:
        """Calculate XP efficiency score (0-100)."""
        if level_max <= 0:
            return 0.0

        target_lo, target_hi = self._target_xp_range_for_level(level_min)
        if target_hi == 0:
            return 50.0

        if xp_hour < target_lo:
            return max(0.0, (xp_hour / target_lo) * 50)
        elif xp_hour > target_hi:
            return max(50.0, 100 - ((xp_hour - target_hi) / target_hi) * 50)
        else:
            # In the sweet spot
            return 50 + ((xp_hour - target_lo) / max(target_hi - target_lo, 1)) * 50

    def _target_xp_for_level(self, level: int) -> float:
        """Get target XP/hour for a given level."""
        target_lo, target_hi = self._target_xp_range_for_level(level)
        return (target_lo + target_hi) / 2

    def _target_xp_range_for_level(self, level: int) -> Tuple[float, float]:
        """Get expected XP range for a level."""
        for (lo, hi), (min_xp, max_xp) in self.XP_CURVES.items():
            if lo <= level <= hi:
                return min_xp, max_xp
        return 0.0, 0.0

    def _rate_xp(self, xp_hour: float, level_min: int, level_max: int) -> str:
        """Rate the XP rate for a given level range."""
        target_lo, target_hi = self._target_xp_range_for_level(level_min)

        if target_hi == 0:
            return "unknown"

        if xp_hour < target_lo * 0.5:
            return "poor"
        elif xp_hour < target_lo * 0.8:
            return "below_average"
        elif xp_hour <= target_hi:
            return "balanced"
        elif xp_hour <= target_hi * 1.5:
            return "great"
        else:
            return "overpowered"

    def _generate_warnings(
        self,
        xp_solo: float,
        xp_duo: float,
        xp_party: float,
        efficiency: float,
        rating: str,
    ) -> List[str]:
        """Generate warnings based on XP analysis."""
        warnings = []

        if rating == "poor":
            warnings.append(
                "XP rate is very low; consider increasing monster XP or density"
            )
        elif rating == "overpowered":
            warnings.append("XP rate is too high; risk of overpowered leveling")

        if efficiency < 30:
            warnings.append("Zone is inefficient for its level range")
        if xp_party / max(xp_solo, 1) < 1.5:
            warnings.append("Party XP gain is minimal; consider adding more spawns")
        if xp_solo < 50000:
            warnings.append("Very low XP; zone may not be worth hunting")

        return warnings
