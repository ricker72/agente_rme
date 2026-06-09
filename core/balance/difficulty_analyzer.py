from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class DifficultyProfile:
    """Difficulty profile for a single monster, zone, or the map."""
    entity_name: str = ""
    difficulty_score: float = 0.0   # 0-100
    damage_dealt_min: int = 0
    damage_dealt_max: int = 0
    damage_taken: int = 0            # combined damage from all monsters
    health_pool: int = 0
    average_hits_to_kill: float = 0.0
    kill_time_seconds: float = 0.0
    player_death_chance: float = 0.0
    rating: str = ""                 # "trivial", "easy", "medium", "hard", "deadly", "impossible"
    concerns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_name": self.entity_name,
            "difficulty_score": self.difficulty_score,
            "rating": self.rating,
            "average_hits_to_kill": self.average_hits_to_kill,
            "player_death_chance": self.player_death_chance,
            "concerns": self.concerns,
        }


@dataclass
class DifficultyAnalysis:
    """Complete difficulty analysis for a zone."""
    zone_name: str = ""
    overall_score: float = 0.0
    min_difficulty: float = 0.0
    max_difficulty: float = 0.0
    avg_difficulty: float = 0.0
    difficulty_spread: float = 0.0
    monster_profiles: Dict[str, DifficultyProfile] = field(default_factory=dict)
    zone_rating: str = ""
    has_deadly_zones: bool = False
    has_too_easy_zones: bool = False
    recommended_level: int = 0
    spawns_too_dense: bool = False
    warnings: List[str] = field(default_factory=list)
    auto_balance_suggestions: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_name": self.zone_name,
            "overall_score": self.overall_score,
            "avg_difficulty": self.avg_difficulty,
            "difficulty_spread": self.difficulty_spread,
            "zone_rating": self.zone_rating,
            "has_deadly_zones": self.has_deadly_zones,
            "has_too_easy_zones": self.has_too_easy_zones,
            "recommended_level": self.recommended_level,
            "spawns_too_dense": self.spawns_too_dense,
            "warnings": self.warnings,
        }


class DifficultyAnalyzer:
    """
    Analyzes the difficulty of hunt zones and detects balance issues.

    Detects:
      - Zones that are too easy (trivial for intended level)
      - Zones that are impossible (deadly)
      - Difficulty spikes within a zone
      - Spawn density imbalances
      - Player death probability

    Uses a multi-factor difficulty model based on:
      - Monster damage output (e.g., 100-600 damage per hit)
      - Monster health pool (e.g., 1000-50000 HP)
      - Player defense at target level
      - Spawn density (how many active monsters at once)
      - Distance to safe zone
    """

    # Player stat approximations for different levels
    PLAYER_STATS = {
        (1, 20):     {"hp": 500,  "defense": 25,  "dps": 50,   "heal_per_sec": 30},
        (20, 50):    {"hp": 1200, "defense": 50,  "dps": 150,  "heal_per_sec": 80},
        (50, 100):   {"hp": 2500, "defense": 75,  "dps": 350,  "heal_per_sec": 150},
        (100, 200):  {"hp": 4000, "defense": 100, "dps": 600,  "heal_per_sec": 300},
        (200, 400):  {"hp": 6000, "defense": 130, "dps": 1000, "heal_per_sec": 500},
        (400, 700):  {"hp": 8500, "defense": 160, "dps": 1500, "heal_per_sec": 800},
        (700, 1000): {"hp": 11000, "defense": 190, "dps": 2000,"heal_per_sec": 1200},
        (1000, 9999):{"hp": 15000,"defense": 220, "dps": 3000,"heal_per_sec": 2000},
    }

    # Monster stat templates (estimated from standard Tibia)
    MONSTER_TEMPLATES = {
        "easy":     {"hp": 500,   "damage_min": 10,   "damage_max": 50,   "hit_chance": 0.3},
        "medium":   {"hp": 2000,  "damage_min": 80,   "damage_max": 250,  "hit_chance": 0.4},
        "hard":     {"hp": 5000,  "damage_min": 200,  "damage_max": 600,  "hit_chance": 0.5},
        "very_hard":{"hp": 12000, "damage_min": 400,  "damage_max": 1200, "hit_chance": 0.6},
        "boss":     {"hp": 50000, "damage_min": 800,  "damage_max": 2500, "hit_chance": 0.7},
    }

    def __init__(self):
        self._analysis_cache: Dict[str, DifficultyAnalysis] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def analyze_zone(self, zone_name: str, spawns: List[Dict[str, Any]],
                     monster_difficulties: Optional[Dict[str, str]] = None,
                     player_level: int = 150) -> DifficultyAnalysis:
        """
        Analyze the difficulty of a hunt zone.

        Args:
            zone_name: Name of the zone.
            spawns: List of spawn dicts with "name"/"monster" and "count".
            monster_difficulties: Dict mapping monster name → difficulty.
            player_level: Target player level for the analysis.

        Returns:
            DifficultyAnalysis with scores, ratings, and concerns.
        """
        monster_difficulties = monster_difficulties or {}
        player_stats = self._get_player_stats(player_level)

        monster_profiles: Dict[str, DifficultyProfile] = {}
        total_damage_per_round = 0
        total_health = 0
        total_dps_to_player = 0
        difficulties = []

        # Analyze each monster type
        for spawn in spawns:
            monster_name = spawn.get("name", spawn.get("monster", ""))
            count = spawn.get("count", 1)
            difficulty_tag = monster_difficulties.get(monster_name, "medium")

            template = self.MONSTER_TEMPLATES.get(difficulty_tag, self.MONSTER_TEMPLATES["medium"])
            monster_hp = template["hp"]
            dmg_min = template["damage_min"]
            dmg_max = template["damage_max"]
            hit_chance = template["hit_chance"]

            # Calculate how many hits to kill the monster
            hits_to_kill = monster_hp / max(player_stats["dps"], 1)
            kill_time = hits_to_kill  # seconds (simplified)

            # Damage this monster deals to player per round
            avg_dmg = (dmg_min + dmg_max) / 2 * hit_chance

            # Difficulty score for this monster type
            def_effective = player_stats["defense"]
            heal_per_sec = player_stats["heal_per_sec"]
            damage_per_second = avg_dmg * count * 0.17  # ~17% of monsters active at once
            net_damage = max(0, damage_per_second - heal_per_sec)
            time_to_die = player_stats["hp"] / max(net_damage, 1) if net_damage > 0 else 999

            death_chance = max(0, min(1, 1.0 - (time_to_die / 60)))  # Death within 60s

            difficulty_score = self._calc_difficulty_score(
                avg_dmg, monster_hp, count, player_stats
            )
            rating = self._rate_difficulty(difficulty_score, death_chance)

            profile = DifficultyProfile(
                entity_name=monster_name,
                difficulty_score=difficulty_score,
                damage_dealt_min=dmg_min,
                damage_dealt_max=dmg_max * count,
                damage_taken=int(avg_dmg * count),
                health_pool=monster_hp,
                average_hits_to_kill=round(hits_to_kill, 1),
                kill_time_seconds=round(kill_time, 1),
                player_death_chance=round(death_chance, 3),
                rating=rating,
                concerns=self._get_concerns(difficulty_score, death_chance, count),
            )

            monster_profiles[monster_name] = profile
            total_damage_per_round += avg_dmg * count
            total_health += monster_hp * count
            total_dps_to_player += damage_per_second
            difficulties.append(difficulty_score)

        # Zone-level analysis
        if not difficulties:
            return DifficultyAnalysis(zone_name=zone_name, zone_rating="unknown")

        avg_difficulty = sum(difficulties) / len(difficulties)
        min_d = min(difficulties)
        max_d = max(difficulties)
        spread = max_d - min_d

        # Spawn density
        spawns_too_dense = len(spawns) > 15 and total_damage_per_round > 10000

        overall = self._calc_overall_difficulty(difficulties, total_dps_to_player, player_stats)
        rating = self._rate_difficulty(overall, 0)
        recommended = self._recommend_level(overall)

        has_deadly = any(p.rating == "impossible" or p.rating == "deadly" for p in monster_profiles.values())
        has_easy = any(p.rating == "trivial" for p in monster_profiles.values())

        warnings = self._generate_warnings(overall, spread, spawns_too_dense, has_deadly, has_easy)

        # Auto-balance suggestions
        suggestions = self._auto_balance(overall, recommended, spawns, monster_profiles, monster_difficulties)

        analysis = DifficultyAnalysis(
            zone_name=zone_name,
            overall_score=overall,
            min_difficulty=min_d,
            max_difficulty=max_d,
            avg_difficulty=avg_difficulty,
            difficulty_spread=spread,
            monster_profiles=monster_profiles,
            zone_rating=rating,
            has_deadly_zones=has_deadly,
            has_too_easy_zones=has_easy,
            recommended_level=recommended,
            spawns_too_dense=spawns_too_dense,
            warnings=warnings,
            auto_balance_suggestions=suggestions,
        )

        self._analysis_cache[zone_name] = analysis
        return analysis

    def compare_zones(self, analyses: List[DifficultyAnalysis]) -> Dict[str, Any]:
        """Compare difficulty across multiple zones."""
        if not analyses:
            return {}

        hardest = max(analyses, key=lambda a: a.overall_score)
        easiest = min(analyses, key=lambda a: a.overall_score)

        return {
            "hardest_zone": hardest.zone_name,
            "hardest_score": hardest.overall_score,
            "easiest_zone": easiest.zone_name,
            "easiest_score": easiest.overall_score,
            "avg_difficulty": sum(a.overall_score for a in analyses) / len(analyses),
            "deadly_zones": [a.zone_name for a in analyses if a.has_deadly_zones],
            "easy_zones": [a.zone_name for a in analyses if a.has_too_easy_zones],
        }

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def _calc_difficulty_score(self, avg_damage: float, monster_hp: float,
                                count: int, player_stats: Dict[str, float]) -> float:
        """Calculate difficulty score (0-100) for a monster type."""
        damage_ratio = avg_damage / max(player_stats["defense"], 1)
        hp_ratio = monster_hp / max(player_stats["hp"], 1)
        density_factor = 1 + (count - 1) * 0.15

        score = (damage_ratio * 25 + hp_ratio * 30) * density_factor
        return min(100, max(0, score))

    def _calc_overall_difficulty(self, difficulties: List[float],
                                  dps_to_player: float,
                                  player_stats: Dict[str, float]) -> float:
        """Calculate overall zone difficulty."""
        if not difficulties:
            return 0.0

        avg = sum(difficulties) / len(difficulties)
        max_d = max(difficulties)

        # Death probability factor
        heal = player_stats.get("heal_per_sec", 100)
        net_dps = max(0, dps_to_player - heal)
        death_factor = min(1.0, net_dps / player_stats.get("hp", 2000) * 10)

        overall = avg * 0.6 + max_d * 0.3 + death_factor * 10 * 0.1
        return min(100, max(0, overall))

    def _rate_difficulty(self, score: float, death_chance: float) -> str:
        """Rate difficulty based on score and death probability."""
        if death_chance > 0.5 or score > 90:
            return "impossible"
        if death_chance > 0.2 or score > 75:
            return "deadly"
        if score > 55:
            return "hard"
        if score > 35:
            return "medium"
        if score > 15:
            return "easy"
        return "trivial"

    def _get_concerns(self, difficulty: float, death_chance: float,
                       count: int) -> List[str]:
        """Get specific concerns about this monster type."""
        concerns = []
        if death_chance > 0.5:
            concerns.append("Extremely lethal; players will die frequently")
        elif death_chance > 0.2:
            concerns.append("High death risk; requires skilled play")

        if difficulty > 80:
            concerns.append("Overpowered; consider reducing damage or count")
        if difficulty < 10 and count > 10:
            concerns.append("Too many weak monsters; consider reducing count")
        if count > 8:
            concerns.append("High spawn count may cause overcrowding")

        return concerns

    def _recommend_level(self, difficulty: float) -> int:
        """Recommend a player level based on difficulty."""
        if difficulty > 80:
            return 400
        elif difficulty > 60:
            return 250
        elif difficulty > 40:
            return 150
        elif difficulty > 20:
            return 80
        elif difficulty > 10:
            return 30
        return 1

    def _generate_warnings(self, overall: float, spread: float,
                           spawns_too_dense: bool, has_deadly: bool,
                           has_easy: bool) -> List[str]:
        """Generate zone-level warnings."""
        warnings = []
        if has_deadly:
            warnings.append("Zone has deadly monsters; review difficulty balance")
        if has_easy and overall > 40:
            warnings.append("Mixed difficulty: easy and hard monsters together")
        if spawns_too_dense:
            warnings.append("Spawns too dense; players may be overwhelmed")
        if overall < 10:
            warnings.append("Zone is trivial; increase monster damage/HP")
        if overall > 85:
            warnings.append("Zone is nearly impossible; reduce monster stats")
        if spread > 40:
            warnings.append(f"Large difficulty spread ({spread:.0f}); inconsistent experience")
        return warnings

    # ------------------------------------------------------------------
    # Auto-balance
    # ------------------------------------------------------------------

    def _auto_balance(self, overall: float, recommended_level: int,
                       spawns: List[Dict], profiles: Dict[str, DifficultyProfile],
                       difficulties: Dict[str, str]) -> Dict[str, Any]:
        """Generate auto-balance suggestions."""
        suggestions: Dict[str, Any] = {}
        adjustments: List[Dict[str, Any]] = []

        if overall > 75:
            # Zone is too hard → reduce difficulty
            suggestions["action"] = "reduce_difficulty"
            suggestions["target_score"] = 50
            for monster_name, profile in profiles.items():
                if profile.difficulty_score > 70:
                    difficulty_tag = difficulties.get(monster_name, "medium")
                    new_tag = self._lower_difficulty(difficulty_tag)
                    adjustments.append({
                        "monster": monster_name,
                        "current_difficulty": difficulty_tag,
                        "suggested_difficulty": new_tag,
                        "reason": "Too hard for recommended level",
                    })

        elif overall < 15:
            # Zone is too easy → increase difficulty
            suggestions["action"] = "increase_difficulty"
            suggestions["target_score"] = 35
            for monster_name, profile in profiles.items():
                if profile.difficulty_score < 10:
                    difficulty_tag = difficulties.get(monster_name, "easy")
                    new_tag = self._raise_difficulty(difficulty_tag)
                    adjustments.append({
                        "monster": monster_name,
                        "current_difficulty": difficulty_tag,
                        "suggested_difficulty": new_tag,
                        "reason": "Too easy for recommended level",
                    })

        else:
            suggestions["action"] = "none"

        suggestions["adjustments"] = adjustments

        # Spawn count adjustments
        if len(spawns) > 15:
            suggestions["reduce_spawns"] = len(spawns) - 10
        if len(spawns) < 3 and overall > 30:
            suggestions["increase_spawns"] = 5 - len(spawns)

        return suggestions

    def _lower_difficulty(self, difficulty: str) -> str:
        levels = ["boss", "very_hard", "hard", "medium", "easy"]
        idx = levels.index(difficulty) if difficulty in levels else 3
        return levels[min(len(levels) - 1, idx + 1)]

    def _raise_difficulty(self, difficulty: str) -> str:
        levels = ["easy", "medium", "hard", "very_hard", "boss"]
        idx = levels.index(difficulty) if difficulty in levels else 0
        return levels[min(len(levels) - 1, idx + 1)]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_player_stats(self, level: int) -> Dict[str, float]:
        """Get player stats for a given level."""
        for (lo, hi), stats in self.PLAYER_STATS.items():
            if lo <= level <= hi:
                return stats
        return list(self.PLAYER_STATS.values())[-1]
