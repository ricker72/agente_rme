"""
HITO 18 â€” Tests for :mod:`agente_rme.core.designer.content_balancer`.

Covers the level curve generation, difficulty scoring, level-gap
detection, suggestion generation and the rebalance pass.
"""

from __future__ import annotations

import unittest
from typing import List

from core.designer import (
    AutonomousDesigner,
    BalanceReport,
    BossArea,
    ContentBalancer,
    ContentBalance,
    DesignGoal,
    HuntArea,
    LevelCurvePoint,
    QuestArea,
    SpawnEntry,
    ThemeSpec,
    Vector2,
    WorldModel,
    Zone,
)


def _make_zone(
    zone_id: str = "zone_0",
    theme: str = "grassland",
    min_level: int = 1,
    max_level: int = 20,
    hunts: int = 1,
    bosses: int = 0,
    quests: int = 0,
) -> Zone:
    """Helper: build a minimal zone with the requested content."""
    theme_spec = ThemeSpec(name=theme, family="natural")
    zone = Zone(
        zone_id=zone_id,
        name=zone_id.replace("_", " ").title(),
        theme=theme_spec,
        bounds_min=Vector2(0, 0),
        bounds_max=Vector2(64, 64),
        min_level=min_level,
        max_level=max_level,
        difficulty="normal",
        layout="grid",
    )
    for k in range(hunts):
        zone.hunts.append(
            HuntArea(
                hunt_id=f"{zone_id}_hunt_{k}",
                name=f"Hunt {k}",
                center=Vector2(10 + k, 10),
                radius=5,
                min_level=min_level,
                max_level=max_level,
                difficulty="normal",
                theme=theme,
                spawns=[SpawnEntry(monster_name="wolf", count=2, radius=5)],
            )
        )
    for k in range(bosses):
        zone.bosses.append(
            BossArea(
                boss_id=f"{zone_id}_boss_{k}",
                name=f"Boss {k}",
                center=Vector2(32, 32),
                radius=8,
                boss_name="demon",
                boss_level=max_level,
                theme=theme,
            )
        )
    for k in range(quests):
        zone.quests.append(
            QuestArea(
                quest_id=f"{zone_id}_quest_{k}",
                name=f"Quest {k}",
                center=Vector2(20, 20),
                radius=5,
                quest_type="side",
                min_level=min_level,
                max_level=max_level,
                objectives=["investigate"],
                rewards=["gold coin"],
                npc_names=["NPC"],
            )
        )
    return zone


def _make_world(
    zones: List[Zone], min_level: int = 1, max_level: int = 100
) -> WorldModel:
    return WorldModel(
        name="test_world",
        goal=DesignGoal(
            raw_text="test",
            min_level=min_level,
            max_level=max_level,
            target_size=(512, 512),
        ),
        zones=zones,
    )


class TestContentBalancerBasic(unittest.TestCase):
    """Test the basic API of :class:`ContentBalancer`."""

    def setUp(self) -> None:
        self.balancer = ContentBalancer()

    def test_default_curve(self) -> None:
        self.assertEqual(self.balancer.target_curve, "linear")

    def test_balance_empty_world(self) -> None:
        world = _make_world([])
        report = self.balancer.balance(world)
        self.assertIsInstance(report, BalanceReport)
        self.assertIn("WorldModel has no zones", report.level_gap_warnings)

    def test_balance_simple_world(self) -> None:
        zone = _make_zone(hunts=3, bosses=1, quests=2)
        world = _make_world([zone], min_level=1, max_level=20)
        report = self.balancer.balance(world)
        self.assertIsInstance(report, BalanceReport)
        self.assertGreater(len(report.level_curve), 0)
        self.assertIn(zone.zone_id, report.per_zone_difficulty)

    def test_balance_records_density(self) -> None:
        zone = _make_zone(hunts=5, bosses=2, quests=3)
        world = _make_world([zone], min_level=1, max_level=50)
        report = self.balancer.balance(world)
        self.assertGreater(report.balance.hunts_per_level, 0)
        self.assertGreater(report.balance.bosses_per_50_levels, 0)
        self.assertGreater(report.balance.quests_per_25_levels, 0)


class TestContentBalancerLevelCurve(unittest.TestCase):
    """Test the level curve generation."""

    def setUp(self) -> None:
        self.balancer = ContentBalancer()

    def test_curve_covers_full_range(self) -> None:
        zone = _make_zone(min_level=1, max_level=50)
        world = _make_world([zone], min_level=1, max_level=50)
        report = self.balancer.balance(world)
        levels = [p.level for p in report.level_curve]
        self.assertIn(1, levels)
        self.assertIn(50, levels)

    def test_curve_xp_grows(self) -> None:
        zone = _make_zone(min_level=1, max_level=50)
        world = _make_world([zone], min_level=1, max_level=50)
        report = self.balancer.balance(world)
        # XP at level 50 should be greater than at level 1
        xp_1 = report.level_curve[0].target_xp
        xp_50 = [p.target_xp for p in report.level_curve if p.level == 50][0]
        self.assertGreater(xp_50, xp_1)

    def test_curve_hp_grows(self) -> None:
        zone = _make_zone(min_level=1, max_level=50)
        world = _make_world([zone], min_level=1, max_level=50)
        report = self.balancer.balance(world)
        hp_1 = report.level_curve[0].hp
        hp_50 = [p.hp for p in report.level_curve if p.level == 50][0]
        self.assertGreater(hp_50, hp_1)

    def test_curve_damage_grows(self) -> None:
        zone = _make_zone(min_level=1, max_level=50)
        world = _make_world([zone], min_level=1, max_level=50)
        report = self.balancer.balance(world)
        d_1 = report.level_curve[0].damage
        d_50 = [p.damage for p in report.level_curve if p.level == 50][0]
        self.assertGreater(d_50, d_1)

    def test_curve_exponential(self) -> None:
        zone = _make_zone(min_level=1, max_level=100)
        world = _make_world([zone], min_level=1, max_level=100)
        balancer = ContentBalancer(target_curve="exponential")
        report = balancer.balance(world)
        # The exponential curve should have a much steeper growth
        # Compare the last point's xp against the first
        self.assertGreater(
            report.level_curve[-1].target_xp, 10 * report.level_curve[0].target_xp
        )

    def test_curve_stepped(self) -> None:
        zone = _make_zone(min_level=1, max_level=100)
        world = _make_world([zone], min_level=1, max_level=100)
        balancer = ContentBalancer(target_curve="stepped")
        report = balancer.balance(world)
        # At least one curve point exists
        self.assertGreater(len(report.level_curve), 0)


class TestContentBalancerGapDetection(unittest.TestCase):
    """Test that level gaps are detected."""

    def setUp(self) -> None:
        self.balancer = ContentBalancer()

    def test_no_gaps_when_covered(self) -> None:
        z1 = _make_zone("z1", min_level=1, max_level=50)
        z2 = _make_zone("z2", min_level=51, max_level=100)
        world = _make_world([z1, z2], min_level=1, max_level=100)
        report = self.balancer.balance(world)
        self.assertEqual(report.level_gap_warnings, [])

    def test_gap_detected(self) -> None:
        z1 = _make_zone("z1", min_level=1, max_level=40)
        z2 = _make_zone("z2", min_level=60, max_level=100)
        world = _make_world([z1, z2], min_level=1, max_level=100)
        report = self.balancer.balance(world)
        self.assertTrue(report.level_gap_warnings)
        # The warning should mention the gap
        joined = " ".join(report.level_gap_warnings)
        self.assertIn("41", joined)
        self.assertIn("59", joined)

    def test_wide_zone_warning(self) -> None:
        z = _make_zone("z_wide", min_level=1, max_level=200)
        world = _make_world([z], min_level=1, max_level=200)
        report = self.balancer.balance(world)
        wide = [
            w for w in report.level_gap_warnings if "spans" in w and "too wide" in w
        ]
        self.assertTrue(wide)

    def test_empty_zone_warning(self) -> None:
        z = _make_zone(
            "z_empty", min_level=1, max_level=10, hunts=0, bosses=0, quests=0
        )
        world = _make_world([z], min_level=1, max_level=10)
        report = self.balancer.balance(world)
        empty = [w for w in report.level_gap_warnings if "no content" in w]
        self.assertTrue(empty)


class TestContentBalancerDifficultyScoring(unittest.TestCase):
    """Test the per-zone difficulty scoring."""

    def setUp(self) -> None:
        self.balancer = ContentBalancer()

    def test_safe_zone_low_score(self) -> None:
        z = _make_zone(theme="grassland", min_level=1, max_level=5)
        z.difficulty = "safe"
        # Make the hunt also "safe" to keep score low
        for h in z.hunts:
            h.difficulty = "safe"
        world = _make_world([z], min_level=1, max_level=5)
        report = self.balancer.balance(world)
        score = report.per_zone_difficulty[z.zone_id]
        self.assertLess(score, 0.5)

    def test_deadly_zone_high_score(self) -> None:
        z = _make_zone(theme="roshamuul", min_level=200, max_level=300, bosses=2)
        z.difficulty = "deadly"
        world = _make_world([z], min_level=200, max_level=300)
        report = self.balancer.balance(world)
        score = report.per_zone_difficulty[z.zone_id]
        self.assertGreater(score, 0.7)

    def test_score_increases_with_bosses(self) -> None:
        z1 = _make_zone("z1", min_level=1, max_level=20, bosses=0)
        z2 = _make_zone("z2", min_level=1, max_level=20, bosses=2)
        world = _make_world([z1, z2], min_level=1, max_level=20)
        report = self.balancer.balance(world)
        self.assertGreater(
            report.per_zone_difficulty["z2"],
            report.per_zone_difficulty["z1"],
        )

    def test_stddev_calculated(self) -> None:
        # A very safe zone and a very deadly zone â€” should produce stddev > 0
        z1 = _make_zone("z1", min_level=1, max_level=10, hunts=0, bosses=0, quests=0)
        z1.difficulty = "safe"
        for h in z1.hunts:
            h.difficulty = "safe"
        z2 = _make_zone("z2", min_level=11, max_level=20, bosses=5, hunts=5, quests=5)
        z2.difficulty = "deadly"
        for h in z2.hunts:
            h.difficulty = "deadly"
        for b in z2.bosses:
            b.mechanics = ["summon", "teleport", "shield_wall"]
        world = _make_world([z1, z2], min_level=1, max_level=20)
        report = self.balancer.balance(world)
        self.assertGreater(report.balance.difficulty_stddev, 0.0)
        # The safe score should be < the deadly score
        self.assertLess(
            report.per_zone_difficulty["z1"],
            report.per_zone_difficulty["z2"],
        )


class TestContentBalancerSuggestions(unittest.TestCase):
    """Test the suggestion generation."""

    def setUp(self) -> None:
        self.balancer = ContentBalancer()

    def test_suggestions_present(self) -> None:
        zone = _make_zone(min_level=1, max_level=20)
        world = _make_world([zone], min_level=1, max_level=20)
        report = self.balancer.balance(world)
        self.assertGreater(len(report.suggestions), 0)

    def test_suggestion_for_missing_connections(self) -> None:
        zone = _make_zone(min_level=1, max_level=20)
        world = _make_world([zone], min_level=1, max_level=20)
        report = self.balancer.balance(world)
        self.assertTrue(any("NavigationDesigner" in s for s in report.suggestions))

    def test_suggestion_for_low_bosses(self) -> None:
        zone = _make_zone(min_level=1, max_level=200, bosses=0)
        world = _make_world([zone], min_level=1, max_level=200)
        report = self.balancer.balance(world)
        self.assertTrue(any("boss" in s.lower() for s in report.suggestions))

    def test_suggestion_for_rebalance_when_gaps(self) -> None:
        z1 = _make_zone("z1", min_level=1, max_level=40)
        z2 = _make_zone("z2", min_level=60, max_level=100)
        world = _make_world([z1, z2], min_level=1, max_level=100)
        report = self.balancer.balance(world)
        self.assertTrue(any("rebalance" in s.lower() for s in report.suggestions))


class TestContentBalancerRebalance(unittest.TestCase):
    """Test the rebalance pass."""

    def setUp(self) -> None:
        self.balancer = ContentBalancer()

    def test_rebalance_no_op_when_no_gaps(self) -> None:
        z1 = _make_zone("z1", min_level=1, max_level=50)
        z2 = _make_zone("z2", min_level=51, max_level=100)
        world = _make_world([z1, z2], min_level=1, max_level=100)
        before_hunts = world.total_hunts()
        rebalanced = self.balancer.rebalance(world)
        self.assertEqual(rebalanced.total_hunts(), before_hunts)

    def test_rebalance_plugs_gap(self) -> None:
        z1 = _make_zone("z1", min_level=1, max_level=40)
        z2 = _make_zone("z2", min_level=60, max_level=100)
        world = _make_world([z1, z2], min_level=1, max_level=100)
        before_hunts = world.total_hunts()
        rebalanced = self.balancer.rebalance(world)
        # A rebalance hunt was added
        self.assertGreater(rebalanced.total_hunts(), before_hunts)
        # The new hunt covers the previously-empty range
        hunt_levels = set()
        for z in rebalanced.zones:
            for h in z.hunts:
                for lvl in range(h.min_level, h.max_level + 1):
                    hunt_levels.add(lvl)
        self.assertIn(45, hunt_levels)
        self.assertIn(55, hunt_levels)

    def test_rebalance_returns_new_world(self) -> None:
        z1 = _make_zone("z1", min_level=1, max_level=40)
        z2 = _make_zone("z2", min_level=60, max_level=100)
        world = _make_world([z1, z2], min_level=1, max_level=100)
        rebalanced = self.balancer.rebalance(world)
        self.assertIsInstance(rebalanced, WorldModel)
        # Original should be untouched
        self.assertEqual(world.total_hunts(), sum(len(z.hunts) for z in world.zones))

    def test_rebalance_with_explicit_report(self) -> None:
        z1 = _make_zone("z1", min_level=1, max_level=40)
        z2 = _make_zone("z2", min_level=60, max_level=100)
        world = _make_world([z1, z2], min_level=1, max_level=100)
        report = self.balancer.balance(world)
        rebalanced = self.balancer.rebalance(world, report)
        self.assertIsInstance(rebalanced, WorldModel)

    def test_rebalance_world_serializable(self) -> None:
        z1 = _make_zone("z1", min_level=1, max_level=40)
        z2 = _make_zone("z2", min_level=60, max_level=100)
        world = _make_world([z1, z2], min_level=1, max_level=100)
        rebalanced = self.balancer.rebalance(world)
        text = rebalanced.to_json()
        loaded = WorldModel.from_json(text)
        self.assertEqual(loaded.to_dict(), rebalanced.to_dict())


class TestContentBalancerIntegration(unittest.TestCase):
    """End-to-end balance tests using the AutonomousDesigner."""

    def test_balancer_in_full_pipeline(self) -> None:
        designer = AutonomousDesigner(auto_rebalance=True)
        world = designer.generate("map level 1-100")
        # The balancer should have left ContentBalance populated
        self.assertGreater(world.balance.hunts_per_level, 0)
        self.assertGreater(len(world.level_curve), 0)

    def test_full_pipeline_covers_levels(self) -> None:
        designer = AutonomousDesigner(auto_rebalance=True)
        world = designer.generate("map level 1-100")
        # After auto-rebalance, all levels covered
        coverage = set()
        for z in world.zones:
            for level in range(z.min_level, z.max_level + 1):
                coverage.add(level)
        missing = set(range(1, 101)) - coverage
        self.assertEqual(missing, set())

    def test_balance_report_serializable(self) -> None:
        designer = AutonomousDesigner()
        result = designer.generate_full("map level 1-50")
        data = result.balance_report.to_dict()
        self.assertIn("balance", data)
        self.assertIn("level_curve", data)
        self.assertIn("per_zone_difficulty", data)


class TestContentBalanceSerialization(unittest.TestCase):
    """Test the ContentBalance dataclass serialisation."""

    def test_to_from_dict(self) -> None:
        b = ContentBalance(
            hunts_per_level=2.5,
            bosses_per_50_levels=1.5,
            quests_per_25_levels=1.0,
            average_difficulty=0.6,
            difficulty_stddev=0.1,
            level_gap_warnings=["gap in 50-60"],
        )
        d = b.to_dict()
        b2 = ContentBalance.from_dict(d)
        self.assertEqual(b2.hunts_per_level, 2.5)
        self.assertEqual(b2.bosses_per_50_levels, 1.5)
        self.assertEqual(b2.average_difficulty, 0.6)
        self.assertEqual(b2.level_gap_warnings, ["gap in 50-60"])

    def test_default_content_balance(self) -> None:
        b = ContentBalance()
        self.assertEqual(b.hunts_per_level, 1.5)
        self.assertEqual(b.bosses_per_50_levels, 1.0)
        self.assertEqual(b.quests_per_25_levels, 1.0)


class TestLevelCurvePointSerialization(unittest.TestCase):
    """Test the LevelCurvePoint serialisation."""

    def test_to_from_dict(self) -> None:
        p = LevelCurvePoint(level=50, target_xp=10000, hp=500, damage=50)
        d = p.to_dict()
        p2 = LevelCurvePoint.from_dict(d)
        self.assertEqual(p2.level, 50)
        self.assertEqual(p2.target_xp, 10000)
        self.assertEqual(p2.hp, 500)
        self.assertEqual(p2.damage, 50)


if __name__ == "__main__":
    unittest.main()
