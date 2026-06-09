"""
Backward-compatibility tests for LuaGenerator.

HITO 26.1B — verifies that every previously-supported call signature
keeps producing the same results, while the new auto-fallback path
also works. No regression allowed.
"""

import os
import sys
import pytest
from dataclasses import dataclass, field
from typing import List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.lua.lua_generator import LuaGenerator
from core.spawn.spawn_generator import (
    SpawnGenerator,
    SpawnPlan,
    SpawnEntry,
)
from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn


# ----------------------------------------------------------------------
# All accepted call signatures
# ----------------------------------------------------------------------


class TestAcceptedCallSignatures:
    """Every public call signature must work without raising."""

    def test_call_with_no_arguments(self):
        gen = LuaGenerator()
        s = gen.generate()
        assert s.code
        assert s.map_name == "GeneratedMap"

    def test_call_with_none(self):
        gen = LuaGenerator()
        s = gen.generate(None)
        assert s.code

    def test_call_with_world_only(self):
        """The regression: this used to fail with "missing required
        argument: spawn_plan". Now it auto-generates one."""
        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7, ground=106))
        gen = LuaGenerator()
        s = gen.generate(world)
        assert s.code

    def test_call_with_world_and_plan(self):
        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7, ground=106))
        plan = SpawnPlan(spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="Rat", interval=60)])
        gen = LuaGenerator()
        s = gen.generate(world, plan)
        assert s.spawn_count == 1

    def test_call_with_plan_as_first_positional(self):
        plan = SpawnPlan(spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="Bat", interval=30)])
        gen = LuaGenerator()
        s = gen.generate(plan)
        assert s.spawn_count == 1

    def test_call_with_hunt_area_kwarg(self):
        @dataclass
        class HuntAreaStub:
            tiles: List = field(default_factory=list)
            rooms: List = field(default_factory=list)
            base_x: int = 100
            base_y: int = 200
            base_z: int = 7
        area = HuntAreaStub(
            tiles=[{"x": 0, "y": 0, "z": 7, "ground": 106}],
        )
        plan = SpawnPlan(spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="X", interval=60)])
        gen = LuaGenerator()
        s = gen.generate(hunt_area=area, spawn_plan=plan)
        assert s.tile_count == 1
        assert s.spawn_count == 1

    def test_call_with_world_and_dict_plan(self):
        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7, ground=106))
        plan = {
            "spawns": [
                {"x": 0, "y": 0, "z": 7, "monster_name": "Rat", "interval": 30}
            ]
        }
        gen = LuaGenerator()
        s = gen.generate(world, plan)
        assert s.spawn_count == 1

    def test_call_with_world_and_explicit_none_plan(self):
        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7, ground=106))
        gen = LuaGenerator()
        s = gen.generate(world, None)
        assert s.code  # auto-fallback produces a valid plan

    def test_call_with_map_name_kwarg(self):
        gen = LuaGenerator()
        s = gen.generate(map_name="MyCustomMap")
        assert s.map_name == "MyCustomMap"
        assert "MyCustomMap" in s.code


# ----------------------------------------------------------------------
# Behavioural compatibility — outputs are the same as before
# ----------------------------------------------------------------------


class TestBehaviouralCompatibility:
    """Make sure nothing about the generated output changed."""

    def test_explicit_plan_unchanged(self):
        """When the caller passes a plan explicitly, the output must
        be exactly the same as before HITO 26.1B."""
        world = WorldModel()
        for i in range(2):
            for j in range(2):
                world.set_tile(Tile(x=i, y=j, z=7, ground=106))
        plan = SpawnPlan(
            spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="X", interval=60)],
            boss_spawn=SpawnEntry(x=1, y=1, z=7, monster_name="Y", interval=600),
        )
        gen = LuaGenerator()
        s = gen.generate(world, plan)
        assert s.tile_count == 4
        assert s.spawn_count == 1
        assert s.creature_count == 1
        assert "X" in s.code
        assert "Y" in s.code

    def test_dict_plan_still_supported(self):
        plan = {
            "spawns": [
                {"x": 0, "y": 0, "z": 7, "monster_name": "Rat", "interval": 30},
            ]
        }
        gen = LuaGenerator()
        s = gen.generate(None, plan)
        assert s.spawn_count == 1
        assert "Rat" in s.code

    def test_only_approved_lua_api(self):
        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7, ground=106))
        plan = SpawnPlan(
            spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="Mob", interval=60)]
        )
        gen = LuaGenerator()
        s = gen.generate(world, plan)
        # Approved
        assert "map:getOrCreateTile" in s.code
        assert "setSpawn" in s.code
        assert "setCreature" in s.code
        assert "app.transaction" in s.code
        assert "if not app.hasMap() then" in s.code
        # Forbidden
        assert "Map.addItem" not in s.code
        assert "Map.addCreature" not in s.code
        assert "Map.setTile" not in s.code
        assert "Map.addNpc" not in s.code

    def test_direction_constant_used(self):
        plan = SpawnPlan(spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="M", interval=60)])
        gen = LuaGenerator()
        s = gen.generate(None, plan)
        assert "Direction.SOUTH" in s.code

    def test_app_hasMap_guard_present(self):
        gen = LuaGenerator()
        s = gen.generate(None)
        assert "if not app.hasMap() then" in s.code
        assert "    return" in s.code

    def test_function_end_blocks_match(self):
        """Every ``function()`` must be closed with ``end)``."""
        for n in (0, 1, 5, 20):
            plan = SpawnPlan(
                spawns=[
                    SpawnEntry(x=i, y=i, z=7, monster_name=f"M{i}", interval=60)
                    for i in range(n)
                ]
            )
            s = LuaGenerator().generate(None, plan)
            assert s.code.count("function(") == s.code.count("end)")


# ----------------------------------------------------------------------
# Backward compatibility with the original room-based SpawnGenerator
# ----------------------------------------------------------------------


class TestRoomBasedSpawnGeneratorBC:
    """The original generate(rooms, ...) signature must still work."""

    def test_room_generator_still_works(self):
        @dataclass
        class _Room:
            x: int
            y: int
            width: int
            height: int
            room_type: str = "spawn"

        gen = SpawnGenerator()
        plan = gen.generate(
            rooms=[_Room(0, 0, 5, 5, room_type="spawn")],
            theme_monsters=["Skeleton", "Demon"],
            level_range=(100, 200),
            base_z=7,
        )
        assert isinstance(plan, SpawnPlan)
        assert len(plan.spawns) >= 1

    def test_room_generator_boss_room(self):
        @dataclass
        class _Room:
            x: int
            y: int
            width: int
            height: int
            room_type: str = "spawn"

        gen = SpawnGenerator()
        plan = gen.generate(
            rooms=[_Room(0, 0, 5, 5, room_type="boss")],
            theme_monsters=["Frazzlemaw"],
            level_range=(300, 500),
            base_z=7,
        )
        assert plan.boss_spawn is not None
        assert plan.boss_spawn.is_boss is True

    def test_room_based_plan_feeds_into_lua_generator(self):
        @dataclass
        class _Room:
            x: int
            y: int
            width: int
            height: int
            room_type: str = "spawn"

        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7, ground=106))

        sg = SpawnGenerator()
        plan = sg.generate(
            rooms=[_Room(0, 0, 5, 5, room_type="spawn")],
            theme_monsters=["Skeleton"],
            level_range=(100, 200),
            base_z=7,
        )
        gen = LuaGenerator()
        s = gen.generate(world, plan)
        assert s.spawn_count >= 1
        assert "Skeleton" in s.code


# ----------------------------------------------------------------------
# No-regression smoke tests for the public API
# ----------------------------------------------------------------------


class TestPublicApiSmokeTests:
    """Make sure none of the original public methods are broken."""

    def test_lua_script_dataclass_unchanged(self):
        from core.lua.lua_generator import LuaScript
        s = LuaScript(code="x", map_name="y", tile_count=1, spawn_count=2,
                      creature_count=3, border_count=4, items_count=5)
        assert s.code == "x"
        assert s.map_name == "y"
        assert s.tile_count == 1
        assert s.spawn_count == 2
        assert s.creature_count == 3
        assert s.border_count == 4
        assert s.items_count == 5

    def test_lua_generator_instantiation(self):
        gen = LuaGenerator()
        assert gen is not None

    def test_generated_code_is_string(self):
        s = LuaGenerator().generate(None)
        assert isinstance(s.code, str)

    def test_generated_code_non_empty(self):
        s = LuaGenerator().generate(None)
        assert len(s.code) > 0
