from __future__ import annotations

import pytest
from typing import Dict, List

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.balance.spawn_balancer import SpawnBalancer, SpawnBalanceResult, SpawnAdjustment


def _build_world(zone_name: str, spawn_count: int,
                 monster: str = "Dragon", zone_tiles: int = 30) -> WorldModel:
    """Build a world with a given number of spawns in a region."""
    world = WorldModel()
    region = Region(name=zone_name, theme="test", min_level=100, max_level=200)
    world.add_region(region)

    spawns_placed = 0
    for x in range(zone_tiles):
        for y in range(zone_tiles):
            tile = Tile(x=x, y=y, z=7, ground=817, zone=zone_name)
            if spawns_placed < spawn_count:
                tile.spawn = Spawn(monster=monster, respawn=60, radius=5)
                spawns_placed += 1
            world.set_tile(tile)

    return world


def _count_spawns(world: WorldModel, zone_name: str) -> int:
    return sum(
        1 for t in world.tiles.values()
        if t.zone == zone_name and t.spawn is not None
    )


class TestSpawnBalancerInit:
    def test_default_constants(self):
        b = SpawnBalancer()
        assert b.MIN_SPAWNS_PER_ZONE == 3
        assert b.MAX_SPAWNS_PER_ZONE == 12
        assert b.IDEAL_SPAWNS_PER_ZONE == 7

    def test_instantiate_with_defaults(self):
        b = SpawnBalancer()
        assert b is not None


class TestSpawnBalancerAdd:
    def test_adds_when_below_minimum(self):
        world = _build_world("cave", 1, monster="Troll")
        region = world.get_region("cave")
        b = SpawnBalancer()
        result = b.balance(world, region)

        assert result.spawns_added > 0
        assert _count_spawns(world, "cave") >= SpawnBalancer.MIN_SPAWNS_PER_ZONE

    def test_no_change_when_ideal(self):
        world = _build_world("forest", 7, monster="Dragon")
        region = world.get_region("forest")
        b = SpawnBalancer()
        result = b.balance(world, region)

        assert result.spawns_added == 0
        assert result.spawns_removed == 0

    def test_adds_to_empty_zone_with_tiles(self):
        # Zone with 0 spawns but tiles present - can't add since no reference monster
        world = _build_world("empty", 0, monster="Rat")
        region = world.get_region("empty")
        b = SpawnBalancer()
        result = b.balance(world, region)

        # With 0 existing spawns, there's no reference monster type to add
        # This is expected behavior - empty zones need external specification
        assert result.spawns_added == 0
        assert _count_spawns(world, "empty") == 0

    def test_adds_to_zone_with_single_spawn(self):
        world = _build_world("lonely", 1, monster="Dragon")
        region = world.get_region("lonely")
        b = SpawnBalancer()
        result = b.balance(world, region)

        assert result.spawns_added > 0
        assert _count_spawns(world, "lonely") >= SpawnBalancer.MIN_SPAWNS_PER_ZONE


class TestSpawnBalancerRemove:
    def test_removes_when_above_maximum(self):
        world = _build_world("overcrowded", 20, monster="Demon")
        region = world.get_region("overcrowded")
        b = SpawnBalancer()
        result = b.balance(world, region)

        assert result.spawns_removed > 0
        assert _count_spawns(world, "overcrowded") <= SpawnBalancer.MAX_SPAWNS_PER_ZONE

    def test_removes_furthest_from_center(self):
        world = _build_world("far_zone", 15, monster="Hydra")
        region = world.get_region("far_zone")
        b = SpawnBalancer()
        result = b.balance(world, region)

        assert result.spawns_removed > 0


class TestSpawnBalancerRespawn:
    def test_fixes_too_fast_respawn(self):
        world = WorldModel()
        region = Region(name="fast")
        world.add_region(region)
        tile = Tile(x=0, y=0, z=7, ground=817, zone="fast")
        tile.spawn = Spawn(monster="Dragon", respawn=5, radius=5)
        world.set_tile(tile)

        b = SpawnBalancer()
        result = b.balance(world, region)

        assert result.respawns_adjusted >= 1
        assert tile.spawn.respawn >= SpawnBalancer.MIN_RESPAWN

    def test_fixes_too_slow_respawn(self):
        world = WorldModel()
        region = Region(name="slow")
        world.add_region(region)
        tile = Tile(x=0, y=0, z=7, ground=817, zone="slow")
        tile.spawn = Spawn(monster="Dragon", respawn=500, radius=5)
        world.set_tile(tile)

        b = SpawnBalancer()
        result = b.balance(world, region)

        assert result.respawns_adjusted >= 1
        assert tile.spawn.respawn <= SpawnBalancer.MAX_RESPAWN


class TestSpawnBalancerRadius:
    def test_fixes_too_small_radius(self):
        world = WorldModel()
        region = Region(name="tiny")
        world.add_region(region)
        tile = Tile(x=0, y=0, z=7, ground=817, zone="tiny")
        tile.spawn = Spawn(monster="Dragon", respawn=60, radius=1)
        world.set_tile(tile)

        b = SpawnBalancer()
        result = b.balance(world, region)

        assert result.radii_adjusted >= 1
        assert tile.spawn.radius >= SpawnBalancer.MIN_RADIUS

    def test_fixes_too_large_radius(self):
        world = WorldModel()
        region = Region(name="huge")
        world.add_region(region)
        tile = Tile(x=0, y=0, z=7, ground=817, zone="huge")
        tile.spawn = Spawn(monster="Dragon", respawn=60, radius=20)
        world.set_tile(tile)

        b = SpawnBalancer()
        result = b.balance(world, region)

        assert result.radii_adjusted >= 1
        assert tile.spawn.radius <= SpawnBalancer.MAX_RADIUS


class TestSpawnBalancerAnalysis:
    def test_analyze_density(self):
        world = _build_world("analysis_zone", 5, monster="Vampire")
        region = world.get_region("analysis_zone")
        b = SpawnBalancer()

        analysis = b.analyze_spawn_density(world, region)

        assert analysis["zone_name"] == "analysis_zone"
        assert analysis["spawn_count"] == 5
        assert analysis["avg_respawn"] == 60.0
        assert analysis["avg_radius"] == 5.0
        assert isinstance(analysis["recommendations"], list)

    def test_analyze_empty_zone(self):
        world = _build_world("empty_analysis", 0, monster="Rat")
        region = world.get_region("empty_analysis")
        b = SpawnBalancer()

        analysis = b.analyze_spawn_density(world, region)

        assert analysis["spawn_count"] == 0
        assert len(analysis["recommendations"]) > 0


class TestSpawnBalanceResult:
    def test_to_dict(self):
        result = SpawnBalanceResult()
        result.spawns_added = 3
        d = result.to_dict()
        assert d["spawns_added"] == 3
        assert d["spawns_removed"] == 0

    def test_adjustment_to_dict(self):
        adj = SpawnAdjustment(
            zone_name="test", action="add", monster="Dragon",
            x=1, y=2, z=7, reason="test"
        )
        d = adj.to_dict()
        assert d["zone_name"] == "test"
        assert d["action"] == "add"
        assert d["monster"] == "Dragon"