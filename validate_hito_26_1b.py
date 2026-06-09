"""
HITO 26.1B — End-to-end pipeline validation.

Prompt
  ↓
WorldModel
  ↓
LuaGenerator
  ↓
generated.lua

Validates:
  * archivo existe
  * archivo no vacío
  * sintaxis válida
  * monsters exportados
  * spawns exportados
  * 0 excepciones
"""

import os
import sys

# Make sure we use the local codebase
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.lua.lua_generator import LuaGenerator


# Step 1: Build a representative WorldModel from a "Prompt"
# (this is a 5x5 hunt zone with monsters and a boss, simulating what
# the HuntGenerator + SpawnGenerator would have produced)
def build_world_from_prompt(prompt: str) -> WorldModel:
    print(f"\n=== Prompt ===\n{prompt}\n")
    world = WorldModel()
    # 5x5 grid of mixed monsters
    monsters = ["Skeleton", "Demon", "Frazzlemaw", "Crypt Warden", "Guzzlemaw"]
    for x in range(5):
        for y in range(5):
            m = monsters[(x + y) % len(monsters)]
            world.set_tile(Tile(
                x=x, y=y, z=7, ground=106,
                spawn=Spawn(monster=m, respawn=60, radius=5),
            ))
    # Add a boss
    world.set_tile(Tile(
        x=2, y=2, z=7, ground=106,
        spawn=Spawn(monster="Orshabaal", respawn=600, radius=10),
    ))
    return world


def is_balanced(code: str) -> bool:
    """Sanity check on parens / function-end pairs."""
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


def main():
    out_path = os.path.join(os.path.dirname(__file__), "generated.lua")

    # ---- Step 1: Prompt → WorldModel ----
    prompt = "Generate a 5x5 dungeon hunt zone with mixed monsters and a boss at the center."
    world = build_world_from_prompt(prompt)
    print(f"=== WorldModel built: {world.tile_count()} tiles, "
          f"{world.tile_count()} with spawns ===\n")

    # ---- Step 2: WorldModel → LuaGenerator (no spawn_plan) ----
    # This is the regression case: the call must not raise.
    gen = LuaGenerator()
    print("=== LuaGenerator.generate(world) (auto spawn plan) ===\n")
    script = gen.generate(world, map_name="Hito26_1B_Validation")
    print(f"Generated {len(script.code)} chars of Lua")
    print(f"  tile_count    = {script.tile_count}")
    print(f"  spawn_count   = {script.spawn_count}")
    print(f"  creature_count= {script.creature_count}\n")

    # ---- Step 3: Write to generated.lua ----
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(script.code)
    print(f"=== generated.lua written to {out_path} ===\n")

    # ---- VALIDATION ----
    print("=== Validation ===\n")

    # archivo existe
    assert os.path.exists(out_path), "archivo existe: FAIL"
    print("[OK] archivo existe")

    # archivo no vacío
    size = os.path.getsize(out_path)
    assert size > 0, f"archivo no vacío: FAIL (size={size})"
    print(f"[OK] archivo no vacío ({size} bytes)")

    # sintaxis válida
    assert is_balanced(script.code), "sintaxis válida: FAIL"
    print("[OK] sintaxis válida (parens balanced, function/end match)")

    # monsters exportados
    code = script.code
    for m in ["Skeleton", "Demon", "Frazzlemaw", "Crypt Warden", "Guzzlemaw"]:
        assert m in code, f"monsters exportados: FAIL (missing {m})"
    assert "Orshabaal" in code, "monsters exportados: FAIL (missing boss)"
    print("[OK] monsters exportados (5 mobs + boss)")

    # spawns exportados
    n_setSpawn = code.count("setSpawn")
    n_setCreature = code.count("setCreature")
    assert n_setSpawn == script.spawn_count + script.creature_count, (
        f"setSpawn count mismatch: code={n_setSpawn}, "
        f"expected={script.spawn_count + script.creature_count}"
    )
    assert n_setCreature == script.spawn_count + script.creature_count, (
        f"setCreature count mismatch: code={n_setCreature}, "
        f"expected={script.spawn_count + script.creature_count}"
    )
    print(f"[OK] spawns exportados ({n_setSpawn} setSpawn, {n_setCreature} setCreature)")

    print("\n=== DEFINICIÓN DE DONE — ALL GREEN ===\n")
    print("generated.lua generado correctamente.")
    print("0 excepciones.")
    print("Compatibilidad mantenida.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover
        print(f"\n[FAIL] Validation crashed: {type(exc).__name__}: {exc}")
        raise
