"""
Tests for SpawnPlan / SpawnGenerator — verify the spawns the Lua generator consumes.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.spawn.spawn_generator import SpawnPlan, SpawnEntry, SpawnGenerator


class _Room:
    """Minimal Room stub for SpawnGenerator."""
    def __init__(self, x, y, width, height, room_type="spawn"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.room_type = room_type


class TestSpawnPlanDataClass:
    """Test the SpawnPlan dataclass behaviour."""

    def test_default_empty(self):
        plan = SpawnPlan()
        assert plan.spawns == []
        assert plan.boss_spawn is None

    def test_with_spawns(self):
        entries = [
            SpawnEntry(x=0, y=0, z=7, monster_name="Dragon", interval=60),
            SpawnEntry(x=1, y=0, z=7, monster_name="Demon", interval=60),
        ]
        plan = SpawnPlan(spawns=entries, boss_spawn=entries[0])
        assert len(plan.spawns) == 2
        assert plan.boss_spawn.monster_name == "Dragon"

    def test_spawn_entry_is_boss(self):
        entry = SpawnEntry(x=0, y=0, z=7, monster_name="Boss", interval=600, is_boss=True)
        assert entry.is_boss is True


class TestSpawnGenerator:
    """Test the SpawnGenerator with rooms."""

    def test_generate_for_spawn_rooms(self):
        gen = SpawnGenerator()
        rooms = [
            _Room(0, 0, 5, 5, room_type="spawn"),
            _Room(10, 10, 5, 5, room_type="spawn"),
        ]
        plan = gen.generate(
            rooms=rooms,
            theme_monsters=["Skeleton", "Demon", "Crypt Warden", "Frazzlemaw"],
            level_range=(100, 200),
            base_z=7,
        )
        assert isinstance(plan, SpawnPlan)
        assert len(plan.spawns) > 0

    def test_generate_for_boss_room(self):
        gen = SpawnGenerator()
        rooms = [_Room(0, 0, 10, 10, room_type="boss")]
        plan = gen.generate(
            rooms=rooms,
            theme_monsters=["Frazzlemaw", "Guzzlemaw"],
            level_range=(300, 500),
            base_z=7,
        )
        assert plan.boss_spawn is not None
        assert plan.boss_spawn.is_boss is True

    def test_generate_with_empty_rooms(self):
        gen = SpawnGenerator()
        plan = gen.generate(
            rooms=[],
            theme_monsters=[],
            level_range=(100, 200),
            base_z=7,
        )
        assert isinstance(plan, SpawnPlan)
        assert len(plan.spawns) == 0
        assert plan.boss_spawn is None

    def test_difficulty_tier_easy(self):
        gen = SpawnGenerator()
        assert gen._difficulty_tier(50) == "easy"
        assert gen._difficulty_tier(199) == "easy"

    def test_difficulty_tier_medium(self):
        gen = SpawnGenerator()
        assert gen._difficulty_tier(200) == "medium"
        assert gen._difficulty_tier(399) == "medium"

    def test_difficulty_tier_hard(self):
        gen = SpawnGenerator()
        assert gen._difficulty_tier(400) == "hard"
        assert gen._difficulty_tier(599) == "hard"

    def test_difficulty_tier_extreme(self):
        gen = SpawnGenerator()
        assert gen._difficulty_tier(600) == "extreme"
        assert gen._difficulty_tier(1000) == "extreme"

    def test_monster_tiers_defined(self):
        gen = SpawnGenerator()
        for tier in ("easy", "medium", "hard", "extreme"):
            assert tier in gen.MONSTER_TIERS
            assert len(gen.MONSTER_TIERS[tier]) > 0


class TestSpawnPlanInLuaGenerator:
    """Test that SpawnPlan is correctly consumed by LuaGenerator."""

    def test_plan_with_no_boss(self):
        from core.lua.lua_generator import LuaGenerator
        plan = SpawnPlan(
            spawns=[
                SpawnEntry(x=0, y=0, z=7, monster_name="A", interval=60),
                SpawnEntry(x=1, y=1, z=7, monster_name="B", interval=60),
                SpawnEntry(x=2, y=2, z=7, monster_name="C", interval=60),
            ],
        )
        gen = LuaGenerator()
        script = gen.generate(None, plan)
        assert script.spawn_count == 3
        assert script.creature_count == 0
        for m in ("A", "B", "C"):
            assert m in script.code

    def test_plan_with_boss(self):
        from core.lua.lua_generator import LuaGenerator
        plan = SpawnPlan(
            spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="Mob", interval=60)],
            boss_spawn=SpawnEntry(x=10, y=10, z=7, monster_name="MegaBoss", interval=600),
        )
        gen = LuaGenerator()
        script = gen.generate(None, plan)
        assert script.spawn_count == 1
        assert script.creature_count == 1
        assert "MegaBoss" in script.code
        assert "Mob" in script.code

    def test_plan_with_zero_interval_uses_default(self):
        from core.lua.lua_generator import LuaGenerator
        plan = SpawnPlan(
            spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="X", interval=0)],
        )
        gen = LuaGenerator()
        script = gen.generate(None, plan)
        # interval=0 should be replaced with 60 (default) to avoid infinite spawn
        assert "setSpawn(60)" in script.code

    def test_plan_with_z_zero_kept_as_zero(self):
        """z=0 is a valid floor in OTBM, it should NOT be replaced with base_z."""
        from core.lua.lua_generator import LuaGenerator
        plan = SpawnPlan(
            spawns=[SpawnEntry(x=0, y=0, z=0, monster_name="Z", interval=60)],
        )
        gen = LuaGenerator()
        script = gen.generate(None, plan, map_name="TestMap")
        # The z=0 should be kept as 0 (ground floor)
        assert "getOrCreateTile(0, 0, 0)" in script.code

    def test_plan_with_z_7_kept(self):
        from core.lua.lua_generator import LuaGenerator
        plan = SpawnPlan(
            spawns=[SpawnEntry(x=0, y=0, z=7, monster_name="Z", interval=60)],
        )
        gen = LuaGenerator()
        script = gen.generate(None, plan, map_name="TestMap")
        assert "getOrCreateTile(0, 0, 7)" in script.code
