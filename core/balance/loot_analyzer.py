from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class LootAnalysis:
    """Analysis of loot economy for a hunt zone."""
    zone_name: str = ""
    profit_per_hour: float = 0.0
    profit_solo: float = 0.0
    profit_duo: float = 0.0
    profit_party: float = 0.0
    supply_cost_per_hour: float = 0.0
    net_profit_per_hour: float = 0.0
    rare_drop_chance: float = 0.0
    loot_value_breakdown: Dict[str, float] = field(default_factory=dict)
    rating: str = ""  # "loss", "low", "balanced", "good", "excellent"
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "profit_per_hour": self.profit_per_hour,
            "profit_solo": self.profit_solo,
            "profit_duo": self.profit_duo,
            "profit_party": self.profit_party,
            "supply_cost_per_hour": self.supply_cost_per_hour,
            "net_profit_per_hour": self.net_profit_per_hour,
            "rare_drop_chance": self.rare_drop_chance,
            "rating": self.rating,
            "warnings": self.warnings,
        }


class LootAnalyzer:
    """
    Analyzes loot economy for hunt zones.

    Calculates:
      - Profit/hour based on average loot value per kill
      - Supply cost estimates based on monster difficulty
      - Net profit (profit - supply cost)
      - Rare drop chances and their impact on economy
      - Zone-level and cross-zone loot balance comparison

    Reference profit curves (standard Tibia):
      Low level:    5-20k profit/h
      Mid level:    20-100k profit/h
      High level:  100-500k profit/h
      Endgame:    500k-2M+ profit/h
    """

    # Reference profit ranges per level bracket (net profit/h)
    PROFIT_CURVES = {
        (0, 50):       (5000, 20000),
        (50, 100):     (20000, 60000),
        (100, 150):    (60000, 150000),
        (150, 200):    (150000, 300000),
        (200, 300):    (300000, 500000),
        (300, 400):    (500000, 800000),
        (400, 500):    (800000, 1200000),
        (500, 700):    (1200000, 2000000),
        (700, 1000):   (2000000, 3000000),
        (1000, 9999):  (3000000, 5000000),
    }

    # Supply cost per kill by monster difficulty
    SUPPLY_PER_KILL = {
        "easy": 500,
        "medium": 2000,
        "hard": 5000,
        "very_hard": 10000,
        "boss": 25000,
    }

    # Average loot value per kill by difficulty
    BASE_LOOT_VALUE = {
        "easy": 1000,
        "medium": 3000,
        "hard": 8000,
        "very_hard": 20000,
        "boss": 50000,
    }

    def __init__(self):
        self._analysis_cache: Dict[str, LootAnalysis] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_zone(self, zone_name: str, spawns: List[Dict[str, Any]],
                     loot_tables: Optional[Dict[str, List[Dict]]] = None,
                     monster_difficulties: Optional[Dict[str, str]] = None) -> LootAnalysis:
        """
        Analyze loot economy for a hunt zone.

        Args:
            zone_name: Name of the zone.
            spawns: List of spawn dicts with "name"/"monster" and "count".
            loot_tables: Dict mapping monster name → list of loot entries.
                         Each entry: {"id": int, "name": str, "chance": float, "value": int}
            monster_difficulties: Dict mapping monster name → difficulty.
                                  "easy", "medium", "hard", "very_hard", "boss"

        Returns:
            LootAnalysis with profit calculations and rating.
        """
        monster_difficulties = monster_difficulties or {}
        total_loot_per_hour = 0.0
        total_supply_per_hour = 0.0
        loot_breakdown: Dict[str, float] = {}
        rare_chance = 0.0
        total_kills = 0

        for spawn in spawns:
            monster_name = spawn.get("name", spawn.get("monster", ""))
            count = spawn.get("count", 1)
            difficulty = monster_difficulties.get(monster_name, "medium")

            supply_cost = self.SUPPLY_PER_KILL.get(difficulty, 2000)
            loot_table = loot_tables.get(monster_name, []) if loot_tables else []

            if loot_table:
                loot_value = self._calc_loot_per_kill(loot_table, monster_name, loot_breakdown)
                for entry in loot_table:
                    if entry.get("chance", 0) < 0.01:  # Rare drops
                        rare_chance += entry["chance"]
            else:
                loot_value = self.BASE_LOOT_VALUE.get(difficulty, 3000)

            kills_hour = self._kills_for_difficulty(difficulty)
            total_loot_per_hour += loot_value * kills_hour * count
            total_supply_per_hour += supply_cost * kills_hour * count
            total_kills += kills_hour * count

        profit = total_loot_per_hour - total_supply_per_hour

        # Calculate different modes
        profit_solo = self._adjust_for_mode(profit, "solo")
        profit_duo = self._adjust_for_mode(profit, "duo")
        profit_party = self._adjust_for_mode(profit, "party")

        # Determine optimal level from profit
        optimal_level = self._find_optimal_level(profit)

        # Rating
        rating = self._rate_profit(profit, optimal_level)
        warnings = self._generate_warnings(profit, profit_solo, total_kills)

        analysis = LootAnalysis(
            zone_name=zone_name,
            profit_per_hour=profit,
            profit_solo=profit_solo,
            profit_duo=profit_duo,
            profit_party=profit_party,
            supply_cost_per_hour=total_supply_per_hour,
            net_profit_per_hour=profit - total_supply_per_hour,
            rare_drop_chance=rare_chance,
            loot_value_breakdown=loot_breakdown,
            rating=rating,
            warnings=warnings,
        )

        self._analysis_cache[zone_name] = analysis
        return analysis

    def compare_zones(self, analyses: List[LootAnalysis]) -> Dict[str, Any]:
        """Compare profit across multiple zones."""
        if not analyses:
            return {}

        best = max(analyses, key=lambda a: a.profit_per_hour)
        worst = min(analyses, key=lambda a: a.profit_per_hour)

        return {
            "most_profitable": best.zone_name,
            "best_profit_h": best.profit_per_hour,
            "least_profitable": worst.zone_name,
            "worst_profit_h": worst.profit_per_hour,
            "avg_profit": sum(a.profit_per_hour for a in analyses) / len(analyses),
            "spread_ratio": best.profit_per_hour / max(worst.profit_per_hour, 1),
        }

    def suggest_loot_adjustment(self, analysis: LootAnalysis,
                                target_level: int = 150) -> Dict[str, Any]:
        """
        Suggest loot value adjustments.

        Returns:
            Dict with suggested multiplier.
        """
        target_lo, target_hi = self._profit_range_for_level(target_level)
        target = (target_lo + target_hi) / 2

        if target == 0:
            return {"adjustment": "none", "reason": "Cannot determine target"}

        ratio = target / max(analysis.profit_per_hour, 1)
        ratio = max(0.1, min(10.0, ratio))

        return {
            "adjustment": "multiply" if abs(ratio - 1.0) > 0.1 else "none",
            "loot_multiplier": round(ratio, 2),
            "target_profit_h": int(target),
            "current_profit_h": int(analysis.profit_per_hour),
            "target_level": target_level,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _calc_loot_per_kill(self, loot_table: List[Dict], monster_name: str,
                             breakdown: Dict[str, float]) -> float:
        """Calculate expected loot value per kill from a loot table."""
        total = 0.0
        for entry in loot_table:
            value = entry.get("value", 0)
            chance = entry.get("chance", 0)
            count = entry.get("count", 1)
            entry_total = value * chance * count
            total += entry_total

            name = entry.get("name", f"item_{entry.get('id', 0)}")
            breakdown[name] = breakdown.get(name, 0) + entry_total

        return total

    def _kills_for_difficulty(self, difficulty: str) -> float:
        """Estimate kills per hour based on monster difficulty."""
        base = {"easy": 200, "medium": 120, "hard": 60, "very_hard": 30, "boss": 5}
        return base.get(difficulty, 100)

    def _adjust_for_mode(self, profit: float, mode: str) -> float:
        """Adjust profit for different group sizes."""
        multipliers = {"solo": 1.0, "duo": 0.7, "party": 0.5}
        return profit * multipliers.get(mode, 1.0)

    def _find_optimal_level(self, profit: float) -> int:
        """Find the optimal level for this profit rate."""
        for (lo, hi), (min_p, max_p) in self.PROFIT_CURVES.items():
            if min_p <= profit <= max_p * 1.5:
                return lo
        if profit < 5000:
            return 1
        return 400

    def _profit_range_for_level(self, level: int) -> Tuple[float, float]:
        """Get expected profit range for a level."""
        for (lo, hi), (min_p, max_p) in self.PROFIT_CURVES.items():
            if lo <= level <= hi:
                return min_p, max_p
        return 0.0, 0.0

    def _rate_profit(self, profit: float, level: int) -> str:
        """Rate the profit level."""
        target_lo, target_hi = self._profit_range_for_level(level)
        if target_hi == 0:
            return "unknown"

        if profit <= 0:
            return "loss"
        elif profit < target_lo * 0.3:
            return "very_low"
        elif profit < target_lo * 0.6:
            return "low"
        elif profit <= target_hi:
            return "balanced"
        elif profit <= target_hi * 1.5:
            return "good"
        else:
            return "excellent"

    def _generate_warnings(self, profit: float, profit_solo: float,
                           total_kills: float) -> List[str]:
        """Generate economy warnings."""
        warnings = []

        if profit <= 0:
            warnings.append("Zone operates at a loss; players will not hunt here")
        elif profit < 10000:
            warnings.append("Very low profit; consider adding valuable drops")

        if total_kills > 500:
            warnings.append("High supply cost ratio; check if drops compensate")
        if profit_solo < profit * 0.3:
            warnings.append("Solo profit is very low; zone may be party-only")

        return warnings