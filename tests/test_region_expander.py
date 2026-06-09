from __future__ import annotations

import pytest

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.expansion.region_expander import RegionExpander, RegionExpansionResult


def _build_two_regions() -> WorldModel:
    world = WorldModel()
    r1 = Region(name="zone_a", theme="grass")
    r2 = Region(name="zone_b", theme="cave")
    world.add_region(r1)
    world.add_region(r2)

    for x in range(10):
        for y in range(10):
            tile = Tile(x=x, y=y, z=7, ground=817, zone="zone_a")
            world.set_tile(tile)

    for x in range(100, 110):
        for y in range(100, 110):
            tile = Tile(x=x, y=y, z=7, ground=818, zone="zone_b")
            world.set_tile(tile)

    return world


def _build_region_with_gaps() -> WorldModel:
    world = WorldModel()
    r = Region(name="gappy", theme="dirt")
    world.add_region(r)

    for x in range(10):
        for y in range(10):
            if (x + y) % 3 != 0:
                tile = Tile(x=x, y=y, z=7, ground=814, zone="gappy")
                world.set_tile(tile)

    return world


class TestRegionExpanderInit:
    def test_create(self):
        re = RegionExpander()
        assert re is not None

    def test_default_constants(self):
        re = RegionExpander()
        assert re.GAP_FILL_GROUND == 814


class TestRegionExpanderFillGaps:
    def test_fills_gaps(self):
        world = _build_region_with_gaps()
        original = world.tile_count()
        re = RegionExpander()
        result = re.expand(world, fill_gaps=True, connect_regions=False)

        assert isinstance(result, RegionExpansionResult)
        assert world.tile_count() > original
        assert result.tiles_added > 0
        assert result.regions_expanded >= 1

    def test_no_gaps_no_change(self):
        world = WorldModel()
        r = Region(name="full")
        world.add_region(r)
        for x in range(5):
            for y in range(5):
                tile = Tile(x=x, y=y, z=7, ground=817, zone="full")
                world.set_tile(tile)

        re = RegionExpander()
        original = world.tile_count()
        result = re.expand(world, fill_gaps=True, connect_regions=False)
        assert result.tiles_added == 0

    def test_skip_small_regions(self):
        world = WorldModel()
        r = Region(name="tiny")
        world.add_region(r)
        for x in range(2):
            tile = Tile(x=x, y=0, z=7, ground=817, zone="tiny")
            world.set_tile(tile)

        re = RegionExpander()
        result = re.expand(world, fill_gaps=True, connect_regions=False)
        assert result.regions_expanded == 0


class TestRegionExpanderConnect:
    def test_connects_distant_regions(self):
        world = _build_two_regions()
        original = world.tile_count()
        re = RegionExpander()
        result = re.expand(world, fill_gaps=False, connect_regions=True)

        assert world.tile_count() > original
        assert result.connections_made >= 1
        assert result.tiles_added > 0

    def test_skips_close_regions(self):
        world = WorldModel()
        r1 = Region(name="near_a")
        r2 = Region(name="near_b")
        world.add_region(r1)
        world.add_region(r2)

        for x in range(5):
            for y in range(5):
                world.set_tile(Tile(x=x, y=y, z=7, ground=817, zone="near_a"))
                world.set_tile(Tile(x=x + 10, y=y, z=7, ground=817, zone="near_b"))

        re = RegionExpander()
        result = re.expand(world, fill_gaps=False, connect_regions=True)
        assert result.connections_made == 0

    def test_single_region_no_connect(self):
        world = WorldModel()
        r = Region(name="solo")
        world.add_region(r)
        for x in range(5):
            for y in range(5):
                world.set_tile(Tile(x=x, y=y, z=7, ground=817, zone="solo"))

        re = RegionExpander()
        result = re.expand(world, fill_gaps=False, connect_regions=True)
        assert result.connections_made == 0


class TestRegionExpansionResult:
    def test_to_dict(self):
        r = RegionExpansionResult()
        r.regions_expanded = 3
        r.tiles_added = 150
        r.connections_made = 2
        d = r.to_dict()
        assert d["regions_expanded"] == 3
        assert d["tiles_added"] == 150
        assert d["connections_made"] == 2