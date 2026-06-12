"""
Playtest Engine — Main orchestrator for automated world playtesting.

Integrates with WorldModel to extract zones, spawns, and structures,
then runs all analyzers to produce a comprehensive playtest report.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

from ..world.world_model import WorldModel
from ..world.region import Region
from ..world.structure import Structure

from .combat_simulator import CombatSimulator, MonsterStats
from .pathfinder import Pathfinder
from .loot_simulator import LootSimulator
from .survival_analyzer import SurvivalAnalyzer
from .difficulty_evaluator import DifficultyEvaluator
from .progression_analyzer import ProgressionAnalyzer
from .report_generator import PlaytestReport, ReportGenerator

logger = logging.getLogger(__name__)

# ── Default Monster Database (real Tibia stats) ──
DEFAULT_MONSTERS: Dict[str, Dict[str, int]] = {
    "Rat": {
        "health": 20,
        "attack": 5,
        "defense": 2,
        "magic_defense": 2,
        "experience": 5,
        "level": 1,
    },
    "Rotworm": {
        "health": 65,
        "attack": 15,
        "defense": 8,
        "magic_defense": 5,
        "experience": 40,
        "level": 8,
    },
    "Goblin": {
        "health": 80,
        "attack": 18,
        "defense": 10,
        "magic_defense": 8,
        "experience": 60,
        "level": 10,
    },
    "Orc": {
        "health": 115,
        "attack": 25,
        "defense": 15,
        "magic_defense": 10,
        "experience": 80,
        "level": 12,
    },
    "Orc Shaman": {
        "health": 170,
        "attack": 35,
        "defense": 18,
        "magic_defense": 40,
        "experience": 150,
        "level": 18,
    },
    "Minotaur": {
        "health": 200,
        "attack": 40,
        "defense": 25,
        "magic_defense": 15,
        "experience": 180,
        "level": 20,
    },
    "Skeleton": {
        "health": 250,
        "attack": 45,
        "defense": 30,
        "magic_defense": 20,
        "experience": 200,
        "level": 25,
    },
    "Vampire": {
        "health": 550,
        "attack": 70,
        "defense": 40,
        "magic_defense": 35,
        "experience": 525,
        "level": 40,
    },
    "Dragon": {
        "health": 1000,
        "attack": 100,
        "defense": 60,
        "magic_defense": 50,
        "experience": 700,
        "level": 50,
    },
    "Hydra": {
        "health": 2100,
        "attack": 150,
        "defense": 80,
        "magic_defense": 70,
        "experience": 1500,
        "level": 80,
    },
    "Demon": {
        "health": 5000,
        "attack": 300,
        "defense": 200,
        "magic_defense": 180,
        "experience": 3500,
        "level": 120,
    },
    "Grim Reaper": {
        "health": 8000,
        "attack": 450,
        "defense": 250,
        "magic_defense": 200,
        "experience": 6000,
        "level": 180,
    },
    "Behemoth": {
        "health": 12000,
        "attack": 550,
        "defense": 300,
        "magic_defense": 250,
        "experience": 10000,
        "level": 250,
    },
    "Dragon Lord": {
        "health": 15000,
        "attack": 650,
        "defense": 350,
        "magic_defense": 300,
        "experience": 12000,
        "level": 300,
    },
    "Werewolf": {
        "health": 3000,
        "attack": 180,
        "defense": 100,
        "magic_defense": 80,
        "experience": 2000,
        "level": 100,
    },
    "Lizard Guard": {
        "health": 1800,
        "attack": 130,
        "defense": 90,
        "magic_defense": 60,
        "experience": 1200,
        "level": 70,
    },
    "Lizard High Guard": {
        "health": 3500,
        "attack": 220,
        "defense": 150,
        "magic_defense": 100,
        "experience": 2800,
        "level": 110,
    },
    "Giant Spider": {
        "health": 4500,
        "attack": 280,
        "defense": 180,
        "magic_defense": 120,
        "experience": 3000,
        "level": 100,
    },
    "Diabolic Imp": {
        "health": 7000,
        "attack": 400,
        "defense": 220,
        "magic_defense": 190,
        "experience": 5500,
        "level": 160,
    },
    "Ancient Scarab": {
        "health": 6500,
        "attack": 380,
        "defense": 200,
        "magic_defense": 170,
        "experience": 5000,
        "level": 150,
    },
}

# ── Boss Templates ──
DEFAULT_BOSSES: Dict[str, Dict[str, int]] = {
    "Dragon Lord": {
        "health": 15000,
        "attack": 650,
        "defense": 350,
        "magic_defense": 300,
        "experience": 12000,
        "level": 300,
        "is_boss": True,
    },
    "Demon": {
        "health": 8000,
        "attack": 400,
        "defense": 250,
        "magic_defense": 200,
        "experience": 5000,
        "level": 200,
        "is_boss": True,
    },
}


class PlaytestEngine:
    """
    Main playtest orchestrator.

    Usage:
        engine = PlaytestEngine(seed=42)
        report = engine.run(world_model)
        assert report.playable
    """

    def __init__(
        self,
        seed: Optional[int] = None,
        player_level: int = 300,
        rotation_minutes: float = 60.0,
    ):
        """
        Args:
            seed: Random seed for deterministic simulation
            player_level: Default player level for simulation
            rotation_minutes: Hunt rotation duration in minutes
        """
        self._seed = seed
        self._player_level = player_level
        self._rotation_minutes = rotation_minutes

        self._combat = CombatSimulator(seed)
        self._loot = LootSimulator(seed)
        self._survival = SurvivalAnalyzer(seed)
        self._difficulty = DifficultyEvaluator(seed)
        self._progression = ProgressionAnalyzer(seed)
        self._report_gen = ReportGenerator()

    def run(self, world: WorldModel, level: Optional[int] = None) -> PlaytestReport:
        """
        Run complete playtest on a WorldModel.

        Args:
            world: The WorldModel to analyze
            level: Override player level

        Returns:
            PlaytestReport with all metrics and verdict
        """
        player_level = level or self._player_level

        # ── Step 1: Extract world data ──
        zones = self._extract_zones(world)
        spawns = self._extract_spawns(world)
        self._extract_structures(world)
        total_spawns = len(spawns)

        # ── Step 2: Build monster pool ──
        zone_monsters = self._build_zone_monsters(zones, spawns, player_level)

        if not zone_monsters:
            # Fallback: use default monsters based on level
            zone_monsters = self._default_zone_monsters(player_level)

        # ── Step 3: Run combat simulation ──
        all_monsters_flat = []
        for monsters in zone_monsters.values():
            all_monsters_flat.extend(monsters)

        if not all_monsters_flat:
            all_monsters_flat = self._default_monster_list(player_level)

        vocation_results = self._combat.simulate_multi_vocation(
            level=player_level,
            monsters=all_monsters_flat,
            rotation_minutes=self._rotation_minutes,
        )

        # ── Step 4: Calculate metrics ──
        avg_xp = sum(r.experience_per_hour for r in vocation_results.values()) / max(
            len(vocation_results), 1
        )
        avg_loot = sum(
            r.experience_per_hour * 0.2 for r in vocation_results.values()
        ) / max(len(vocation_results), 1)
        total_deaths = sum(r.deaths for r in vocation_results.values())

        voc_results_dict = {}
        for voc_name, enc in vocation_results.items():
            voc_results_dict[voc_name] = {
                "xp_per_hour": enc.experience_per_hour,
                "deaths": enc.deaths,
                "monsters_killed": enc.monsters_killed,
                "damage_per_second": enc.average_dps,
            }

        # ── Step 5: Pathfinding analysis ──
        pathfinder = Pathfinder(world)
        spawn_pos = self._find_entry_point(world)

        # ── Step 6: Survival analysis ──
        survival_report = self._survival.analyze_world(
            zones=zone_monsters,
            level=player_level,
            pathfinder=pathfinder if spawn_pos else None,
            spawn_pos=spawn_pos,
        )

        # ── Step 7: Difficulty analysis ──
        difficulty_input = {}
        for zone_name, monsters in zone_monsters.items():
            avg_monster_level = sum(m.level for m in monsters) / max(len(monsters), 1)
            difficulty_input[zone_name] = {
                "spawn_count": len(monsters),
                "total_tiles": 2500,
                "monster_avg_level": int(avg_monster_level),
                "has_boss": any(m.is_boss for m in monsters),
                "has_healing": False,
                "monster_xp": sum(m.experience for m in monsters)
                // max(len(monsters), 1),
            }

        diff_report = self._difficulty.evaluate_world(difficulty_input, player_level)

        # ── Step 8: Progression analysis ──
        level_min = max(1, player_level - 100)
        level_max = player_level + 100
        prog_report = self._progression.analyze_progression_curve(
            zones=zone_monsters,
            level_min=level_min,
            level_max=level_max,
            level_step=50,
        )

        # ── Step 9: Collect issues ──
        all_issues = []
        all_issues.extend(diff_report.issues)
        all_issues.extend(survival_report.recommendations[:3])
        all_issues.extend(prog_report.recommendations[:3])

        all_recs = list(diff_report.recommendations)

        # ── Step 10: Generate report ──
        report = self._report_gen.generate(
            xp_per_hour=avg_xp,
            loot_per_hour=avg_loot,
            deaths=total_deaths,
            issues=all_issues,
            recommendations=all_recs,
            survival_rate=survival_report.overall_survival_rate,
            progression_smoothness=prog_report.curve_smoothness,
            difficulty_score=diff_report.difficulty_score,
            difficulty_label=diff_report.overall_difficulty,
            zone_count=len(zone_monsters),
            total_spawns=total_spawns,
            vocation_results=voc_results_dict,
        )

        return report

    def _extract_zones(self, world: WorldModel) -> Dict[str, Region]:
        """Extract named zones from the world."""
        zones: Dict[str, Region] = {}
        for region in world.regions:
            name = region.name or f"zone_{len(zones)}"
            zones[name] = region
        return zones

    def _extract_spawns(self, world: WorldModel) -> List[Tuple[str, int, int, int]]:
        """Extract all monster spawn positions."""
        spawns = []
        for key, tile in world.tiles.items():
            if tile.spawn is not None:
                spawns.append((tile.spawn.monster, tile.x, tile.y, tile.z))
        return spawns

    def _extract_structures(self, world: WorldModel) -> List[Structure]:
        """Extract all structures."""
        return list(world.structures)

    def _build_zone_monsters(
        self,
        zones: Dict[str, Region],
        spawns: List[Tuple[str, int, int, int]],
        player_level: int,
    ) -> Dict[str, List[MonsterStats]]:
        """Build monster lists per zone from spawn data."""
        zone_monsters: Dict[str, List[MonsterStats]] = {}

        zone_names = list(zones.keys()) if zones else ["main"]

        for idx, (monster_name, x, y, z) in enumerate(spawns):
            # Distribute spawns across available zones round-robin
            zone_name = zone_names[idx % len(zone_names)]

            stats = self._resolve_monster(monster_name, player_level)
            if zone_name not in zone_monsters:
                zone_monsters[zone_name] = []
            zone_monsters[zone_name].append(stats)

        return zone_monsters

    def _resolve_monster(self, name: str, player_level: int) -> MonsterStats:
        """Resolve a monster by name from the database."""
        # Check default monsters (exact match)
        if name in DEFAULT_MONSTERS:
            data = DEFAULT_MONSTERS[name]
            return MonsterStats(
                name=name,
                health=data["health"],
                attack=data["attack"],
                defense=data["defense"],
                magic_defense=data["magic_defense"],
                experience=data["experience"],
                speed=data.get("speed", 80),
                is_boss=False,
            )

        # Check bosses
        if name in DEFAULT_BOSSES:
            data = DEFAULT_BOSSES[name]
            return MonsterStats(
                name=name,
                health=data["health"],
                attack=data["attack"],
                defense=data["defense"],
                magic_defense=data["magic_defense"],
                experience=data["experience"],
                speed=data.get("speed", 80),
                is_boss=True,
            )

        # Fallback: generate stats based on level
        return MonsterStats(
            name=name,
            health=max(50, player_level * 15),
            attack=max(10, player_level * 0.8),
            defense=max(5, player_level * 0.4),
            magic_defense=max(5, player_level * 0.3),
            experience=max(10, player_level * 10),
            speed=80,
        )

    def _default_zone_monsters(
        self, player_level: int
    ) -> Dict[str, List[MonsterStats]]:
        """Create default monster list based on player level."""
        # Select appropriate monsters for level range
        appropriate = []
        for name, data in DEFAULT_MONSTERS.items():
            if data["level"] <= player_level * 1.2:
                appropriate.append(name)

        if not appropriate:
            appropriate = ["Rat", "Rotworm"]

        # Pick top 3-5 appropriate monsters
        selected = appropriate[-5:] if len(appropriate) > 5 else appropriate
        monsters = [self._resolve_monster(name, player_level) for name in selected]

        return {"hunt_default": monsters}

    def _default_monster_list(self, player_level: int) -> List[MonsterStats]:
        """Default flat monster list for combat simulation."""
        zone = self._default_zone_monsters(player_level)
        all_monsters = []
        for monsters in zone.values():
            all_monsters.extend(monsters)
        return (
            all_monsters
            if all_monsters
            else [
                MonsterStats(
                    name="Rat",
                    health=20,
                    attack=5,
                    defense=2,
                    magic_defense=2,
                    experience=5,
                    speed=80,
                )
            ]
        )

    def _find_entry_point(self, world: WorldModel) -> Optional[Tuple[int, int, int]]:
        """Find a walkable entry point in the world."""
        for key, tile in world.tiles.items():
            if tile.ground is not None and tile.spawn is None:
                return (tile.x, tile.y, tile.z)
        # Fallback: first tile
        for key, tile in world.tiles.items():
            return (tile.x, tile.y, tile.z)
        return None

    def run_quick(
        self, world: WorldModel, level: Optional[int] = None
    ) -> PlaytestReport:
        """
        Quick playtest with reduced analysis.

        Skips progression curve analysis for faster results.
        """
        player_level = level or self._player_level

        zones = self._extract_zones(world)
        spawns = self._extract_spawns(world)
        total_spawns = len(spawns)

        zone_monsters = self._build_zone_monsters(zones, spawns, player_level)
        if not zone_monsters:
            zone_monsters = self._default_zone_monsters(player_level)

        all_monsters_flat = []
        for monsters in zone_monsters.values():
            all_monsters_flat.extend(monsters)
        if not all_monsters_flat:
            all_monsters_flat = self._default_monster_list(player_level)

        vocation_results = self._combat.simulate_multi_vocation(
            level=player_level,
            monsters=all_monsters_flat,
            rotation_minutes=max(self._rotation_minutes, 10.0),
        )

        avg_xp = sum(r.experience_per_hour for r in vocation_results.values()) / max(
            len(vocation_results), 1
        )
        avg_loot = avg_xp * 0.2
        total_deaths = sum(r.deaths for r in vocation_results.values())

        voc_results_dict = {}
        for voc_name, enc in vocation_results.items():
            voc_results_dict[voc_name] = {
                "xp_per_hour": enc.experience_per_hour,
                "deaths": enc.deaths,
                "monsters_killed": enc.monsters_killed,
            }

        # Quick difficulty check
        diff_input = {}
        for zone_name, monsters in zone_monsters.items():
            avg_lvl = sum(m.level for m in monsters) / max(len(monsters), 1)
            diff_input[zone_name] = {
                "spawn_count": len(monsters),
                "total_tiles": 2500,
                "monster_avg_level": int(avg_lvl),
                "has_boss": any(m.is_boss for m in monsters),
                "has_healing": False,
                "monster_xp": sum(m.experience for m in monsters)
                // max(len(monsters), 1),
            }

        diff_report = self._difficulty.evaluate_world(diff_input, player_level)

        survival_rate = 1.0 - (total_deaths / max(len(vocation_results) * 5, 1))

        return self._report_gen.generate(
            xp_per_hour=avg_xp,
            loot_per_hour=avg_loot,
            deaths=total_deaths,
            issues=diff_report.issues,
            recommendations=diff_report.recommendations,
            survival_rate=max(0.0, min(1.0, survival_rate)),
            progression_smoothness=1.0,
            difficulty_score=diff_report.difficulty_score,
            difficulty_label=diff_report.overall_difficulty,
            zone_count=len(zone_monsters),
            total_spawns=total_spawns,
            vocation_results=voc_results_dict,
        )
