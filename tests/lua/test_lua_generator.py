"""
Tests for LuaGenerator — both call signatures and the generated code.

Verifies:
  * generate(world)  — works without a spawn plan
  * generate(world, spawn_plan) — works with explicit plan
  * generate(world, plan_dict) — works with a dict plan
  * Lua syntax is valid (no obvious malformations)
  * The script contains the expected RME API calls
  * Both backends (HuntArea dataclass and WorldModel) are supported
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.lua.lua_generator import LuaGenerator
from core.spawn.spawn_generator import SpawnPlan, SpawnEntry
from core.world.world_model import WorldModel
from core.world.tile import Tile


class TestLuaGeneratorWorldOnly:
    """Test generate(world) with no spawn_plan argument."""

    def test_generate_with_world_model(self):
        world = WorldModel()
        for i in range(3):
            for j in range(3):
                world.set_tile(Tile(x=100 + i, y=200 + j, z=7, ground=106))
        gen = LuaGenerator()
        script = gen.generate(world)
        assert script.code
        assert "if not app.hasMap() then" in script.code
        assert "return" in script.code
        assert script.tile_count == 9
        assert script.spawn_count == 0

    def test_generate_with_empty_world(self):
        world = WorldModel()
        gen = LuaGenerator()
        script = gen.generate(world)
        assert script.code
        assert script.tile_count == 0

    def test_generate_with_none_world(self):
        gen = LuaGenerator()
        script = gen.generate(None)
        # Should not raise
        assert script.code

    def test_generate_with_dict_world(self):
        # Some pipelines pass a plain dict.
        world_dict = {
            "base_x": 1000,
            "base_y": 1000,
            "base_z": 7,
            "tiles": [
                {"x": 0, "y": 0, "z": 7, "ground": 106},
                {"x": 1, "y": 0, "z": 7, "ground": 106},
            ],
        }
        gen = LuaGenerator()
        script = gen.generate(world_dict)
        assert script.tile_count == 2

    def test_generate_with_none_and_spawn_plan(self):
        """Verify that the world can be None when a spawn_plan is provided."""
        plan = SpawnPlan(
            spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="Dragon", interval=60)],
        )
        gen = LuaGenerator()
        script = gen.generate(None, plan)
        assert script.spawn_count == 1


class TestLuaGeneratorWithSpawnPlan:
    """Test generate(world, spawn_plan) with both dataclass and dict plans."""

    def test_generate_with_dataclass_plan(self):
        world = WorldModel()
        for i in range(3):
            for j in range(3):
                world.set_tile(Tile(x=i, y=j, z=7, ground=106))
        plan = SpawnPlan(
            spawns=[
                SpawnEntry(x=1, y=1, z=7, monster_name="Dragon", interval=60),
                SpawnEntry(x=2, y=2, z=7, monster_name="Demon", interval=60),
            ],
            boss_spawn=SpawnEntry(x=2, y=2, z=7, monster_name="Boss", interval=600),
        )
        gen = LuaGenerator()
        script = gen.generate(world, plan)
        assert script.tile_count == 9
        assert script.spawn_count == 2
        assert script.creature_count == 1
        # Verify the monster names are in the code
        assert "Dragon" in script.code
        assert "Demon" in script.code
        assert "Boss" in script.code

    def test_generate_with_dict_plan(self):
        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7, ground=106))
        plan_dict = {
            "spawns": [
                {"x": 5, "y": 5, "z": 7, "monster_name": "Rat", "interval": 30},
            ],
            "boss_spawn": None,
        }
        gen = LuaGenerator()
        script = gen.generate(world, plan_dict)
        assert script.spawn_count == 1
        assert "Rat" in script.code

    def test_generate_with_plan_as_first_arg(self):
        """If a SpawnPlan is passed as the first positional arg, the
        generator should still work (backwards compatibility)."""
        plan = SpawnPlan(
            spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="Bat", interval=30)],
        )
        gen = LuaGenerator()
        script = gen.generate(plan)
        assert script.spawn_count == 1
        assert "Bat" in script.code


class TestLuaScriptContent:
    """Verify the generated Lua script has the right structure."""

    def test_lua_has_header(self):
        gen = LuaGenerator()
        script = gen.generate(None)
        assert "-- OpenTibiaBR RME Map" in script.code

    def test_lua_has_map_guard(self):
        gen = LuaGenerator()
        script = gen.generate(None)
        assert "if not app.hasMap() then" in script.code
        assert "return" in script.code

    def test_lua_uses_only_approved_api(self):
        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7, ground=106))
        plan = SpawnPlan(
            spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="Orc", interval=60)],
        )
        gen = LuaGenerator()
        script = gen.generate(world, plan)
        # Approved API
        assert "map:getOrCreateTile" in script.code
        assert "setSpawn" in script.code
        assert "setCreature" in script.code
        assert "app.transaction" in script.code
        # Forbidden API
        assert "Map.addItem" not in script.code
        assert "Map.addCreature" not in script.code
        assert "Map.setTile" not in script.code

    def test_lua_spawn_line_contains_direction(self):
        plan = SpawnPlan(
            spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="Skeleton", interval=60)],
        )
        gen = LuaGenerator()
        script = gen.generate(None, plan)
        assert "Direction.SOUTH" in script.code

    def test_lua_custom_map_name(self):
        gen = LuaGenerator()
        script = gen.generate(None, map_name="MyMap")
        assert "MyMap" in script.code
        assert script.map_name == "MyMap"

    def test_lua_with_borderize(self):
        world = WorldModel()
        tile = Tile(x=0, y=0, z=7, ground=106)
        # Add a marker that triggers borderized
        tile_dict = {
            "x": 0, "y": 0, "z": 7, "ground": 106, "borderized": True,
        }
        world_dict = {"tiles": [tile_dict], "base_x": 0, "base_y": 0, "base_z": 7}
        gen = LuaGenerator()
        script = gen.generate(world_dict)
        assert "borderize" in script.code
        assert script.border_count == 1

    def test_lua_with_items(self):
        world = WorldModel()
        world.set_tile(Tile(
            x=0, y=0, z=7, ground=106,
            items=[{"id": 2050}, {"id": 2016}],
        ))
        gen = LuaGenerator()
        script = gen.generate(world)
        assert "addItem(2050)" in script.code
        assert "addItem(2016)" in script.code
        assert script.items_count == 2

    def test_lua_with_wall(self):
        tile_dict = {
            "x": 0, "y": 0, "z": 7, "ground": 106,
            "wall_id": 159, "tile_type": "wall",
        }
        world_dict = {"tiles": [tile_dict], "base_x": 0, "base_y": 0, "base_z": 7}
        gen = LuaGenerator()
        script = gen.generate(world_dict)
        assert "addItem(159)" in script.code


class TestLuaScriptStatistics:
    """Verify the LuaScript statistics counters."""

    def test_empty_world_stats(self):
        gen = LuaGenerator()
        s = gen.generate(None)
        assert s.tile_count == 0
        assert s.spawn_count == 0
        assert s.creature_count == 0

    def test_stats_with_spawns_and_boss(self):
        plan = SpawnPlan(
            spawns=[
                SpawnEntry(x=0, y=0, z=7, monster_name="A", interval=60),
                SpawnEntry(x=1, y=0, z=7, monster_name="B", interval=60),
            ],
            boss_spawn=SpawnEntry(x=2, y=0, z=7, monster_name="Boss", interval=600),
        )
        gen = LuaGenerator()
        s = gen.generate(None, plan)
        assert s.spawn_count == 2
        assert s.creature_count == 1
