"""
HITO 16 - Procedural World Generation: Continent Generator tests
================================================================

Verifies that the ContinentGenerator:
    - accepts a WorldPlan and returns a WorldModel
    - tiles, structures, regions and spawns are produced
    - cities, dungeons, hunts, bosses and quests are all represented
    - the AIArchitect integration works (prompt -> plan -> world)
    - roads and rivers are placed
    - the result is deterministic given a seed
    - helper functions (generate_continent, generate_from_prompt) work
    - the result is a valid WorldModel that passes the WorldValidator

NOTE: Tests use small world sizes (50-80 tiles) to keep runtime fast.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.world import WorldModel, Structure
from core.world import WorldValidator
from core.architect import AIArchitect
from core.procedural import (
    ContinentGenerator,
    ContinentResult,
    generate_continent,
    generate_from_prompt,
)

# Test world size - keeps tests fast
TEST_W = 60
TEST_H = 60


# =============================================================================
# Tests
# =============================================================================


def test_continent_generator_creation():
    """ContinentGenerator should be instantiable with no args."""
    g = ContinentGenerator(seed=42)
    assert g is not None
    print("  [OK] test_continent_generator_creation")


def test_continent_generator_creation_with_seed():
    """A specific seed should be honoured."""
    g = ContinentGenerator(seed=1234)
    assert g is not None
    print("  [OK] test_continent_generator_creation_with_seed")


def test_generate_continent_accepts_worldplan():
    """generate_continent should accept a WorldPlan and return a WorldModel."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts level 200 and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    world = generate_continent(plan, seed=42)
    assert isinstance(world, WorldModel)
    assert world.tile_count() > 0
    print("  [OK] test_generate_continent_accepts_worldplan")


def test_generate_continent_world_has_tiles():
    """A continent should have plenty of tiles."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts level 200 and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    world = generate_continent(plan, seed=42)
    assert world.tile_count() > 100
    print("  [OK] test_generate_continent_world_has_tiles")


def test_generate_continent_world_has_structures():
    """A world built from a plan should have structures registered."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts level 200 and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    world = generate_continent(plan, seed=42)
    assert world.structure_count() >= 1
    print("  [OK] test_generate_continent_world_has_structures")


def test_generate_continent_world_has_regions():
    """Regions should be added for each placed zone."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    world = generate_continent(plan, seed=42)
    assert world.region_count() >= 1
    kinds = {r.name.split("_")[0] for r in world.regions}
    assert "hunt" in kinds or "city" in kinds or "boss" in kinds
    print("  [OK] test_generate_continent_world_has_regions")


def test_generate_continent_world_has_spawns():
    """Hunt zones and boss zones should have at least one spawn each."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts level 200 and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    world = generate_continent(plan, seed=42)
    spawn_count = sum(1 for t in world.tiles.values() if t.spawn is not None)
    assert spawn_count >= 1
    print("  [OK] test_generate_continent_world_has_spawns")


def test_generate_continent_world_has_roads():
    """A world with multiple zones should have road tiles."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    world = generate_continent(plan, seed=42)
    road_tiles = sum(
        1 for t in world.tiles.values() if t.zone and t.zone.startswith("road:")
    )
    assert road_tiles > 0
    print("  [OK] test_generate_continent_world_has_roads")


def test_generate_continent_deterministic_with_seed():
    """Two runs with the same seed should produce the same world."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts level 200 and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    w1 = generate_continent(plan, seed=99)
    w2 = generate_continent(plan, seed=99)
    assert w1.tile_count() == w2.tile_count()
    sample = list(w1.tiles.values())[:100]
    for t1 in sample:
        t2 = w2.get_tile(t1.x, t1.y, t1.z)
        assert t2 is not None
        assert t1.ground == t2.ground
    print("  [OK] test_generate_continent_deterministic_with_seed")


def test_generate_continent_different_seeds_differ():
    """Different seeds should produce different worlds."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts level 200 and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    w1 = generate_continent(plan, seed=1)
    w2 = generate_continent(plan, seed=2)
    diffs = sum(1 for k in w1.tiles if w1.tiles[k].ground != w2.tiles.get(k).ground)
    assert diffs > 0
    print("  [OK] test_generate_continent_different_seeds_differ")


def test_generate_continent_supports_full_example():
    """The canonical example from the task spec must work."""
    architect = AIArchitect()
    plan = architect.plan(
        "Genera una ciudad estilo Issavi con 3 hunts nivel 200-400 y un boss final",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    assert plan.primary_theme == "issavi"
    world = generate_continent(plan, seed=42)
    assert isinstance(world, WorldModel)
    assert len(plan.cities) == 1
    assert len(plan.hunting_zones) == 3
    assert len(plan.boss_zones) == 1
    assert world.structure_count() >= 4
    print("  [OK] test_generate_continent_supports_full_example")


def test_generate_continent_uses_plan_layout():
    """Zones from the plan's layout should be visible in the result."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts level 200 and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    world = generate_continent(plan, seed=42)
    layout = plan.layout
    if layout is not None and layout.zones:
        assert world.structure_count() >= len(layout.zones)
    print("  [OK] test_generate_continent_uses_plan_layout")


def test_generate_continent_integration_with_ai_architect():
    """End-to-end: AIArchitect -> plan -> continent -> WorldModel."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    cg = ContinentGenerator(
        seed=42,
        theme_resolver=architect.theme_resolver,
    )
    world = cg.generate(plan)
    assert world.tile_count() > 0
    assert world.structure_count() >= 1
    print("  [OK] test_generate_continent_integration_with_ai_architect")


def test_generate_continent_works_without_layout():
    """A plan with no layout should still produce a continent."""
    plan = {
        "prompt": "test",
        "themes": ["issavi"],
        "primary_theme": "issavi",
        "world_width": TEST_W,
        "world_height": TEST_H,
        "layout": None,
    }
    world = generate_continent(plan, seed=42)
    assert isinstance(world, WorldModel)
    assert world.tile_count() >= TEST_W * TEST_H
    print("  [OK] test_generate_continent_works_without_layout")


def test_generate_continent_supports_dict_plan():
    """The generator should accept a plain dict as the plan."""
    plan = {
        "prompt": "Test dict plan",
        "themes": ["issavi"],
        "primary_theme": "issavi",
        "level_min": 200,
        "level_max": 400,
        "world_width": TEST_W,
        "world_height": TEST_H,
        "layout": None,
    }
    world = generate_continent(plan, seed=42)
    assert isinstance(world, WorldModel)
    assert world.tile_count() > 0
    print("  [OK] test_generate_continent_supports_dict_plan")


def test_generate_from_prompt_end_to_end():
    """generate_from_prompt should run the full pipeline."""
    world = generate_from_prompt(
        "Generate Issavi city with 1 hunt level 200 and a boss",
        seed=42,
        world_width=TEST_W,
        world_height=TEST_H,
    )
    assert isinstance(world, WorldModel)
    assert world.tile_count() > 0
    print("  [OK] test_generate_from_prompt_end_to_end")


def test_continent_result_dataclass():
    """ContinentResult should expose the expected properties."""
    res = ContinentResult(world=WorldModel())
    res.zones_placed = [{"x": 1, "y": 2}]
    res.structures.append(
        Structure(
            name="s", category="c", x=0, y=0, z=7, width=5, height=5, tile_count=25
        )
    )
    assert res.total_tiles == 0
    assert res.total_zones == 1
    assert res.total_structures == 1
    assert res.total_spawns == 0
    d = res.to_dict()
    assert d["total_zones"] == 1
    assert d["total_structures"] == 1
    print("  [OK] test_continent_result_dataclass")


def test_continent_result_includes_roads_and_rivers():
    """ContinentResult should report roads and rivers as well."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    cg = ContinentGenerator(seed=42)
    world = cg.generate(plan)
    res = ContinentResult(
        world=world,
        zones_placed=[],
        roads=[],
        rivers=[],
        terrain_features=[],
        structures=list(world.structures),
        regions=list(world.regions),
    )
    d = res.to_dict()
    assert "roads" in d
    assert "rivers" in d
    assert "structures" in d
    assert "regions" in d
    assert "terrain_features" in d
    assert "metadata" in d
    print("  [OK] test_continent_result_includes_roads_and_rivers")


def test_world_validator_passes_on_continent():
    """The synthesized world should pass the WorldValidator."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 1 hunt and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    world = generate_continent(plan, seed=42)
    validator = WorldValidator()
    result = validator.validate(world)
    assert len(result.errors) == 0, result.summary()
    print("  [OK] test_world_validator_passes_on_continent")


def test_continent_generator_seed_persistence():
    """The seed should be stored on the generator."""
    g = ContinentGenerator(seed=1234)
    assert g._seed == 1234
    print("  [OK] test_continent_generator_seed_persistence")


def test_continent_generator_dependencies_injection():
    """The generator should accept custom sub-generators."""
    from core.procedural import (
        BiomeGenerator,
        TerrainGenerator,
        RoadGenerator,
        RiverGenerator,
    )

    bg = BiomeGenerator(seed=1)
    tg = TerrainGenerator(seed=2)
    rg = RoadGenerator(seed=3)
    rivg = RiverGenerator(seed=4)
    cg = ContinentGenerator(
        biome_generator=bg,
        terrain_generator=tg,
        road_generator=rg,
        river_generator=rivg,
        seed=42,
    )
    assert cg._biome is bg
    assert cg._terrain is tg
    assert cg._roads is rg
    assert cg._rivers is rivg
    print("  [OK] test_continent_generator_dependencies_injection")


def test_continent_generator_themes_resolved():
    """The generator should resolve all themes from the plan."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi + Roshamuul with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    cg = ContinentGenerator(seed=42, theme_resolver=architect.theme_resolver)
    world = cg.generate(plan)
    assert isinstance(world, WorldModel)
    assert cg._resolve_all_themes(plan, "issavi") != {}
    print("  [OK] test_continent_generator_themes_resolved")


def test_continent_handles_empty_plan():
    """A plan with no zones should still produce a world (just biome)."""
    empty_plan = {
        "prompt": "empty",
        "themes": ["generic"],
        "primary_theme": "generic",
        "world_width": TEST_W,
        "world_height": TEST_H,
        "layout": None,
    }
    world = generate_continent(empty_plan, seed=42)
    assert world.tile_count() > 0
    print("  [OK] test_continent_handles_empty_plan")


# =============================================================================
# Runner
# =============================================================================


def run_all():
    tests = [
        test_continent_generator_creation,
        test_continent_generator_creation_with_seed,
        test_generate_continent_accepts_worldplan,
        test_generate_continent_world_has_tiles,
        test_generate_continent_world_has_structures,
        test_generate_continent_world_has_regions,
        test_generate_continent_world_has_spawns,
        test_generate_continent_world_has_roads,
        test_generate_continent_deterministic_with_seed,
        test_generate_continent_different_seeds_differ,
        test_generate_continent_supports_full_example,
        test_generate_continent_uses_plan_layout,
        test_generate_continent_integration_with_ai_architect,
        test_generate_continent_works_without_layout,
        test_generate_continent_supports_dict_plan,
        test_generate_from_prompt_end_to_end,
        test_continent_result_dataclass,
        test_continent_result_includes_roads_and_rivers,
        test_world_validator_passes_on_continent,
        test_continent_generator_seed_persistence,
        test_continent_generator_dependencies_injection,
        test_continent_generator_themes_resolved,
        test_continent_handles_empty_plan,
    ]
    print("=" * 60)
    print("  HITO 16 - CONTINENT GENERATOR - TESTS")
    print("=" * 60)
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            import traceback

            tb = traceback.format_exc()
            failures.append((t.__name__, f"{type(e).__name__}: {e}\n{tb}"))
            print(f"  [FAIL] {t.__name__}: {type(e).__name__}: {e}")

    print("=" * 60)
    print(f"  Results: {len(tests) - len(failures)}/{len(tests)} tests passed")
    if failures:
        print("  Failures:")
        for name, err in failures:
            print(f"    - {name}")
            for line in err.split("\n")[:5]:
                print(f"        {line}")
    else:
        print("  ALL TESTS PASSED")
    print("=" * 60)
    return len(failures) == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
