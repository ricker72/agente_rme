from __future__ import annotations

import pytest

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.expansion.hunt_expander import HuntExpander, HuntExpansionResult


def _build_world_with_bounds() -> WorldModel:
    world = WorldModel()
    region = Region(name="base", theme="grass")
    world.add_region(region)
    for x in range(20):
        for y in range(20):
            tile = Tile(x=x, y=y, z=7, ground=817, zone="base")
            world.set_tile(tile)
    return world


def _count_spawns(world: WorldModel) -> int:
    return sum(1 for t in world.tiles.values() if t.spawn is not None)


class TestHuntExpanderInit:
    def test_create(self):
        h = HuntExpander()
        assert h is not None

    def test_default_constants(self):
        h = HuntExpander()
        assert h.DEFAULT_HUNT_SIZE == 15
        assert h.SPAWN_DENSITY == 0.15
        assert "easy" in h.MIN_LEVEL_TIERS
        assert "hard" in h.MIN_LEVEL_TIERS


class TestHuntExpanderRun:
    def test_expands_world(self):
        world = _build_world_with_bounds()
        original = world.tile_count()
        h = HuntExpander()
        result = h.expand(world, max_hunts=2, theme="cave")

        assert isinstance(result, HuntExpansionResult)
        assert world.tile_count() > original
        assert result.tiles_added > 0

    def test_adds_spawns(self):
        world = _build_world_with_bounds()
        original_spawns = _count_spawns(world)
        h = HuntExpander()
        result = h.expand(world, max_hunts=2)

        assert _count_spawns(world) > original_spawns
        assert result.spawns_added > 0

    def test_adds_regions(self):
        world = _build_world_with_bounds()
        original_regions = world.region_count()
        h = HuntExpander()
        h.expand(world, max_hunts=2)
        assert world.region_count() > original_regions

    def test_adds_structures(self):
        world = _build_world_with_bounds()
        h = HuntExpander()
        h.expand(world, max_hunts=1)
        assert world.structure_count() > 0

    def test_respects_max_hunts(self):
        world = _build_world_with_bounds()
        h = HuntExpander()
        result = h.expand(world, max_hunts=1)
        assert len(result.zones_created) <= 1

    def test_expands_with_different_themes(self):
        world = _build_world_with_bounds()
        h = HuntExpander()
        result = h.expand(world, max_hunts=1, theme="hell")
        assert result.tiles_added > 0

    def test_empty_world_no_expansion(self):
        world = WorldModel()
        h = HuntExpander()
        result = h.expand(world, max_hunts=3)
        assert result.tiles_added == 0


class TestHuntExpanderAnalysis:
    def test_classify_area_small(self):
        h = HuntExpander()
        assert h._classify_area_size((0, 0, 5, 5)) == "easy"

    def test_classify_area_medium(self):
        h = HuntExpander()
        assert h._classify_area_size((0, 0, 12, 12)) == "medium"

    def test_classify_area_large(self):
        h = HuntExpander()
        assert h._classify_area_size((0, 0, 20, 20)) == "hard"

    def test_classify_area_huge(self):
        h = HuntExpander()
        assert h._classify_area_size((0, 0, 40, 40)) == "very_hard"


class TestHuntExpansionResult:
    def test_to_dict(self):
        r = HuntExpansionResult()
        r.tiles_added = 100
        r.spawns_added = 10
        d = r.to_dict()
        assert d["tiles_added"] == 100
        assert d["spawns_added"] == 10
        assert d["zones_created"] == []