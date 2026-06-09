"""
Combat Simulator — Models real Tibia-style combat for 5 vocations.

Simulates Knight, Paladin, Druid, Sorcerer, and Monk combat encounters
against monsters found in generated worlds. Calculates DPS, time-to-kill,
damage taken, and resource consumption.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .player_bot import Vocation, VocationStats

logger = logging.getLogger(__name__)


@dataclass
class MonsterStats:
    """Stats for a monster used in combat simulation."""
    name: str
    health: int
    attack: int
    defense: int
    magic_defense: int
    experience: int
    speed: int = 80
    is_boss: bool = False
    gold_min: int = 0
    gold_max: int = 0
    level: int = 1


@dataclass
class CombatResult:
    """Result of a simulated combat encounter."""
    monster_name: str
    vocation: str
    player_level: int
    damage_dealt: int
    damage_taken: int
    time_seconds: float
    health_remaining: int
    mana_remaining: int
    used_healing: bool
    died: bool
    experience_gained: int
    dps: float
    hps: float
    efficiency: float


@dataclass
class EncounterResult:
    """Result of fighting multiple monsters in a hunt rotation."""
    vocation: str
    player_level: int
    monsters_killed: int
    total_time: float
    total_damage_dealt: int
    total_damage_taken: int
    total_experience: int
    deaths: int
    average_dps: float
    experience_per_hour: float
    health_potions_used: int
    mana_potions_used: int
    results: List[CombatResult] = field(default_factory=list)


class CombatMode:
    SOLO = "solo"
    PARTY = "party"
    MASS = "mass"


# Vocation stats at level 300 for combat simulation
# These are combat-specific stats separate from the player_bot stats
VOCATION_COMBAT_PROFILES: Dict[Vocation, Dict[str, int]] = {
    Vocation.KNIGHT: {
        "health": 4800, "mana": 1400,
        "attack": 140, "defense": 120, "magic_defense": 50,
        "speed": 85, "sword_skill": 110, "shielding": 100,
        "melee_damage": 350, "spell_damage": 0,
        "healing": 0, "aoe_damage": 0,
        "mana_per_spell": 0, "health_per_attack": 0,
        "heal_amount": 0, "mana_per_heal": 0,
    },
    Vocation.PALADIN: {
        "health": 3200, "mana": 2800,
        "attack": 100, "defense": 80, "magic_defense": 70,
        "speed": 90, "sword_skill": 60, "shielding": 70,
        "distance_skill": 110,
        "melee_damage": 150, "spell_damage": 250,
        "healing": 200, "aoe_damage": 180,
        "mana_per_spell": 45, "health_per_attack": 0,
        "heal_amount": 400, "mana_per_heal": 70,
    },
    Vocation.DRUID: {
        "health": 2600, "mana": 4200,
        "attack": 40, "defense": 50, "magic_defense": 100,
        "speed": 80, "sword_skill": 30, "shielding": 50,
        "melee_damage": 80, "spell_damage": 350,
        "healing": 500, "aoe_damage": 400,
        "mana_per_spell": 60, "health_per_attack": 0,
        "heal_amount": 650, "mana_per_heal": 80,
    },
    Vocation.SORCERER: {
        "health": 2400, "mana": 4500,
        "attack": 30, "defense": 40, "magic_defense": 110,
        "speed": 82, "sword_skill": 20, "shielding": 40,
        "melee_damage": 60, "spell_damage": 420,
        "healing": 300, "aoe_damage": 500,
        "mana_per_spell": 70, "health_per_attack": 0,
        "heal_amount": 400, "mana_per_heal": 90,
    },
    Vocation.MONK: {
        "health": 3800, "mana": 2200,
        "attack": 120, "defense": 100, "magic_defense": 65,
        "speed": 95, "sword_skill": 90, "shielding": 85,
        "melee_damage": 300, "spell_damage": 200,
        "healing": 350, "aoe_damage": 250,
        "mana_per_spell": 35, "health_per_attack": 0,
        "heal_amount": 500, "mana_per_heal": 60,
    },
}


class CombatSimulator:
    """Simulates combat encounters between players and monsters."""

    HEAL_THRESHOLD = 0.6
    MANA_THRESHOLD = 0.3

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    def create_vocation_stats(self, vocation: Vocation, level: int):
        """Create scaled combat stats for a vocation at a given level."""
        base = VOCATION_COMBAT_PROFILES[vocation]
        scale = level / 300.0

        return {
            "vocation": vocation,
            "level": level,
            "health": int(base["health"] * scale),
            "mana": int(base["mana"] * scale),
            "attack": int(base["attack"] * scale),
            "defense": int(base["defense"] * scale),
            "magic_defense": int(base["magic_defense"] * scale),
            "melee_damage": int(base["melee_damage"] * scale),
            "spell_damage": int(base["spell_damage"] * scale),
            "heal_amount": int(base["heal_amount"] * scale),
            "mana_per_spell": base["mana_per_spell"],
            "mana_per_heal": base["mana_per_heal"],
            "shielding": int(base["shielding"] * scale),
        }

    def simulate_encounter(self, player_stats: dict, monster: MonsterStats, max_time: float = 30.0) -> CombatResult:
        """Simulate a single combat encounter."""
        hp = player_stats["health"]
        mp = player_stats["mana"]
        total_damage_dealt = 0
        total_damage_taken = 0
        time_elapsed = 0.0
        used_healing = False

        # Make a mutable copy of monster health
        monster_hp = monster.health

        while time_elapsed < max_time and hp > 0:
            time_elapsed += 1.0

            # Player turn
            if player_stats["spell_damage"] > 0 and mp >= player_stats["mana_per_spell"]:
                base_dmg = player_stats["spell_damage"]
                variance = self._rng.uniform(0.8, 1.2)
                raw = int(base_dmg * variance)
                mitigation = monster.magic_defense * 0.3
                dmg = max(1, int(raw - mitigation))
                mp -= player_stats["mana_per_spell"]
            elif player_stats["melee_damage"] > 0:
                base_dmg = player_stats["melee_damage"]
                variance = self._rng.uniform(0.85, 1.15)
                raw = int(base_dmg * variance)
                mitigation = monster.defense * 0.4
                dmg = max(1, int(raw - mitigation))
            else:
                dmg = 0

            if self._rng.random() < 0.05:
                dmg = int(dmg * 1.5)

            total_damage_dealt += dmg
            monster_hp -= dmg

            if monster_hp <= 0:
                break

            # Healing
            heal_threshold_hp = int(player_stats["health"] * self.HEAL_THRESHOLD)
            if hp <= heal_threshold_hp and player_stats["heal_amount"] > 0:
                if mp >= player_stats["mana_per_heal"]:
                    heal = int(player_stats["heal_amount"] * self._rng.uniform(0.9, 1.1))
                    hp = min(player_stats["health"], hp + heal)
                    mp -= player_stats["mana_per_heal"]
                    used_healing = True
                else:
                    potion_heal = int(player_stats["health"] * 0.25)
                    hp = min(player_stats["health"], hp + potion_heal)

            # Monster turn
            if self._rng.random() < 0.7:
                base_dmg = monster.attack
                variance = self._rng.uniform(0.8, 1.2)
                raw = int(base_dmg * variance)
                mitigation = (player_stats["defense"] + player_stats["shielding"] * 0.5) * 0.3
                dmg = max(1, int(raw - mitigation))
                total_damage_taken += dmg
                hp -= dmg

            mp = min(player_stats["mana"], int(mp + player_stats["mana"] * 0.01))

        died = hp <= 0
        dps = total_damage_dealt / max(time_elapsed, 1.0)
        hps = total_damage_taken / max(time_elapsed, 1.0)
        efficiency = total_damage_dealt / max(total_damage_taken, 1)

        return CombatResult(
            monster_name=monster.name,
            vocation=player_stats["vocation"].name.lower(),
            player_level=player_stats["level"],
            damage_dealt=total_damage_dealt,
            damage_taken=total_damage_taken,
            time_seconds=time_elapsed,
            health_remaining=max(0, hp),
            mana_remaining=max(0, mp),
            used_healing=used_healing,
            died=died,
            experience_gained=monster.experience if not died else 0,
            dps=dps,
            hps=hps,
            efficiency=efficiency,
        )

    def simulate_hunt_rotation(
        self, vocation: Vocation, level: int, monsters: List[MonsterStats],
        rotation_time_minutes: float = 60.0, respawn_seconds: int = 60,
    ) -> EncounterResult:
        """Simulate a full hunt rotation with respawning monsters."""
        rotation_seconds = rotation_time_minutes * 60.0
        monster_timers: Dict[int, float] = {i: 0.0 for i in range(len(monsters))}
        monster_hp: Dict[int, int] = {i: m.health for i, m in enumerate(monsters)}

        total_dealt = 0
        total_taken = 0
        total_xp = 0
        deaths = 0
        elapsed = 0.0
        kill_count = 0
        hp_potions = 0
        results: List[CombatResult] = []

        while elapsed < rotation_seconds:
            target_idx = None
            for i in range(len(monsters)):
                if monster_hp[i] > 0 and monster_timers[i] <= 0:
                    target_idx = i
                    break

            if target_idx is None:
                elapsed += 1.0
                for i in monster_timers:
                    if monster_hp[i] <= 0:
                        monster_timers[i] += 1.0
                        if monster_timers[i] >= respawn_seconds:
                            monster_hp[i] = monsters[i].health
                            monster_timers[i] = 0.0
                continue

            target = MonsterStats(
                name=monsters[target_idx].name, health=monster_hp[target_idx],
                attack=monsters[target_idx].attack, defense=monsters[target_idx].defense,
                magic_defense=monsters[target_idx].magic_defense,
                experience=monsters[target_idx].experience,
                speed=monsters[target_idx].speed, is_boss=monsters[target_idx].is_boss,
            )

            player_stats = self.create_vocation_stats(vocation, level)
            result = self.simulate_encounter(player_stats, target, max_time=30.0)
            results.append(result)

            elapsed += result.time_seconds
            total_dealt += result.damage_dealt
            total_taken += result.damage_taken
            total_xp += result.experience_gained

            if result.died:
                deaths += 1
            else:
                kill_count += 1
                monster_hp[target_idx] = max(0, monster_hp[target_idx] - result.damage_dealt)

            if result.used_healing:
                hp_potions += 1

        avg_dps = total_dealt / max(elapsed, 1.0)
        xp_per_hour = (total_xp / max(elapsed, 1.0)) * 3600.0

        return EncounterResult(
            vocation=vocation.name.lower(), player_level=level,
            monsters_killed=kill_count, total_time=elapsed,
            total_damage_dealt=total_dealt, total_damage_taken=total_taken,
            total_experience=total_xp, deaths=deaths, average_dps=avg_dps,
            experience_per_hour=xp_per_hour,
            health_potions_used=hp_potions, mana_potions_used=0, results=results,
        )

    def simulate_multi_vocation(self, level: int, monsters: List[MonsterStats], rotation_minutes: float = 60.0) -> Dict[str, EncounterResult]:
        """Simulate hunt rotation for all 5 vocations."""
        results = {}
        for vocation in Vocation:
            results[vocation.name.lower()] = self.simulate_hunt_rotation(
                vocation=vocation, level=level, monsters=monsters,
                rotation_time_minutes=rotation_minutes,
            )
        return results

    @staticmethod
    def create_monster(name, health, attack, defense, magic_defense, experience, speed=80, is_boss=False, gold_min=0, gold_max=0):
        return MonsterStats(name=name, health=health, attack=attack, defense=defense,
                           magic_defense=magic_defense, experience=experience,
                           speed=speed, is_boss=is_boss, gold_min=gold_min, gold_max=gold_max)