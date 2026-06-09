from __future__ import annotations

import pytest

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.expansion.boss_expander import BossExpander, BossExpansionResult


def _build_world_with_region() -> WorldModel:
    world = WorldModel()
    region = Region(name="hunt", theme="cave", min_level=100, max_level=250)
    world.add_region(region)
    for x in range(20):
        for y in range(20):
            tile = Tile(x=x, y=y, z=7, ground=818, zone="hunt")
            if (x + y) % 4 == 0:
                tile.spawn = Spawn(monster="Dragon", respawn=60, radius=5)
            world.set_tile(tile)
    return world


def _count_spawns(world: WorldModel) -> int:
    return sum(1 for t in world.tiles.values() if t.spawn is not None)


class TestBossExpanderInit:
    def test_create(self):
        b = BossExpander()
        assert b is not None

    def test_room_sizes(self):
        b = BossExpander()
        assert b.ROOM_SIZE_MIN == 8
        assert b.ROOM_SIZE_MAX == 14


class TestBossExpanderRun:
    def test_creates_boss_room(self):
        world = _build_world_with_region()
        original = world.tile_count()
        b = BossExpander()
        result = b.expand(world, max_rooms=1, difficulty="medium")

        assert isinstance(result, BossExpansionResult)
        assert world.tile_count() > original
        assert result.rooms_created == 1
        assert result.bosses_placed == 1

    def test_adds_structure(self):
        world = _build_world_with_region()
        b = BossExpander()
        b.expand(world, max_rooms=1)
        boss_structures = [s for s in world.structures
                           if s.category == "boss_room"]
        assert len(boss_structures) >= 1

    def test_adds_region(self):
        world = _build_world_with_region()
        original_regions = world.region_count()
        b = BossExpander()
        b.expand(world, max_rooms=1)
        assert world.region_count() > original_regions

    def test_boss_spawn_exists(self):
        world = _build_world_with_region()
        b = BossExpander()
        result = b.expand(world, max_rooms=1, difficulty="easy")
        assert result.bosses_placed == 1

    def test_respects_max_rooms(self):
        world = _build_world_with_region()
        b = BossExpander()
        result = b.expand(world, max_rooms=1)
        assert result.rooms_created <= 1

    def test_different_difficulties(self):
        world = _build_world_with_region()
        b = BossExpander()
        for diff in ["easy", "medium", "hard"]:
            result = b.expand(world, max_rooms=1, difficulty=diff)
            assert result.rooms_created >= 0

    def test_no_regions_no_expansion(self):
        world = WorldModel()
        b = BossExpander()
        result = b.expand(world, max_rooms=2)
        assert result.rooms_created == 0

    def test_get_room_size(self):
        b = BossExpander()
        assert b._get_room_size("easy") == 8
        assert b._get_room_size("medium") == 10
        assert b._get_room_size("hard") == 14
        assert b._get_room_size("unknown") == 10


class TestBossExpansionResult:
    def test_to_dict(self):
        r = BossExpansionResult()
        r.rooms_created = 2
        r.tiles_added = 200
        r.bosses_placed = 2
        d = r.to_dict()
        assert d["rooms_created"] == 2
        assert d["tiles_added"] == 200
        assert d["bosses_placed"] == 2