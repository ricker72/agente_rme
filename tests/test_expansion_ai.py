from __future__ import annotations

import pytest

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.expansion.expansion_ai import ExpansionAI, ExpansionReport, ExpansionResult


def _build_small_world() -> WorldModel:
    world = WorldModel()
    region = Region(name="starter", theme="grass", min_level=1, max_level=50)
    world.add_region(region)
    for x in range(10):
        for y in range(10):
            tile = Tile(x=x, y=y, z=7, ground=817, zone="starter")
            if (x + y) % 5 == 0:
                tile.spawn = Spawn(monster="Rat", respawn=60, radius=5)
            world.set_tile(tile)
    return world


def _build_empty_world() -> WorldModel:
    return WorldModel()


def _count_spawns(world: WorldModel) -> int:
    return sum(1 for t in world.tiles.values() if t.spawn is not None)


class TestExpansionAIInit:
    def test_create(self):
        ai = ExpansionAI()
        assert ai is not None

    def test_has_all_expanders(self):
        ai = ExpansionAI()
        assert ai._hunt_expander is not None
        assert ai._boss_expander is not None
        assert ai._region_expander is not None
        assert ai._quest_expander is not None
        assert ai._road_expander is not None


class TestExpansionAIRun:
    def test_expand_small_world(self):
        world = _build_small_world()
        original_tiles = world.tile_count()
        ai = ExpansionAI()

        expanded, report = ai.expand(world)

        assert expanded is not None
        assert isinstance(report, ExpansionReport)
        assert report.expanded is True
        assert world.tile_count() > original_tiles

    def test_expand_returns_same_world(self):
        world = _build_small_world()
        ai = ExpansionAI()
        expanded, _ = ai.expand(world)
        assert expanded is world

    def test_expand_empty_world(self):
        world = _build_empty_world()
        ai = ExpansionAI()
        expanded, report = ai.expand(world, max_hunts=0, max_boss_rooms=0,
                                     max_quest_zones=0)
        assert report.tiles_original == 0
        assert report.tiles_final == 0

    def test_expand_adds_regions(self):
        world = _build_small_world()
        original_regions = world.region_count()
        ai = ExpansionAI()
        _, report = ai.expand(world)
        assert world.region_count() > original_regions

    def test_expand_adds_structures(self):
        world = _build_small_world()
        ai = ExpansionAI()
        _, report = ai.expand(world)
        assert world.structure_count() > 0

    def test_expand_adds_spawns(self):
        world = _build_small_world()
        original_spawns = _count_spawns(world)
        ai = ExpansionAI()
        ai.expand(world)
        assert _count_spawns(world) > original_spawns

    def test_expand_custom_params(self):
        world = _build_small_world()
        ai = ExpansionAI()
        _, report = ai.expand(world, max_hunts=1, max_boss_rooms=0,
                              max_quest_zones=1, theme="hell")
        assert report.expanded is True


class TestExpansionAIReport:
    def test_report_to_dict(self):
        world = _build_small_world()
        ai = ExpansionAI()
        _, report = ai.expand(world)
        d = report.to_dict()
        assert "tiles_original" in d
        assert "tiles_final" in d
        assert "expanded" in d
        assert d["expanded"] is True

    def test_report_tiles_added(self):
        world = _build_small_world()
        ai = ExpansionAI()
        _, report = ai.expand(world)
        assert report.tiles_added > 0

    def test_report_has_steps(self):
        world = _build_small_world()
        ai = ExpansionAI()
        _, report = ai.expand(world)
        assert len(report.results) >= 4
        for step in report.results:
            assert isinstance(step, ExpansionResult)


class TestExpansionAIAnalyze:
    def test_analyze_small_world(self):
        world = _build_small_world()
        ai = ExpansionAI()
        analysis = ai.analyze(world)
        assert analysis["tile_count"] == 100
        assert analysis["region_count"] == 1
        assert analysis["expansion_needed"] is True

    def test_analyze_empty_world(self):
        world = _build_empty_world()
        ai = ExpansionAI()
        analysis = ai.analyze(world)
        assert analysis["tile_count"] == 0
        assert analysis["expansion_needed"] is True

    def test_analyze_returns_recommendations(self):
        world = _build_small_world()
        ai = ExpansionAI()
        analysis = ai.analyze(world)
        assert isinstance(analysis["recommendations"], list)
        assert len(analysis["recommendations"]) > 0


class TestExpansionResult:
    def test_to_dict(self):
        r = ExpansionResult(step_name="test", success=True, tiles_after=50)
        d = r.to_dict()
        assert d["step_name"] == "test"
        assert d["success"] is True