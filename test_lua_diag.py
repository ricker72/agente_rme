"""Smoke test for lua_generator with both call signatures."""
import sys
sys.path.insert(0, '.')

from core.lua.lua_generator import LuaGenerator
from core.spawn.spawn_generator import SpawnPlan, SpawnEntry
from core.world.world_model import WorldModel
from core.world.tile import Tile

# Build a minimal WorldModel
world = WorldModel()
for i in range(3):
    for j in range(3):
        world.set_tile(Tile(x=100 + i, y=200 + j, z=7, ground=106))

# Build a SpawnPlan
plan = SpawnPlan(
    spawns=[
        SpawnEntry(x=101, y=201, z=7, monster_name="Dragon", interval=60),
        SpawnEntry(x=102, y=202, z=7, monster_name="Demon", interval=60),
    ],
    boss_spawn=SpawnEntry(x=104, y=204, z=7, monster_name="Orshabaal", interval=600),
)

gen = LuaGenerator()

print("=== Test 1: generate(world) ===")
try:
    s1 = gen.generate(world)
    print("OK tile_count=", s1.tile_count, "spawn_count=", s1.spawn_count)
    print("First 20 lines:")
    for l in s1.code.split("\n")[:20]:
        print(" ", l)
except Exception as e:
    print("FAIL:", type(e).__name__, e)

print("\n=== Test 2: generate(world, spawn_plan) ===")
try:
    s2 = gen.generate(world, plan)
    print("OK tile_count=", s2.tile_count, "spawn_count=", s2.spawn_count, "creature_count=", s2.creature_count)
except Exception as e:
    print("FAIL:", type(e).__name__, e)

print("\n=== Test 3: generate(world, plan_dict) ===")
try:
    plan_dict = {
        "spawns": [
            {"x": 5, "y": 5, "z": 7, "monster_name": "Rat", "interval": 30},
        ],
        "boss_spawn": None,
    }
    s3 = gen.generate(world, plan_dict)
    print("OK tile_count=", s3.tile_count, "spawn_count=", s3.spawn_count)
except Exception as e:
    print("FAIL:", type(e).__name__, e)

print("\n=== Test 4: generate(None, plan) ===")
try:
    s4 = gen.generate(None, plan)
    print("OK tile_count=", s4.tile_count, "spawn_count=", s4.spawn_count)
except Exception as e:
    print("FAIL:", type(e).__name__, e)
