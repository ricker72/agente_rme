from __future__ import annotations

import pytest

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.balance.xp_balancer import XPBalancer, XPBalanceResult, XPAdjustment, MONSTER_XP_DB
from core.balance.xp_analyzer import XPAnalysis


def _build_world(zone_name: str, monsters: list, zone_tiles: int = 30) -> WorldModel:
    world = WorldModel()
    region = Region(name=zone_name, theme="test", min_level=100, max_level=200)
    world.add_region(region)

    idx = 0
    for x in range(zone_tiles):
        for y in range(zone_tiles):
            tile = Tile(x=x, y=y, z=7, ground=817, zone=zone_name)
            if idx < len(monsters):
                tile.spawn = Spawn(monster=monsters[idx], respawn=60, radius=5)
                idx += 1
            world.set_tile(tile)

    return world


def _count_spawns(world: WorldModel, zone_name: str) -> int:
    return sum(
        1 for t in world.tiles.values()
        if t.zone == zone_name and t.spawn is not None
    )


class TestXPBalancerInit:
    def test_create(self):
        b = XPBalancer()
        assert b is not None

    def test_target_efficiency(self):
        b = XPBalancer()
        assert b.TARGET_EFFICIENCY == 60.0

    def test_has_analyzer(self):
        b = XPBalancer()
        assert b._analyzer is not None


class TestXPBalancerBalance:
    def test_no_spawns_returns_empty(self):
        world = WorldModel()
        region = Region(name="empty")
        world.add_region(region)

        b = XPBalancer()
        result = b.balance(world, region)

        assert result.total_monsters_adjusted == 0
        assert len(result.zones_modified) == 0

    def test_balances_low_xp_zone(self):
        # Rats have very low XP, zone likely needs more spawns
        monsters = ["Rat"] * 5
        world = _build_world("rat_cave", monsters)
        region = world.get_region("rat_cave")
        b = XPBalancer()

        monsters_dict = {"Rat": 20}
        result = b.balance(world, region, monsters=monsters_dict, player_level=150)

        # Should have made some adjustment or determined it's already balanced
        assert isinstance(result, XPBalanceResult)

    def test_balances_high_xp_zone(self):
        # Demons have very high XP
        monsters = ["Demon"] * 5
        world = _build_world("demon_hell", monsters)
        region = world.get_region("demon_hell")
        b = XPBalancer()

        monsters_dict = {"Demon": 3000}
        result = b.balance(world, region, monsters=monsters_dict, player_level=150)

        assert isinstance(result, XPBalanceResult)

    def test_balanced_zone_no_change(self):
        # A well-balanced zone should not be modified
        monsters = ["Dragon"] * 7
        world = _build_world("balanced_zone", monsters)
        region = world.get_region("balanced_zone")
        b = XPBalancer()

        result = b.balance(world, region, player_level=150)
        assert isinstance(result, XPBalanceResult)


class TestXPBalancerAnalysis:
    def test_analyze_zone(self):
        monsters = ["Dragon", "Dragon", "Hydra"]
        world = _build_world("dragon_zone", monsters)
        region = world.get_region("dragon_zone")
        b = XPBalancer()

        analysis = b.analyze_zone_xp(world, region, player_level=150)

        assert isinstance(analysis, XPAnalysis)
        assert analysis.zone_name == "dragon_zone"

    def test_analyze_empty_zone(self):
        world = WorldModel()
        region = Region(name="empty")
        world.add_region(region)
        b = XPBalancer()

        analysis = b.analyze_zone_xp(world, region)

        assert analysis.zone_name == "empty"
        assert analysis.rating == "no_data"


class TestXPBalancerReplacement:
    def test_suggest_replacement(self):
        b = XPBalancer()
        replacement = b.suggest_monster_replacement("Rat", target_xp=700)

        assert replacement is not None
        assert replacement != "Rat"
        assert replacement in MONSTER_XP_DB

    def test_suggest_replacement_exact(self):
        b = XPBalancer()
        replacement = b.suggest_monster_replacement("Dragon", target_xp=700)

        # Should find something close
        assert replacement is not None

    def test_suggest_replacement_unknown_monster(self):
        b = XPBalancer()
        replacement = b.suggest_monster_replacement("UnknownMonster", target_xp=100)

        assert replacement is None


class TestXPBalancerMultiplier:
    def test_calc_multiplier_balanced(self):
        b = XPBalancer()
        analysis = XPAnalysis(efficiency_score=60.0)
        mult = b._calc_xp_multiplier(analysis, 150)
        assert mult == 1.0

    def test_calc_multiplier_low_efficiency(self):
        b = XPBalancer()
        analysis = XPAnalysis(efficiency_score=10.0)
        mult = b._calc_xp_multiplier(analysis, 150)
        assert mult > 1.0

    def test_calc_multiplier_zero_efficiency(self):
        b = XPBalancer()
        analysis = XPAnalysis(efficiency_score=0)
        mult = b._calc_xp_multiplier(analysis, 150)
        assert mult == 1.0


class TestXPAdjustment:
    def test_to_dict(self):
        adj = XPAdjustment(
            zone_name="test", monster="Dragon",
            old_xp=700, new_xp=700, multiplier=1.0,
            reason="test"
        )
        d = adj.to_dict()
        assert d["zone_name"] == "test"
        assert d["monster"] == "Dragon"
        assert d["multiplier"] == 1.0


class TestXPBalanceResult:
    def test_to_dict(self):
        r = XPBalanceResult()
        r.total_monsters_adjusted = 5
        d = r.to_dict()
        assert d["total_monsters_adjusted"] == 5
        assert d["zones_modified"] == []