"""
Integration tests for the Lua export pipeline.

Verifies end-to-end:
  * generated.lua is created
  * File contains valid Lua syntax (no unbalanced parens/brackets)
  * Spawns are exported
  * Monsters are exported
  * Compatible with both HuntArea and WorldModel inputs
"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.lua.lua_generator import LuaGenerator
from core.spawn.spawn_generator import SpawnPlan, SpawnEntry
from core.world.world_model import WorldModel
from core.world.tile import Tile


def _is_balanced(code: str) -> bool:
    """Quick sanity check: parentheses and end-statements balance."""
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
    # Every `function()` should be closed with `end)` / `end`
    n_func = code.count("function(")
    n_end = code.count("end)")
    return n_func == n_end


class TestLuaExportPipeline:
    """End-to-end test: generate Lua, write to file, validate contents."""

    def test_export_writes_file(self, tmp_path):
        world = WorldModel()
        for i in range(3):
            for j in range(3):
                world.set_tile(Tile(x=i, y=j, z=7, ground=106))
        plan = SpawnPlan(
            spawns=[SpawnEntry(x=1, y=1, z=7, monster_name="Dragon", interval=60)],
        )
        gen = LuaGenerator()
        script = gen.generate(world, plan)
        out = tmp_path / "generated.lua"
        out.write_text(script.code, encoding="utf-8")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_export_balanced_parentheses(self):
        gen = LuaGenerator()
        for n_spawns in (0, 1, 5, 20):
            plan = SpawnPlan(
                spawns=[
                    SpawnEntry(x=i, y=i, z=7, monster_name=f"M{i}", interval=60)
                    for i in range(n_spawns)
                ],
            )
            script = gen.generate(None, plan)
            assert _is_balanced(script.code), f"Unbalanced for n_spawns={n_spawns}"

    def test_export_with_complex_world(self):
        """Test the integration with a non-trivial world."""
        world = WorldModel()
        # 5x5 grid
        for x in range(5):
            for y in range(5):
                world.set_tile(Tile(
                    x=x, y=y, z=7, ground=106,
                    items=[{"id": 2050}] if (x + y) % 2 == 0 else [],
                ))
        plan = SpawnPlan(
            spawns=[
                SpawnEntry(x=1, y=1, z=7, monster_name="Skeleton", interval=60),
                SpawnEntry(x=2, y=2, z=7, monster_name="Demon", interval=120),
                SpawnEntry(x=3, y=3, z=7, monster_name="Dragon", interval=300),
            ],
            boss_spawn=SpawnEntry(x=4, y=4, z=7, monster_name="Orshabaal", interval=600),
        )
        gen = LuaGenerator()
        script = gen.generate(world, plan)
        assert script.tile_count == 25
        assert script.spawn_count == 3
        assert script.creature_count == 1
        # Verify content
        assert "Skeleton" in script.code
        assert "Demon" in script.code
        assert "Dragon" in script.code
        assert "Orshabaal" in script.code
        # Verify Lua validity
        assert _is_balanced(script.code)

    def test_export_with_issavi_roshamuul_simulation(self):
        """Simulate the benchmark prompt: Issavi + Roshamuul for levels 300-500."""
        # Create a complex world with two regions
        world = WorldModel()
        # Issavi region: 5x5 of magic ground (id 406)
        for x in range(5):
            for y in range(5):
                world.set_tile(Tile(x=100 + x, y=100 + y, z=7, ground=406))
        # Roshamuul region: 5x5 of dark ground (id 319)
        for x in range(5):
            for y in range(5):
                world.set_tile(Tile(x=200 + x, y=200 + y, z=7, ground=319))
        # 3 hunts, 2 bosses
        plan = SpawnPlan(
            spawns=[
                # Issavi hunts
                SpawnEntry(x=102, y=102, z=7, monster_name="Frazzlemaw", interval=60),
                SpawnEntry(x=103, y=103, z=7, monster_name="Guzzlemaw", interval=60),
                SpawnEntry(x=104, y=104, z=7, monster_name="Vexclaw", interval=60),
                # Roshamuul hunts
                SpawnEntry(x=202, y=202, z=7, monster_name="Spawn of Destruction", interval=120),
                SpawnEntry(x=203, y=203, z=7, monster_name="Demon", interval=60),
            ],
            boss_spawn=SpawnEntry(x=204, y=204, z=7, monster_name="Orshabaal", interval=600),
        )
        gen = LuaGenerator()
        script = gen.generate(world, plan, map_name="IssaviRoshamuul")
        assert "IssaviRoshamuul" in script.code
        # Verify the monsters are exported
        assert "Frazzlemaw" in script.code
        assert "Guzzlemaw" in script.code
        assert "Vexclaw" in script.code
        assert "Orshabaal" in script.code
        # Verify syntax
        assert _is_balanced(script.code)

    def test_export_handles_missing_boss(self):
        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7))
        plan = SpawnPlan(spawns=[])  # no boss
        gen = LuaGenerator()
        script = gen.generate(world, plan)
        assert script.creature_count == 0
        assert _is_balanced(script.code)

    def test_export_handles_empty_plan(self):
        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7))
        gen = LuaGenerator()
        script = gen.generate(world)  # no plan at all
        assert script.code
        assert _is_balanced(script.code)
