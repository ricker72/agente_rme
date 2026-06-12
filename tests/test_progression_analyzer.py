"""Tests for the Progression Analyzer."""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.playtest.combat_simulator import MonsterStats
from core.playtest.progression_analyzer import (
    ProgressionAnalyzer,
    ProgressionPoint,
    ProgressionReport,
)
from core.playtest.difficulty_evaluator import DifficultyEvaluator
from core.playtest.survival_analyzer import SurvivalAnalyzer
from core.playtest.loot_simulator import LootSimulator


@pytest.fixture
def analyzer():
    return ProgressionAnalyzer(seed=42)


@pytest.fixture
def sample_monsters():
    return [
        MonsterStats(
            name="Dragon",
            health=1000,
            attack=100,
            defense=60,
            magic_defense=50,
            experience=700,
            level=50,
        ),
        MonsterStats(
            name="Hydra",
            health=2100,
            attack=150,
            defense=80,
            magic_defense=70,
            experience=1500,
            level=80,
        ),
    ]


class TestXPFormula:
    def test_xp_level_1(self, analyzer):
        xp = analyzer.xp_required_for_level(1)
        assert xp > 0
        assert xp == int(1000 * 1 * (1 + 1 / 100.0))

    def test_xp_increases_with_level(self, analyzer):
        xp_100 = analyzer.xp_required_for_level(100)
        xp_200 = analyzer.xp_required_for_level(200)
        assert xp_200 > xp_100

    def test_xp_level_300(self, analyzer):
        xp = analyzer.xp_required_for_level(300)
        expected = int(1000 * 300 * (1 + 300 / 100.0))
        assert xp == expected


class TestTimeToLevel:
    def test_time_to_level_positive_xp(self, analyzer):
        t = analyzer.time_to_level(1000000, 300)
        assert t > 0
        assert t < 1000  # Should be reasonable

    def test_time_to_level_zero_xp(self, analyzer):
        t = analyzer.time_to_level(0, 300)
        assert t == float("inf")

    def test_time_to_level_negative_xp(self, analyzer):
        t = analyzer.time_to_level(-100, 300)
        assert t == float("inf")

    def test_time_to_level_higher_xp_faster(self, analyzer):
        t1 = analyzer.time_to_level(100000, 300)
        t2 = analyzer.time_to_level(1000000, 300)
        assert t2 < t1


class TestZoneProgression:
    def test_analyze_zone(self, analyzer, sample_monsters):
        point = analyzer.analyze_zone_progression(
            monsters=sample_monsters,
            player_level=300,
            rotation_minutes=60.0,
        )
        assert isinstance(point, ProgressionPoint)
        assert point.level == 300
        assert point.xp_per_hour >= 0
        assert point.loot_per_hour >= 0
        assert point.time_to_next_level_hours >= 0
        assert point.hunt_efficiency >= 0

    def test_higher_level_higher_xp(self, analyzer, sample_monsters):
        p_100 = analyzer.analyze_zone_progression(sample_monsters, 100)
        p_500 = analyzer.analyze_zone_progression(sample_monsters, 500)
        # Higher level = more stats = more kills = more XP
        assert p_500.xp_per_hour >= p_100.xp_per_hour


class TestProgressionCurve:
    def test_analyze_curve(self, analyzer, sample_monsters):
        zones = {"hunt_1": sample_monsters}
        report = analyzer.analyze_progression_curve(
            zones=zones,
            level_min=100,
            level_max=500,
            level_step=100,
        )
        assert isinstance(report, ProgressionReport)
        assert report.level_range == (100, 500)
        assert len(report.progression_points) == 5  # 100, 200, 300, 400, 500
        assert report.xp_per_hour_avg >= 0
        assert 0.0 <= report.curve_smoothness <= 1.0

    def test_curve_has_points(self, analyzer, sample_monsters):
        zones = {"hunt_1": sample_monsters}
        report = analyzer.analyze_progression_curve(
            zones=zones,
            level_min=100,
            level_max=300,
            level_step=50,
        )
        assert len(report.progression_points) > 0

    def test_bottleneck_detection(self, analyzer):
        # Create zones with very different difficulty
        easy_monsters = [
            MonsterStats(
                name="Rat",
                health=20,
                attack=5,
                defense=2,
                magic_defense=2,
                experience=5,
                level=1,
            ),
        ]
        hard_monsters = [
            MonsterStats(
                name="Demon",
                health=5000,
                attack=300,
                defense=200,
                magic_defense=180,
                experience=3500,
                level=120,
            ),
        ]
        zones = {"easy": easy_monsters, "hard": hard_monsters}
        report = analyzer.analyze_progression_curve(
            zones=zones,
            level_min=1,
            level_max=300,
            level_step=50,
        )
        assert isinstance(report, ProgressionReport)
        # Should have some recommendations
        assert len(report.recommendations) > 0


class TestVocationComparison:
    def test_compare_vocations(self, analyzer, sample_monsters):
        results = analyzer.compare_vocation_progression(
            monsters=sample_monsters,
            level_min=100,
            level_max=300,
            level_step=100,
        )
        assert len(results) == 5
        assert "knight" in results
        assert "sorcerer" in results
        # Each vocation should have progression points
        for voc, points in results.items():
            assert len(points) > 0
            for p in points:
                assert p.xp_per_hour >= 0


class TestLevelRangeValidation:
    def test_balanced_levels(self, analyzer):
        ok, issues = analyzer.validate_level_range(
            zone_monster_min_level=200,
            zone_monster_max_level=400,
            target_player_min=250,
            target_player_max=350,
        )
        assert ok is True
        assert len(issues) == 0

    def test_monsters_too_strong(self, analyzer):
        ok, issues = analyzer.validate_level_range(
            zone_monster_min_level=500,
            zone_monster_max_level=600,
            target_player_min=100,
            target_player_max=200,
        )
        assert ok is False
        assert len(issues) > 0

    def test_monsters_too_weak(self, analyzer):
        ok, issues = analyzer.validate_level_range(
            zone_monster_min_level=10,
            zone_monster_max_level=20,
            target_player_min=200,
            target_player_max=300,
        )
        assert ok is False
        assert len(issues) > 0

    def test_spread_too_wide(self, analyzer):
        ok, issues = analyzer.validate_level_range(
            zone_monster_min_level=1,
            zone_monster_max_level=1000,
            target_player_min=200,
            target_player_max=250,
        )
        assert ok is False


class TestDifficultyEvaluator:
    def test_easy_zone(self):
        evaluator = DifficultyEvaluator(seed=42)
        score, label, issues = evaluator.evaluate_zone(
            zone_name="test",
            spawn_count=50,
            total_tiles=2500,
            monster_avg_level=300,
            player_level=300,
            has_boss=False,
            has_healing=False,
        )
        assert 0 <= score <= 10
        assert label in ("trivial", "easy", "medium", "hard", "extreme")

    def test_dense_zone(self):
        evaluator = DifficultyEvaluator(seed=42)
        score, label, issues = evaluator.evaluate_zone(
            zone_name="overcrowded",
            spawn_count=500,
            total_tiles=2500,
            monster_avg_level=300,
            player_level=300,
        )
        assert score > 5  # Should be harder
        assert any("density" in i.lower() for i in issues)

    def test_world_evaluation(self):
        evaluator = DifficultyEvaluator(seed=42)
        zones = {
            "easy_zone": {
                "spawn_count": 30,
                "total_tiles": 2500,
                "monster_avg_level": 100,
                "has_boss": False,
                "has_healing": True,
                "monster_xp": 100,
            },
            "hard_zone": {
                "spawn_count": 100,
                "total_tiles": 2500,
                "monster_avg_level": 500,
                "has_boss": True,
                "has_healing": False,
                "monster_xp": 5000,
            },
        }
        report = evaluator.evaluate_world(zones, player_level=300)
        assert report.difficulty_score >= 0
        assert report.overall_difficulty in (
            "trivial",
            "easy",
            "medium",
            "hard",
            "extreme",
        )

    def test_is_balanced(self):
        evaluator = DifficultyEvaluator(seed=42)
        ok, issues = evaluator.is_balanced(
            player_level=300,
            monster_min_level=250,
            monster_max_level=350,
            spawn_count=60,
            area_tiles=2500,
        )
        assert ok is True

    def test_is_balanced_too_dense(self):
        evaluator = DifficultyEvaluator(seed=42)
        ok, issues = evaluator.is_balanced(
            player_level=300,
            monster_min_level=250,
            monster_max_level=350,
            spawn_count=500,
            area_tiles=2500,
        )
        assert ok is False

    def test_difficulty_color(self):
        assert DifficultyEvaluator.difficulty_color(1.0) == "#00ff00"
        assert DifficultyEvaluator.difficulty_color(5.0) == "#ffff00"
        assert DifficultyEvaluator.difficulty_color(9.0) == "#ff0000"


class TestLootSimulator:
    def test_simulate_hunt(self):
        loot = LootSimulator(seed=42)
        gold, items, rare = loot.simulate_hunt("Dragon", 100)
        assert gold > 0
        assert gold > 100 * 150  # min gold * kills
        assert isinstance(items, dict)

    def test_simulate_rotation(self):
        loot = LootSimulator(seed=42)
        report = loot.simulate_hunt_rotation(
            monsters=["Dragon", "Hydra"],
            kills_per_monster=50,
            rotation_minutes=60.0,
        )
        assert report.total_gold > 0
        assert report.gold_per_hour > 0
        assert report.total_kills == 100

    def test_unknown_monster(self):
        loot = LootSimulator(seed=42)
        gold, items, rare = loot.simulate_hunt("UnknownMonster", 10)
        assert gold == 10 * 50  # Fallback
        assert items == {}

    def test_get_loot_table(self):
        loot = LootSimulator(seed=42)
        table = loot.get_loot_table("Dragon")
        assert table is not None
        assert table.monster_name == "Dragon"

    def test_register_custom_table(self):
        from core.playtest.loot_simulator import LootTable

        loot = LootSimulator(seed=42)
        custom = LootTable(
            monster_name="Custom",
            gold_min=100,
            gold_max=200,
            items=[("Custom Item", 50, 9999)],
            rare_items=[],
        )
        loot.register_loot_table(custom)
        table = loot.get_loot_table("Custom")
        assert table is not None


class TestSurvivalAnalyzer:
    def test_quick_risk_assessment(self):
        analyzer = SurvivalAnalyzer(seed=42)
        assert analyzer.quick_risk_assessment(100, 300, 10) == "safe"
        assert analyzer.quick_risk_assessment(300, 100, 100) == "deadly"

    def test_analyze_zone(self):
        analyzer = SurvivalAnalyzer(seed=42)
        monsters = [
            MonsterStats(
                name="Dragon",
                health=1000,
                attack=100,
                defense=60,
                magic_defense=50,
                experience=700,
                level=50,
            ),
        ]
        report = analyzer.analyze_zone("test_zone", monsters, 300)
        assert report.zone_name == "test_zone"
        assert 0 <= report.survival_rate <= 1.0
        assert report.risk_level in ("safe", "moderate", "dangerous", "deadly")

    def test_analyze_world(self):
        analyzer = SurvivalAnalyzer(seed=42)
        zones = {
            "zone_a": [
                MonsterStats(
                    name="Rat",
                    health=20,
                    attack=5,
                    defense=2,
                    magic_defense=2,
                    experience=5,
                    level=1,
                ),
            ],
        }
        report = analyzer.analyze_world(zones, 300)
        assert report.overall_survival_rate >= 0
        assert len(report.zone_reports) == 1
        assert len(report.recommendations) > 0
