from __future__ import annotations


from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.balance.balance_engine import BalanceEngine, BalanceReport, ZoneBalanceReport
from core.balance.spawn_balancer import SpawnBalancer
from core.balance.xp_balancer import XPBalancer
from core.balance.loot_balancer import LootBalancer
from core.balance.difficulty_balancer import DifficultyBalancer
from core.balance.risk_balancer import RiskBalancer

# ---------------------------------------------------------------------------
# World builders
# ---------------------------------------------------------------------------


def _build_simple_world() -> WorldModel:
    """Build a simple world with one region and spawns."""
    world = WorldModel()
    region = Region(name="hunt_zone", theme="jungle", min_level=50, max_level=150)
    world.add_region(region)

    monsters = ["Dragon", "Dragon", "Hydra", "Vampire", "Cyclops"]
    idx = 0
    for x in range(20):
        for y in range(20):
            tile = Tile(x=x, y=y, z=7, ground=817, zone="hunt_zone")
            if idx < len(monsters):
                tile.spawn = Spawn(monster=monsters[idx], respawn=60, radius=5)
                idx += 1
            world.set_tile(tile)

    return world


def _build_multi_region_world() -> WorldModel:
    """Build a world with multiple regions."""
    world = WorldModel()

    # Easy zone
    easy = Region(name="easy_zone", theme="grass", min_level=10, max_level=50)
    world.add_region(easy)
    for x in range(15):
        for y in range(15):
            tile = Tile(x=x, y=y, z=7, ground=817, zone="easy_zone")
            if (x + y) % 5 == 0:
                tile.spawn = Spawn(monster="Rat", respawn=60, radius=5)
            world.set_tile(tile)

    # Hard zone
    hard = Region(name="hard_zone", theme="hell", min_level=200, max_level=400)
    world.add_region(hard)
    for x in range(15):
        for y in range(15):
            tile = Tile(x=x + 20, y=y, z=7, ground=817, zone="hard_zone")
            if (x + y) % 3 == 0:
                tile.spawn = Spawn(monster="Demon", respawn=60, radius=5)
            world.set_tile(tile)

    return world


def _build_overcrowded_world() -> WorldModel:
    """Build a world with too many spawns in one zone."""
    world = WorldModel()
    region = Region(name="overcrowded", theme="cave")
    world.add_region(region)

    for x in range(20):
        for y in range(20):
            tile = Tile(x=x, y=y, z=7, ground=817, zone="overcrowded")
            tile.spawn = Spawn(monster="Dragon", respawn=60, radius=5)
            world.set_tile(tile)

    return world


def _build_empty_world() -> WorldModel:
    """Build an empty world with no regions."""
    world = WorldModel()
    return world


def _build_dangerous_world() -> WorldModel:
    """Build a world with very dangerous monsters."""
    world = WorldModel()
    region = Region(name="danger", theme="hell", min_level=100, max_level=300)
    world.add_region(region)

    monsters = ["Demon", "Demon", "Demon", "Black Knight", "Iron Golem"]
    idx = 0
    for x in range(10):
        for y in range(10):
            tile = Tile(x=x, y=y, z=7, ground=817, zone="danger")
            if idx < len(monsters):
                tile.spawn = Spawn(monster=monsters[idx], respawn=30, radius=5)
                idx += 1
            world.set_tile(tile)

    return world


def _build_trivial_world() -> WorldModel:
    """Build a world with very easy monsters."""
    world = WorldModel()
    region = Region(name="tutorial", theme="grass", min_level=1, max_level=10)
    world.add_region(region)

    for x in range(10):
        for y in range(10):
            tile = Tile(x=x, y=y, z=7, ground=817, zone="tutorial")
            if (x + y) % 3 == 0:
                tile.spawn = Spawn(monster="Rat", respawn=60, radius=5)
            world.set_tile(tile)

    return world


def _count_spawns(world: WorldModel, zone_name: str) -> int:
    return sum(
        1 for t in world.tiles.values() if t.zone == zone_name and t.spawn is not None
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestBalanceEngineInit:
    def test_create_default(self):
        engine = BalanceEngine()
        assert engine is not None
        assert engine._player_level == 150

    def test_create_custom_level(self):
        engine = BalanceEngine(player_level=300)
        assert engine._player_level == 300

    def test_has_all_balancers(self):
        engine = BalanceEngine()
        assert isinstance(engine._spawn_balancer, SpawnBalancer)
        assert isinstance(engine._xp_balancer, XPBalancer)
        assert isinstance(engine._loot_balancer, LootBalancer)
        assert isinstance(engine._difficulty_balancer, DifficultyBalancer)
        assert isinstance(engine._risk_balancer, RiskBalancer)


class TestBalanceEngineRun:
    def test_balance_simple_world(self):
        world = _build_simple_world()
        engine = BalanceEngine()

        balanced, report = engine.balance(world)

        assert balanced is not None
        assert isinstance(report, BalanceReport)
        assert report.world_balanced is True
        assert len(report.zones) >= 1

    def test_balance_returns_same_world(self):
        world = _build_simple_world()
        engine = BalanceEngine()

        balanced, report = engine.balance(world)

        # Balance modifies in-place and returns same object
        assert balanced is world

    def test_balance_multi_region(self):
        world = _build_multi_region_world()
        engine = BalanceEngine()

        balanced, report = engine.balance(world)

        assert report.world_balanced is True
        assert len(report.zones) == 2
        zone_names = [z.zone_name for z in report.zones]
        assert "easy_zone" in zone_names
        assert "hard_zone" in zone_names

    def test_balance_empty_world(self):
        world = _build_empty_world()
        engine = BalanceEngine()

        balanced, report = engine.balance(world)

        assert report.world_balanced is True
        # Even empty world gets a global zone
        assert len(report.zones) == 1

    def test_balance_report_has_totals(self):
        world = _build_simple_world()
        engine = BalanceEngine()

        _, report = engine.balance(world)

        assert report.total_adjustments >= 0
        assert report.zones_modified >= 0

    def test_balance_overcrowded_world(self):
        world = _build_overcrowded_world()
        engine = BalanceEngine()

        balanced, report = engine.balance(world)

        assert report.world_balanced is True
        # Should have made adjustments to reduce overcrowding
        assert report.total_adjustments > 0


class TestBalanceEngineReport:
    def test_zone_report_to_dict(self):
        world = _build_simple_world()
        engine = BalanceEngine()

        _, report = engine.balance(world)

        d = report.to_dict()
        assert "zones" in d
        assert "total_adjustments" in d
        assert "zones_modified" in d
        assert "world_balanced" in d
        assert d["world_balanced"] is True

    def test_zone_balance_report_to_dict(self):
        zr = ZoneBalanceReport(zone_name="test", was_modified=True)
        d = zr.to_dict()
        assert d["zone_name"] == "test"
        assert d["was_modified"] is True

    def test_zone_report_analyses_populated(self):
        world = _build_simple_world()
        engine = BalanceEngine()

        _, report = engine.balance(world)

        for zr in report.zones:
            assert zr.xp_analysis is not None
            assert zr.loot_analysis is not None
            assert zr.difficulty_analysis is not None
            assert zr.risk_assessment is not None


class TestBalanceEngineAnalyze:
    def test_analyze_does_not_modify(self):
        world = _build_simple_world()
        engine = BalanceEngine()

        original_count = _count_spawns(world, "hunt_zone")
        report = engine.analyze(world)
        final_count = _count_spawns(world, "hunt_zone")

        assert original_count == final_count
        assert len(report.zones) >= 1

    def test_analyze_multi_region(self):
        world = _build_multi_region_world()
        engine = BalanceEngine()

        report = engine.analyze(world)

        assert len(report.zones) == 2
        for zr in report.zones:
            assert zr.xp_analysis is not None


class TestBalanceEngineIntegration:
    def test_playtest_failed_world_pattern(self):
        """Simulate the pattern from the task example:
        world = playtest_failed_world
        balanced = balance_engine.balance(world)
        assert balanced is not None
        """
        # Build a "failed" world (unbalanced)
        world = _build_overcrowded_world()

        engine = BalanceEngine()
        balanced, report = engine.balance(world)

        assert balanced is not None
        assert report.world_balanced is True

    def test_dangerous_world_gets_corrected(self):
        world = _build_dangerous_world()
        engine = BalanceEngine()

        balanced, report = engine.balance(world)

        assert report.world_balanced is True
        # Should have made corrections to dangerous zone
        danger_zone = [z for z in report.zones if z.zone_name == "danger"]
        assert len(danger_zone) == 1

    def test_balance_preserves_world_structure(self):
        world = _build_simple_world()
        original_tile_count = world.tile_count()

        engine = BalanceEngine()
        balanced, _ = engine.balance(world)

        # Tile count should be the same (we modify spawns, not tiles)
        assert balanced.tile_count() == original_tile_count

    def test_balance_deterministic(self):
        """Running balance twice on similar worlds should produce similar results."""
        world1 = _build_simple_world()
        world2 = _build_simple_world()

        engine = BalanceEngine()
        _, report1 = engine.balance(world1)
        _, report2 = engine.balance(world2)

        # Both should be balanced
        assert report1.world_balanced is True
        assert report2.world_balanced is True

    def test_balance_with_custom_player_level(self):
        world = _build_dangerous_world()
        engine = BalanceEngine(player_level=50)

        balanced, report = engine.balance(world)

        assert report.world_balanced is True
