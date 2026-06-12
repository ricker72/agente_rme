"""Tests for the Combat Simulator."""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.playtest.combat_simulator import (
    CombatSimulator,
    MonsterStats,
    CombatResult,
    EncounterResult,
)
from core.playtest.player_bot import Vocation


@pytest.fixture
def sim():
    return CombatSimulator(seed=42)


@pytest.fixture
def dragon():
    return MonsterStats(
        name="Dragon",
        health=1000,
        attack=100,
        defense=60,
        magic_defense=50,
        experience=700,
        speed=80,
    )


@pytest.fixture
def rat():
    return MonsterStats(
        name="Rat",
        health=20,
        attack=5,
        defense=2,
        magic_defense=2,
        experience=5,
        speed=80,
    )


@pytest.fixture
def boss():
    return MonsterStats(
        name="Demon",
        health=8000,
        attack=400,
        defense=250,
        magic_defense=200,
        experience=5000,
        speed=80,
        is_boss=True,
    )


class TestVocationStats:
    def test_create_knight(self, sim):
        stats = sim.create_vocation_stats(Vocation.KNIGHT, 300)
        assert stats["vocation"] == Vocation.KNIGHT
        assert stats["level"] == 300
        assert stats["health"] > 0
        assert stats["mana"] > 0
        assert stats["melee_damage"] > 0
        assert stats["spell_damage"] == 0  # Knight uses melee

    def test_create_druid(self, sim):
        stats = sim.create_vocation_stats(Vocation.DRUID, 300)
        assert stats["vocation"] == Vocation.DRUID
        assert stats["spell_damage"] > 0
        assert stats["heal_amount"] > 0
        assert stats["mana_per_spell"] > 0

    def test_create_sorcerer(self, sim):
        stats = sim.create_vocation_stats(Vocation.SORCERER, 300)
        assert stats["vocation"] == Vocation.SORCERER
        assert stats["spell_damage"] > stats["melee_damage"]

    def test_create_paladin(self, sim):
        stats = sim.create_vocation_stats(Vocation.PALADIN, 300)
        assert stats["vocation"] == Vocation.PALADIN
        assert stats["spell_damage"] > 0

    def test_create_monk(self, sim):
        stats = sim.create_vocation_stats(Vocation.MONK, 300)
        assert stats["vocation"] == Vocation.MONK
        assert stats["melee_damage"] > 0
        assert stats["heal_amount"] > 0

    def test_scaling_level_150(self, sim):
        stats_300 = sim.create_vocation_stats(Vocation.KNIGHT, 300)
        stats_150 = sim.create_vocation_stats(Vocation.KNIGHT, 150)
        assert stats_300["health"] > stats_150["health"]
        assert stats_300["melee_damage"] > stats_150["melee_damage"]

    def test_scaling_level_600(self, sim):
        stats_300 = sim.create_vocation_stats(Vocation.KNIGHT, 300)
        stats_600 = sim.create_vocation_stats(Vocation.KNIGHT, 600)
        assert stats_600["health"] > stats_300["health"]


class TestCombatEncounter:
    def test_knight_vs_rat(self, sim):
        player = sim.create_vocation_stats(Vocation.KNIGHT, 300)
        target = MonsterStats(
            name="Rat",
            health=20,
            attack=5,
            defense=2,
            magic_defense=2,
            experience=5,
            speed=80,
        )
        result = sim.simulate_encounter(player, target)
        assert isinstance(result, CombatResult)
        assert result.monster_name == "Rat"
        assert result.vocation == "knight"
        assert result.damage_dealt > 0
        assert not result.died  # Knight should kill rat easily
        assert result.experience_gained == 5
        assert result.time_seconds > 0
        assert result.dps > 0

    def test_knight_vs_dragon(self, sim):
        player = sim.create_vocation_stats(Vocation.KNIGHT, 300)
        target = MonsterStats(
            name="Dragon",
            health=1000,
            attack=100,
            defense=60,
            magic_defense=50,
            experience=700,
            speed=80,
        )
        result = sim.simulate_encounter(player, target)
        assert result.damage_dealt > 0
        assert result.time_seconds > 0

    def test_druid_heals(self, sim):
        player = sim.create_vocation_stats(Vocation.DRUID, 300)
        # High attack monster to force healing
        target = MonsterStats(
            name="Boss",
            health=5000,
            attack=300,
            defense=200,
            magic_defense=100,
            experience=3000,
            speed=80,
        )
        result = sim.simulate_encounter(player, target)
        assert result.damage_dealt > 0
        assert result.time_seconds > 0

    def test_sorcerer_spell_attack(self, sim):
        player = sim.create_vocation_stats(Vocation.SORCERER, 300)
        target = MonsterStats(
            name="Hydra",
            health=2100,
            attack=150,
            defense=80,
            magic_defense=70,
            experience=1500,
            speed=80,
        )
        result = sim.simulate_encounter(player, target)
        assert result.damage_dealt > 0

    def test_deterministic_with_seed(self):
        sim1 = CombatSimulator(seed=123)
        sim2 = CombatSimulator(seed=123)
        player1 = sim1.create_vocation_stats(Vocation.KNIGHT, 300)
        player2 = sim2.create_vocation_stats(Vocation.KNIGHT, 300)
        monster = MonsterStats(
            name="Dragon",
            health=1000,
            attack=100,
            defense=60,
            magic_defense=50,
            experience=700,
            speed=80,
        )
        r1 = sim1.simulate_encounter(player1, monster)
        monster2 = MonsterStats(
            name="Dragon",
            health=1000,
            attack=100,
            defense=60,
            magic_defense=50,
            experience=700,
            speed=80,
        )
        r2 = sim2.simulate_encounter(player2, monster2)
        assert r1.damage_dealt == r2.damage_dealt
        assert r1.time_seconds == r2.time_seconds

    def test_efficiency_ratio(self, sim):
        player = sim.create_vocation_stats(Vocation.KNIGHT, 300)
        target = MonsterStats(
            name="Rat",
            health=20,
            attack=5,
            defense=2,
            magic_defense=2,
            experience=5,
            speed=80,
        )
        result = sim.simulate_encounter(player, target)
        assert result.efficiency > 0

    def test_dps_positive(self, sim):
        player = sim.create_vocation_stats(Vocation.KNIGHT, 300)
        target = MonsterStats(
            name="Rotworm",
            health=65,
            attack=15,
            defense=8,
            magic_defense=5,
            experience=40,
            speed=80,
        )
        result = sim.simulate_encounter(player, target)
        assert result.dps > 0
        assert result.time_seconds > 0


class TestHuntRotation:
    def test_single_monster_hunt(self, sim):
        monsters = [
            MonsterStats(
                name="Rotworm",
                health=65,
                attack=15,
                defense=8,
                magic_defense=5,
                experience=40,
                speed=80,
            )
        ]
        result = sim.simulate_hunt_rotation(
            vocation=Vocation.KNIGHT,
            level=300,
            monsters=monsters,
            rotation_time_minutes=5.0,
        )
        assert isinstance(result, EncounterResult)
        assert result.monsters_killed > 0
        assert result.total_experience > 0
        assert result.vocation == "knight"

    def test_multi_vocation(self, sim):
        monsters = [
            MonsterStats(
                name="Dragon",
                health=1000,
                attack=100,
                defense=60,
                magic_defense=50,
                experience=700,
                speed=80,
            )
        ]
        results = sim.simulate_multi_vocation(
            level=300,
            monsters=monsters,
            rotation_minutes=5.0,
        )
        assert len(results) == 5
        assert "knight" in results
        assert "paladin" in results
        assert "druid" in results
        assert "sorcerer" in results
        assert "monk" in results

    def test_all_vocations_produce_results(self, sim):
        monsters = [
            MonsterStats(
                name="Goblin",
                health=80,
                attack=18,
                defense=10,
                magic_defense=8,
                experience=60,
                speed=80,
            )
        ]
        for vocation in Vocation:
            result = sim.simulate_hunt_rotation(
                vocation=vocation,
                level=300,
                monsters=monsters,
                rotation_time_minutes=2.0,
            )
            assert result.monsters_killed >= 0
            assert result.total_time > 0


class TestMonsterCreation:
    def test_create_monster(self):
        m = CombatSimulator.create_monster(
            name="Test",
            health=100,
            attack=10,
            defense=5,
            magic_defense=3,
            experience=20,
        )
        assert m.name == "Test"
        assert m.health == 100
        assert m.experience == 20

    def test_create_boss(self):
        m = CombatSimulator.create_monster(
            name="Boss",
            health=10000,
            attack=500,
            defense=300,
            magic_defense=200,
            experience=10000,
            is_boss=True,
        )
        assert m.is_boss is True
