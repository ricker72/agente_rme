"""
Tests for the world → SpawnPlan auto-generation path.

HITO 26.1B — when a caller invokes ``LuaGenerator.generate(world)``
without an explicit spawn plan, the generator must transparently
build a :class:`SpawnPlan` from the world. These tests exercise
``SpawnGenerator.generate_for_world`` directly and the
:func:`LuaGenerator.generate` auto-fallback end-to-end.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.spawn.spawn_generator import (
    SpawnGenerator,
    SpawnPlan,
    SpawnEntry,
)
from core.lua.lua_generator import LuaGenerator
from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn


def _make_tile(x: int, y: int, z: int = 7, *, monster: str = None,
               respawn: int = 60, is_boss: bool = False) -> Tile:
    """Build a Tile, optionally with a Spawn attached."""
    tile = Tile(x=x, y=y, z=z, ground=106)
    if monster is not None:
        tile.spawn = Spawn(monster=monster, respawn=respawn, radius=5)
    return tile


# ----------------------------------------------------------------------
# Direct SpawnGenerator.generate_for_world tests
# ----------------------------------------------------------------------


class TestSpawnGeneratorGenerateForWorld:
    """The new ``generate_for_world`` method on SpawnGenerator."""

    def test_none_returns_empty_plan(self):
        gen = SpawnGenerator()
        plan = gen.generate_for_world(None)
        assert isinstance(plan, SpawnPlan)
        assert plan.spawns == []
        assert plan.boss_spawn is None

    def test_empty_world_returns_empty_plan(self):
        gen = SpawnGenerator()
        plan = gen.generate_for_world(WorldModel())
        assert plan.spawns == []
        assert plan.boss_spawn is None

    def test_world_with_tiles_no_spawns(self):
        gen = SpawnGenerator()
        world = WorldModel()
        for i in range(3):
            world.set_tile(_make_tile(i, i))
        plan = gen.generate_for_world(world)
        assert plan.spawns == []

    def test_world_with_regular_spawns(self):
        gen = SpawnGenerator()
        world = WorldModel()
        world.set_tile(_make_tile(0, 0, monster="Skeleton", respawn=60))
        world.set_tile(_make_tile(1, 0, monster="Demon", respawn=60))
        plan = gen.generate_for_world(world)
        assert len(plan.spawns) == 2
        monsters = sorted(s.monster_name for s in plan.spawns)
        assert monsters == ["Demon", "Skeleton"]
        assert plan.boss_spawn is None

    def test_world_with_boss_spawn(self):
        gen = SpawnGenerator()
        world = WorldModel()
        world.set_tile(_make_tile(0, 0, monster="Skeleton", respawn=60))
        world.set_tile(_make_tile(5, 5, monster="Orshabaal", respawn=600))
        plan = gen.generate_for_world(world)
        assert plan.boss_spawn is not None
        assert plan.boss_spawn.monster_name == "Orshabaal"
        assert plan.boss_spawn.is_boss is True
        # The other spawn must still be in the spawns list
        names = {s.monster_name for s in plan.spawns}
        assert "Skeleton" in names

    def test_world_with_dict_spawn_object(self):
        gen = SpawnGenerator()
        world = WorldModel()
        tile = _make_tile(0, 0)
        tile.spawn = {"monster": "Dragon", "respawn": 60, "radius": 5}
        world.set_tile(tile)
        plan = gen.generate_for_world(world)
        assert len(plan.spawns) == 1
        assert plan.spawns[0].monster_name == "Dragon"

    def test_dict_world_with_spawns_key(self):
        gen = SpawnGenerator()
        world = {
            "spawns": [
                {"x": 0, "y": 0, "z": 7, "monster_name": "Rat", "interval": 30},
                {"x": 1, "y": 1, "z": 7, "monster_name": "Bat", "interval": 30},
            ]
        }
        plan = gen.generate_for_world(world)
        assert len(plan.spawns) == 2
        names = {s.monster_name for s in plan.spawns}
        assert names == {"Rat", "Bat"}

    def test_dict_world_with_boss_spawn(self):
        gen = SpawnGenerator()
        world = {
            "spawns": [
                {"x": 0, "y": 0, "z": 7, "monster_name": "Mob", "interval": 60},
            ],
            "boss_spawn": {
                "x": 10, "y": 10, "z": 7, "monster_name": "Boss", "interval": 600
            },
        }
        plan = gen.generate_for_world(world)
        assert plan.boss_spawn is not None
        assert plan.boss_spawn.monster_name == "Boss"

    def test_dict_world_empty(self):
        gen = SpawnGenerator()
        plan = gen.generate_for_world({})
        assert isinstance(plan, SpawnPlan)
        assert plan.spawns == []
        assert plan.boss_spawn is None

    def test_preserves_tile_coordinates(self):
        gen = SpawnGenerator()
        world = WorldModel()
        world.set_tile(_make_tile(123, 456, z=9, monster="Dragon", respawn=60))
        plan = gen.generate_for_world(world)
        assert plan.spawns[0].x == 123
        assert plan.spawns[0].y == 456
        assert plan.spawns[0].z == 9


# ----------------------------------------------------------------------
# LuaGenerator auto-fallback tests
# ----------------------------------------------------------------------


class TestLuaGeneratorAutoSpawnPlan:
    """Verify the new auto-fallback in LuaGenerator.generate()."""

    def test_generate_world_with_spawns_auto_uses_them(self):
        """When world has Tile.spawn, the auto-fallback should pick them up."""
        world = WorldModel()
        for i in range(3):
            world.set_tile(_make_tile(i, 0, monster=f"Mob{i}", respawn=60))
        gen = LuaGenerator()
        script = gen.generate(world)
        assert script.spawn_count == 3
        for i in range(3):
            assert f"Mob{i}" in script.code

    def test_generate_world_no_spawns_still_runs(self):
        """An empty world must still produce a valid script (no exception)."""
        world = WorldModel()
        world.set_tile(_make_tile(0, 0))
        gen = LuaGenerator()
        script = gen.generate(world)
        assert script.code
        assert script.spawn_count == 0

    def test_generate_world_boss_appears_in_script(self):
        """A boss on a tile should be reflected in the generated Lua."""
        world = WorldModel()
        world.set_tile(_make_tile(0, 0, monster="Skeleton", respawn=60))
        world.set_tile(_make_tile(5, 5, monster="Orshabaal", respawn=600))
        gen = LuaGenerator()
        script = gen.generate(world)
        assert "Orshabaal" in script.code
        assert "Skeleton" in script.code
        assert script.creature_count == 1

    def test_explicit_spawn_plan_takes_precedence(self):
        """If the caller passes a plan, it wins over the world's auto plan."""
        world = WorldModel()
        world.set_tile(_make_tile(0, 0, monster="WorldMob", respawn=60))
        explicit = SpawnPlan(
            spawns=[SpawnEntry(x=1, y=1, z=7, monster_name="Explicit", interval=60)]
        )
        gen = LuaGenerator()
        script = gen.generate(world, explicit)
        assert "Explicit" in script.code
        # The world-mob should NOT have leaked into the script
        assert "WorldMob" not in script.code

    def test_generate_with_explicit_dict_plan_does_not_auto_fallback(self):
        world = WorldModel()
        world.set_tile(_make_tile(0, 0, monster="LeakMonster", respawn=60))
        plan = {
            "spawns": [
                {"x": 0, "y": 0, "z": 7, "monster_name": "Planned", "interval": 60}
            ]
        }
        gen = LuaGenerator()
        script = gen.generate(world, plan)
        assert "Planned" in script.code
        assert "LeakMonster" not in script.code
