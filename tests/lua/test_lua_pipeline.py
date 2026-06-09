"""
End-to-end Lua export pipeline tests.

HITO 26.1B — full pipeline:

    Prompt
      ↓
    WorldModel (built by HuntGenerator or by hand)
      ↓
    LuaGenerator
      ↓
    generated.lua

These tests verify the file is created, is non-empty, has valid
syntax, and exports both monsters and spawns.
"""

import os
import sys
import tempfile
import re
import pytest
from pathlib import Path

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
# Helpers
# ----------------------------------------------------------------------


def _is_balanced(code: str) -> bool:
    """Quick sanity check on parens/brackets/end-statements."""
    parens = 0
    for c in code:
        if c == "(":
            parens += 1
        elif c == ")":
            parens -= 1
        if parens < 0:
            return False
    if parens != 0:
        return False
    n_func = code.count("function(")
    n_end = code.count("end)")
    return n_func == n_end


def _lua_function_blocks_balance(code: str) -> bool:
    """Verify that every ``function()`` has a matching ``end)``."""
    n_func = code.count("function(")
    n_end = code.count("end)")
    return n_func == n_end


# ----------------------------------------------------------------------
# Pipeline: Prompt → WorldModel → generated.lua
# ----------------------------------------------------------------------


class TestLuaPipeline:
    """Full pipeline integration tests."""

    def test_pipeline_world_to_lua_file(self, tmp_path):
        """Build a small world, run LuaGenerator, write to disk, validate."""
        world = WorldModel()
        for x in range(3):
            for y in range(3):
                world.set_tile(Tile(
                    x=x, y=y, z=7, ground=106,
                    spawn=Spawn(monster=f"Mob_{x}_{y}", respawn=60, radius=5),
                ))

        gen = LuaGenerator()
        script = gen.generate(world)

        out = tmp_path / "generated.lua"
        out.write_text(script.code, encoding="utf-8")

        # archivo existe
        assert out.exists()
        # archivo no vacío
        assert out.stat().st_size > 0
        # sintaxis válida
        assert _is_balanced(script.code)
        assert _lua_function_blocks_balance(script.code)
        # monsters exportados
        for x in range(3):
            for y in range(3):
                assert f"Mob_{x}_{y}" in script.code

    def test_pipeline_with_explicit_plan(self, tmp_path):
        """Run pipeline with an explicit spawn plan."""
        world = WorldModel()
        for i in range(3):
            world.set_tile(Tile(x=i, y=0, z=7, ground=106))

        plan = SpawnPlan(
            spawns=[
                SpawnEntry(x=0, y=0, z=7, monster_name="Skeleton", interval=60),
                SpawnEntry(x=1, y=0, z=7, monster_name="Demon", interval=60),
            ],
            boss_spawn=SpawnEntry(x=2, y=0, z=7, monster_name="Orshabaal", interval=600),
        )

        gen = LuaGenerator()
        script = gen.generate(world, plan)

        out = tmp_path / "generated.lua"
        out.write_text(script.code, encoding="utf-8")

        assert out.exists()
        assert out.stat().st_size > 0
        assert "Skeleton" in script.code
        assert "Demon" in script.code
        assert "Orshabaal" in script.code
        assert _is_balanced(script.code)
        assert _lua_function_blocks_balance(script.code)

    def test_pipeline_complex_world_5x5(self, tmp_path):
        """5x5 world with mixed monsters and a boss."""
        world = WorldModel()
        monsters = ["Rat", "Bat", "Skeleton", "Demon", "Dragon"]
        for x in range(5):
            for y in range(5):
                m_idx = (x + y) % len(monsters)
                world.set_tile(Tile(
                    x=x, y=y, z=7, ground=106,
                    spawn=Spawn(monster=monsters[m_idx], respawn=60, radius=5),
                ))
        # Replace one tile with a boss
        world.set_tile(Tile(
            x=2, y=2, z=7, ground=106,
            spawn=Spawn(monster="MegaBoss", respawn=600, radius=8),
        ))

        gen = LuaGenerator()
        script = gen.generate(world)

        out = tmp_path / "generated.lua"
        out.write_text(script.code, encoding="utf-8")

        # archivo existe y no vacío
        assert out.exists()
        assert out.stat().st_size > 0
        # sintaxis válida
        assert _is_balanced(script.code)
        assert _lua_function_blocks_balance(script.code)
        # monsters exportados
        for m in monsters:
            assert m in script.code
        # boss exportado
        assert "MegaBoss" in script.code
        # spawns exportados (setSpawn + setCreature)
        assert script.spawn_count >= 24
        assert script.creature_count == 1

    def test_pipeline_with_two_zones(self, tmp_path):
        """Multi-zone world: 2 themes, 2 monster pools."""
        world = WorldModel()
        # Issavi zone (ground 406)
        for x in range(3):
            for y in range(3):
                world.set_tile(Tile(
                    x=100 + x, y=100 + y, z=7, ground=406,
                    spawn=Spawn(monster="Frazzlemaw", respawn=60, radius=5),
                ))
        # Roshamuul zone (ground 319)
        for x in range(3):
            for y in range(3):
                world.set_tile(Tile(
                    x=200 + x, y=200 + y, z=7, ground=319,
                    spawn=Spawn(monster="Demon", respawn=60, radius=5),
                ))

        gen = LuaGenerator()
        script = gen.generate(world, map_name="IssaviRoshamuul")

        out = tmp_path / "generated.lua"
        out.write_text(script.code, encoding="utf-8")

        assert out.exists()
        assert "IssaviRoshamuul" in script.code
        assert "Frazzlemaw" in script.code
        assert "Demon" in script.code
        assert _is_balanced(script.code)
        assert _lua_function_blocks_balance(script.code)

    def test_pipeline_empty_world(self, tmp_path):
        """Even with an empty world, the pipeline should not crash."""
        world = WorldModel()
        gen = LuaGenerator()
        script = gen.generate(world)
        out = tmp_path / "generated.lua"
        out.write_text(script.code, encoding="utf-8")
        assert out.exists()
        assert out.stat().st_size > 0
        assert _is_balanced(script.code)

    def test_pipeline_no_exception_on_realistic_input(self):
        """Simulate the full benchmark prompt flow.

        25 tiles total: 24 regular spawns + 1 boss (counted as creature).
        """
        world = WorldModel()
        # 5x5 grid of mixed monsters
        for x in range(5):
            for y in range(5):
                world.set_tile(Tile(
                    x=x, y=y, z=7, ground=106,
                    spawn=Spawn(
                        monster="Crypt Warden" if (x + y) % 2 == 0 else "Skeleton",
                        respawn=60,
                        radius=5,
                    ),
                ))
        # Add a boss in the middle
        world.set_tile(Tile(
            x=2, y=2, z=7, ground=106,
            spawn=Spawn(monster="Orshabaal", respawn=600, radius=10),
        ))

        gen = LuaGenerator()
        # Both call patterns must work
        script1 = gen.generate(world)  # auto spawn plan
        script2 = gen.generate(world, None)  # explicit None
        script3 = gen.generate(world, SpawnPlan())  # explicit empty plan

        for s in (script1, script2, script3):
            assert s.code
            assert _is_balanced(s.code)
            assert _lua_function_blocks_balance(s.code)
        # script1 has spawns from the world: 24 regular + 1 boss (creature)
        assert script1.spawn_count == 24
        assert script1.creature_count == 1


# ----------------------------------------------------------------------
# Spawn-plan-derivation tests that exercise the pipeline
# ----------------------------------------------------------------------


class TestSpawnDerivationInPipeline:
    """The auto spawn plan derivation must produce valid Lua."""

    def test_auto_plan_uses_world_spawns(self):
        world = WorldModel()
        for i in range(4):
            world.set_tile(Tile(
                x=i, y=0, z=7, ground=106,
                spawn=Spawn(monster=f"AutoMob{i}", respawn=60, radius=5),
            ))

        gen = LuaGenerator()
        # No spawn_plan provided — auto-fallback must build one
        script = gen.generate(world)
        assert script.spawn_count == 4
        for i in range(4):
            assert f"AutoMob{i}" in script.code
        # Lua APIs are used
        assert "setSpawn" in script.code
        assert "setCreature" in script.code

    def test_auto_plan_with_boss(self):
        world = WorldModel()
        world.set_tile(Tile(
            x=0, y=0, z=7, ground=106,
            spawn=Spawn(monster="Orshabaal", respawn=600, radius=10),
        ))
        world.set_tile(Tile(
            x=1, y=0, z=7, ground=106,
            spawn=Spawn(monster="Skeleton", respawn=60, radius=5),
        ))

        gen = LuaGenerator()
        script = gen.generate(world)
        assert script.creature_count == 1
        assert "Orshabaal" in script.code
        assert "Skeleton" in script.code

    def test_spawn_generator_then_lua_generator(self):
        """Run the full chain: SpawnGenerator → SpawnPlan → LuaGenerator."""
        world = WorldModel()
        for i in range(3):
            for j in range(3):
                world.set_tile(Tile(
                    x=i, y=j, z=7, ground=106,
                    spawn=Spawn(monster="Skeleton", respawn=60, radius=5),
                ))
        # Add a boss
        world.set_tile(Tile(
            x=1, y=1, z=7, ground=106,
            spawn=Spawn(monster="Boss", respawn=600, radius=10),
        ))

        # Build a SpawnPlan via the generator
        sg = SpawnGenerator()
        plan = sg.generate_for_world(world)
        assert plan.boss_spawn is not None
        assert plan.boss_spawn.monster_name == "Boss"
        assert len(plan.spawns) >= 1

        # Feed it into LuaGenerator
        gen = LuaGenerator()
        script = gen.generate(world, plan)
        assert script.spawn_count >= 1
        assert script.creature_count == 1
        assert "Boss" in script.code
        assert _is_balanced(script.code)
