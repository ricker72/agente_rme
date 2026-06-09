"""Tests for the A* Pathfinder."""

import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.playtest.pathfinder import Pathfinder, PathResult


def _build_grid_world(width: int = 10, height: int = 10, z: int = 7) -> WorldModel:
    world = WorldModel()
    for x in range(width):
        for y in range(height):
            tile = Tile(x=x, y=y, z=z, ground=100)
            world.set_tile(tile)
    return world


def _build_maze_world() -> WorldModel:
    world = WorldModel()
    for x in range(10):
        for y in range(10):
            tile = Tile(x=x, y=y, z=7, ground=100)
            world.set_tile(tile)
    for y in range(5, 8):
        for x in range(2, 8):
            key = Tile.make_key(x, y, 7)
            if key in world.tiles:
                world.tiles[key].ground = None
                world.tiles[key].items = []
    return world


def _build_multi_floor_world() -> WorldModel:
    world = WorldModel()
    for x in range(5):
        for y in range(5):
            world.set_tile(Tile(x=x, y=y, z=7, ground=100))
            world.set_tile(Tile(x=x, y=y, z=6, ground=100))
    return world


class TestPathResult:
    def test_path_result_creation(self):
        result = PathResult(
            waypoints=[(0, 0, 7), (1, 0, 7), (2, 0, 7)],
            distance=2.0, steps=2, floors_traversed=0, reachable=True,
        )
        assert result.reachable is True
        assert result.steps == 2
        assert result.total_distance == 2.0

    def test_path_result_unreachable(self):
        result = PathResult(
            waypoints=[], distance=0.0, steps=0,
            floors_traversed=0, reachable=False,
        )
        assert not result.reachable
        assert result.steps == 0


class TestPathfinderBasic:
    def test_same_position(self):
        world = _build_grid_world()
        pf = Pathfinder(world)
        result = pf.find_path((0, 0, 7), (0, 0, 7))
        assert result.reachable is True
        assert result.steps == 0
        assert result.waypoints == [(0, 0, 7)]

    def test_adjacent_tiles(self):
        world = _build_grid_world()
        pf = Pathfinder(world)
        result = pf.find_path((0, 0, 7), (1, 0, 7))
        assert result.reachable is True
        assert result.steps == 1

    def test_straight_line_distance(self):
        world = _build_grid_world(20, 20)
        pf = Pathfinder(world)
        result = pf.find_path((0, 0, 7), (5, 0, 7))
        assert result.reachable is True
        assert result.steps == 5

    def test_diagonal_path(self):
        world = _build_grid_world(20, 20)
        pf = Pathfinder(world, diagonal=True)
        result = pf.find_path((0, 0, 7), (5, 5, 7))
        assert result.reachable is True
        assert result.steps == 5

    def test_no_diagonal_path(self):
        world = _build_grid_world(20, 20)
        pf = Pathfinder(world, diagonal=False)
        result = pf.find_path((0, 0, 7), (3, 3, 7))
        assert result.reachable is True
        assert result.steps == 6


class TestPathfinderObstacles:
    def test_unreachable_tile(self):
        world = _build_grid_world()
        pf = Pathfinder(world)
        result = pf.find_path((0, 0, 7), (100, 100, 7))
        assert result.reachable is False

    def test_blocked_start(self):
        world = _build_grid_world()
        pf = Pathfinder(world)
        result = pf.find_path((100, 100, 7), (0, 0, 7))
        assert result.reachable is False

    def test_maze_wall_avoidance(self):
        world = _build_maze_world()
        pf = Pathfinder(world, diagonal=False)
        result = pf.find_path((0, 6, 7), (9, 6, 7))
        assert result.reachable is True
        assert result.steps > 2


class TestPathfinderMultiFloor:
    def test_floor_transition(self):
        world = _build_multi_floor_world()
        pf = Pathfinder(world, use_stairs=True)
        result = pf.find_path((0, 0, 7), (0, 0, 6))
        assert result.reachable is True
        assert result.floors_traversed >= 1

    def test_no_stairs_mode(self):
        world = _build_multi_floor_world()
        pf = Pathfinder(world, use_stairs=False)
        result = pf.find_path((0, 0, 7), (0, 0, 6))
        assert result.reachable is False


class TestPathfinderSpawns:
    def test_spawn_penalty(self):
        world = _build_grid_world()
        tile = world.get_tile(2, 0, 7)
        tile.spawn = Spawn(monster="Dragon")
        pf = Pathfinder(world)
        result = pf.find_path((0, 0, 7), (4, 0, 7))
        assert result.reachable is True
        assert result.distance > 0


class TestPathfinderBFS:
    def test_reachable_tiles(self):
        world = _build_grid_world(5, 5)
        pf = Pathfinder(world)
        reachable = pf.reachable_tiles((2, 2, 7), max_steps=10)
        assert len(reachable) == 25

    def test_reachable_limited_steps(self):
        world = _build_grid_world(10, 10)
        pf = Pathfinder(world)
        reachable = pf.reachable_tiles((0, 0, 7), max_steps=2)
        assert len(reachable) <= 9

    def test_coverage_ratio(self):
        world = _build_grid_world(5, 5)
        pf = Pathfinder(world)
        ratio = pf.coverage_ratio((2, 2, 7))
        assert ratio == 1.0

    def test_distance_map(self):
        world = _build_grid_world(5, 5)
        pf = Pathfinder(world)
        dmap = pf.distance_map((2, 2, 7))
        assert (2, 2, 7) in dmap
        assert dmap[(2, 2, 7)] == 0.0
        assert dmap[(3, 2, 7)] == pytest.approx(1.0, abs=0.1)

    def test_nearest_spawn(self):
        world = _build_grid_world(10, 10)
        tile = world.get_tile(5, 5, 7)
        tile.spawn = Spawn(monster="Dragon")
        pf = Pathfinder(world)
        nearest = pf.find_nearest_spawn((0, 0, 7))
        assert nearest is not None
        assert nearest[0] == 5

    def test_nearest_spawn_none(self):
        world = _build_grid_world(5, 5)
        pf = Pathfinder(world)
        nearest = pf.find_nearest_spawn((0, 0, 7))
        assert nearest is None


class TestPathfinderCache:
    def test_clear_cache(self):
        world = _build_grid_world()
        pf = Pathfinder(world)
        pf.find_path((0, 0, 7), (4, 4, 7))
        assert len(pf._tile_cache) > 0
        pf.clear_cache()
        assert len(pf._tile_cache) == 0