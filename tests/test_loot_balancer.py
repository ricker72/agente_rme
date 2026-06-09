from __future__ import annotations

import pytest

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.balance.loot_balancer import LootBalancer, LootBalanceResult, LootAdjustment, DEFAULT_LOOT_TABLES
from core.balance.loot_analyzer import LootAnalysis


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


class TestLootBalancerInit:
    def test_create(self):
        b = LootBalancer()
        assert b is not None

    def test_has_analyzer(self):
        b = LootBalancer()
        assert b._analyzer is not None

    def test_default_loot_tables(self):
        assert "Dragon" in DEFAULT_LOOT_TABLES
        assert "Demon" in DEFAULT_LOOT_TABLES
        assert len(DEFAULT_LOOT_TABLES) > 5


class TestLootBalancerBalance:
    def test_no_spawns_returns_empty(self):
        world = WorldModel()
        region = Region(name="empty")
        world.add_region(region)

        b = LootBalancer()
        result = b.balance(world, region)

        assert result.total_adjustments == 0

    def test_balances_low_profit_zone(self):
        monsters = ["Rat"] * 5
        world = _build_world("rat_field", monsters)
        region = world.get_region("rat_field")

        b = LootBalancer()
        result = b.balance(world, region, target_level=150)

        assert isinstance(result, LootBalanceResult)

    def test_balances_high_profit_zone(self):
        monsters = ["Demon"] * 5
        world = _build_world("demon_area", monsters)
        region = world.get_region("demon_area")

        b = LootBalancer()
        result = b.balance(world, region, target_level=150)

        assert isinstance(result, LootBalanceResult)

    def test_balanced_zone_minimal_change(self):
        monsters = ["Dragon"] * 5
        world = _build_world("dragon_cave", monsters)
        region = world.get_region("dragon_cave")

        b = LootBalancer()
        result = b.balance(world, region, target_level=150)

        assert isinstance(result, LootBalanceResult)


class TestLootBalancerAnalysis:
    def test_analyze_zone(self):
        monsters = ["Dragon", "Demon", "Hydra"]
        world = _build_world("loot_zone", monsters)
        region = world.get_region("loot_zone")

        b = LootBalancer()
        analysis = b.analyze_zone_loot(world, region, target_level=150)

        assert isinstance(analysis, LootAnalysis)
        assert analysis.zone_name == "loot_zone"

    def test_analyze_empty_zone(self):
        world = WorldModel()
        region = Region(name="empty")
        world.add_region(region)

        b = LootBalancer()
        analysis = b.analyze_zone_loot(world, region)

        assert analysis.zone_name == "empty"


class TestLootBalancerDifficulty:
    def test_guess_difficulty_easy(self):
        b = LootBalancer()
        assert b._guess_difficulty("Rat") == "easy"
        assert b._guess_difficulty("Troll") == "easy"

    def test_guess_difficulty_medium(self):
        b = LootBalancer()
        assert b._guess_difficulty("Cyclops") == "medium"
        assert b._guess_difficulty("Vampire") == "medium"

    def test_guess_difficulty_hard(self):
        b = LootBalancer()
        assert b._guess_difficulty("Dragon") == "hard"
        assert b._guess_difficulty("Hydra") == "hard"

    def test_guess_difficulty_very_hard(self):
        b = LootBalancer()
        assert b._guess_difficulty("Demon") == "very_hard"
        assert b._guess_difficulty("Dragon Lord") == "very_hard"

    def test_guess_difficulty_unknown(self):
        b = LootBalancer()
        assert b._guess_difficulty("RandomMonster") == "medium"


class TestLootBalancerHelpers:
    def test_find_more_profitable_monsters(self):
        b = LootBalancer()
        spawns = [
            (0, 0, 7, Spawn(monster="Rat")),
            (1, 0, 7, Spawn(monster="Troll")),
        ]
        result = b._find_more_profitable_monsters(spawns, DEFAULT_LOOT_TABLES)
        assert len(result) > 0
        assert "Rat" not in result
        assert "Troll" not in result


class TestLootAdjustment:
    def test_to_dict(self):
        adj = LootAdjustment(
            zone_name="test", monster="Dragon",
            action="add_spawn", reason="low profit"
        )
        d = adj.to_dict()
        assert d["zone_name"] == "test"
        assert d["action"] == "add_spawn"


class TestLootBalanceResult:
    def test_to_dict(self):
        r = LootBalanceResult()
        r.total_adjustments = 3
        d = r.to_dict()
        assert d["total_adjustments"] == 3
        assert d["zones_modified"] == []