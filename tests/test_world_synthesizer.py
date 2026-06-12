"""
HITO 16 - Procedural World Generation: World Synthesizer tests
=============================================================

Verifies that the WorldSynthesizer:
    - accepts a WorldPlan and returns a WorldModel
    - accepts a ContinentResult
    - merges multiple WorldModels
    - normalizes tiles
    - attaches AIArchitect and BlueprintRegistry references
    - runs validation
    - produces a SynthesisReport with all expected fields
    - is reproducible given a seed
    - integrates with the full pipeline (prompt -> world)

NOTE: Tests use small world sizes (60x60) to keep runtime fast.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.world import WorldModel, Tile, Structure, Region
from core.world import WorldValidationResult
from core.architect import AIArchitect
from core.procedural import (
    WorldSynthesizer,
    SynthesisReport,
    ContinentResult,
    synthesize,
    merge,
    validate_synthesis,
    attach_ai_architect,
    attach_blueprint_registry,
    generate_from_prompt,
)

# Test world size - keeps tests fast
TEST_W = 60
TEST_H = 60


# =============================================================================
# Tests
# =============================================================================


def test_synthesizer_creation():
    """WorldSynthesizer should be instantiable with no args."""
    s = WorldSynthesizer(seed=42)
    assert s is not None
    print("  [OK] test_synthesizer_creation")


def test_synthesizer_creation_with_seed():
    """A specific seed should be honoured."""
    s = WorldSynthesizer(seed=1234)
    assert s is not None
    print("  [OK] test_synthesizer_creation_with_seed")


def test_synthesize_accepts_plan():
    """synthesize should accept a WorldPlan and return a WorldModel."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    world = synthesize(plan, seed=42)
    assert isinstance(world, WorldModel)
    assert world.tile_count() > 0
    print("  [OK] test_synthesize_accepts_plan")


def test_synthesize_accepts_continent_result():
    """synthesize should accept a ContinentResult."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    from core.procedural import ContinentGenerator

    cg = ContinentGenerator(seed=42, theme_resolver=architect.theme_resolver)
    world = cg.generate(plan)
    result = ContinentResult(
        world=world,
        zones_placed=[],
        metadata={"prompt": "test"},
    )
    out = synthesize(result, seed=42)
    assert isinstance(out, WorldModel)
    assert out.tile_count() == world.tile_count()
    print("  [OK] test_synthesize_accepts_continent_result")


def test_synthesize_creates_report():
    """synthesize should populate the synthesizer's last_report."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    synth = WorldSynthesizer(seed=42)
    synth.synthesize(plan)
    assert synth.last_report is not None
    report = synth.last_report
    assert isinstance(report, SynthesisReport)
    assert report.total_tiles > 0
    print("  [OK] test_synthesize_creates_report")


def test_synthesize_report_includes_all_fields():
    """The SynthesisReport should include all the expected fields."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    synth = WorldSynthesizer(seed=42)
    synth.synthesize(plan)
    r = synth.last_report
    d = r.to_dict()
    expected_keys = {
        "total_tiles",
        "total_structures",
        "total_spawns",
        "total_regions",
        "total_chunks",
        "themes_used",
        "ai_architect_attached",
        "blueprint_registry_attached",
        "validation",
        "metadata",
    }
    assert expected_keys.issubset(set(d.keys()))
    print("  [OK] test_synthesize_report_includes_all_fields")


def test_synthesize_attaches_ai_architect():
    """synthesize should attach an AIArchitect when passed one."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    synth = WorldSynthesizer(seed=42)
    world = synth.synthesize(plan, ai_architect=architect)
    assert hasattr(world, "_ai_architect")
    assert world._ai_architect is architect
    assert synth.last_report.ai_architect_attached is True
    print("  [OK] test_synthesize_attaches_ai_architect")


def test_synthesize_attaches_blueprint_registry():
    """synthesize should attach a BlueprintRegistry when passed one."""
    from core.registry import BlueprintRegistry

    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    synth = WorldSynthesizer(seed=42)
    reg = BlueprintRegistry()
    world = synth.synthesize(plan, blueprint_registry=reg)
    assert hasattr(world, "_blueprint_registry")
    assert world._blueprint_registry is reg
    assert synth.last_report.blueprint_registry_attached is True
    print("  [OK] test_synthesize_attaches_blueprint_registry")


def test_synthesize_validates_by_default():
    """synthesize should validate the world by default."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    synth = WorldSynthesizer(seed=42, auto_validate=True)
    synth.synthesize(plan)
    assert synth.last_report.validation is not None
    assert isinstance(synth.last_report.validation, WorldValidationResult)
    print("  [OK] test_synthesize_validates_by_default")


def test_synthesize_validation_pass():
    """The synthesized world should pass validation."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    synth = WorldSynthesizer(seed=42)
    synth.synthesize(plan)
    r = synth.last_report.validation
    assert r.passed, r.summary()
    print("  [OK] test_synthesize_validation_pass")


def test_synthesize_deterministic_with_seed():
    """Two synth runs with the same seed should produce the same world."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    s1 = WorldSynthesizer(seed=99)
    s2 = WorldSynthesizer(seed=99)
    w1 = s1.synthesize(plan)
    w2 = s2.synthesize(plan)
    assert w1.tile_count() == w2.tile_count()
    sample = list(w1.tiles.values())[:50]
    for t1 in sample:
        t2 = w2.get_tile(t1.x, t1.y, t1.z)
        assert t2 is not None
        assert t1.ground == t2.ground
    print("  [OK] test_synthesize_deterministic_with_seed")


def test_synthesize_supports_auto_validate_false():
    """synthesize should respect auto_validate=False."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    synth = WorldSynthesizer(seed=42, auto_validate=False)
    synth.synthesize(plan)
    assert synth.last_report.validation is None
    print("  [OK] test_synthesize_supports_auto_validate_false")


def test_synthesize_with_dependencies_injection():
    """synthesize should use the injected ContinentGenerator."""
    from core.procedural import (
        ContinentGenerator,
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
    synth = WorldSynthesizer(continent_generator=cg)
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 1 hunt and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    world = synth.synthesize(plan)
    assert world.tile_count() > 0
    print("  [OK] test_synthesize_with_dependencies_injection")


def test_synthesizer_merge_empty():
    """merge() of an empty list should return a fresh WorldModel."""
    synth = WorldSynthesizer()
    world = synth.merge([])
    assert isinstance(world, WorldModel)
    assert world.tile_count() == 0
    print("  [OK] test_synthesizer_merge_empty")


def test_synthesizer_merge_single():
    """merge() of a single world should return that world normalized."""
    synth = WorldSynthesizer()
    w = WorldModel()
    w.set_tile(Tile(x=5, y=5, z=7, ground=415))
    out = synth.merge([w])
    assert out.tile_count() == 1
    assert out.get_tile(5, 5, 7).ground == 415
    print("  [OK] test_synthesizer_merge_single")


def test_synthesizer_merge_multiple():
    """merge() of multiple worlds should combine all tiles."""
    synth = WorldSynthesizer()
    w1 = WorldModel()
    w1.set_tile(Tile(x=1, y=1, z=7, ground=100))
    w2 = WorldModel()
    w2.set_tile(Tile(x=2, y=2, z=7, ground=200))
    w3 = WorldModel()
    w3.set_tile(Tile(x=3, y=3, z=7, ground=300))
    out = synth.merge([w1, w2, w3])
    assert out.tile_count() == 3
    assert out.get_tile(1, 1, 7).ground == 100
    assert out.get_tile(2, 2, 7).ground == 200
    assert out.get_tile(3, 3, 7).ground == 300
    print("  [OK] test_synthesizer_merge_multiple")


def test_synthesizer_merge_combines_structures():
    """merge() should combine structures from all worlds."""
    synth = WorldSynthesizer()
    w1 = WorldModel()
    w1.add_structure(
        Structure(
            name="s1",
            category="city",
            x=0,
            y=0,
            z=7,
            width=10,
            height=10,
            tile_count=100,
        )
    )
    w2 = WorldModel()
    w2.add_structure(
        Structure(
            name="s2",
            category="hunt_zone",
            x=20,
            y=20,
            z=7,
            width=10,
            height=10,
            tile_count=100,
        )
    )
    out = synth.merge([w1, w2])
    assert out.structure_count() == 2
    names = {s.name for s in out.structures}
    assert "s1" in names
    assert "s2" in names
    print("  [OK] test_synthesizer_merge_combines_structures")


def test_synthesizer_merge_combines_regions():
    """merge() should combine regions from all worlds."""
    synth = WorldSynthesizer()
    w1 = WorldModel()
    w1.add_region(Region(name="r1", theme="issavi"))
    w2 = WorldModel()
    w2.add_region(Region(name="r2", theme="roshamuul"))
    out = synth.merge([w1, w2])
    assert out.region_count() == 2
    print("  [OK] test_synthesizer_merge_combines_regions")


def test_synthesizer_merge_normalizes_negative_coords():
    """merge() should remove tiles with negative coordinates."""
    synth = WorldSynthesizer()
    w = WorldModel()
    w.set_tile(Tile(x=-1, y=5, z=7, ground=100))
    w.set_tile(Tile(x=5, y=-1, z=7, ground=100))
    w.set_tile(Tile(x=5, y=5, z=7, ground=200))
    out = synth.merge([w])
    assert out.tile_count() == 1
    assert out.get_tile(5, 5, 7).ground == 200
    print("  [OK] test_synthesizer_merge_normalizes_negative_coords")


def test_synthesize_normalize():
    """synthesize should normalize invalid tiles (negative coords)."""
    from core.procedural import ContinentResult

    w = WorldModel()
    w.set_tile(Tile(x=-5, y=5, z=7, ground=100))
    w.set_tile(Tile(x=5, y=5, z=7, ground=200))
    result = ContinentResult(
        world=w,
        zones_placed=[],
        metadata={"prompt": "test"},
    )
    out = synthesize(result, seed=42)
    assert out.tile_count() == 1
    print("  [OK] test_synthesize_normalize")


def test_synthesis_report_to_dict():
    """SynthesisReport.to_dict() should produce a JSON-serializable dict."""
    import json

    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 1 hunt and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    synth = WorldSynthesizer(seed=42)
    synth.synthesize(plan)
    d = synth.last_report.to_dict()
    json.dumps(d, default=str)
    print("  [OK] test_synthesis_report_to_dict")


def test_synthesis_report_includes_themes():
    """The report should include the themes used."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi + Roshamuul with 1 hunt and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    synth = WorldSynthesizer(seed=42)
    synth.synthesize(plan)
    assert len(synth.last_report.themes_used) > 0
    print("  [OK] test_synthesis_report_includes_themes")


def test_module_level_synthesize():
    """The module-level synthesize() helper should work."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 1 hunt and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    world = synthesize(plan, seed=42)
    assert isinstance(world, WorldModel)
    print("  [OK] test_module_level_synthesize")


def test_module_level_merge():
    """The module-level merge() helper should work."""
    w1 = WorldModel()
    w1.set_tile(Tile(x=1, y=1, z=7, ground=100))
    w2 = WorldModel()
    w2.set_tile(Tile(x=2, y=2, z=7, ground=200))
    out = merge(w1, w2)
    assert out.tile_count() == 2
    print("  [OK] test_module_level_merge")


def test_module_level_validate_synthesis():
    """The module-level validate_synthesis() should work."""
    w = WorldModel()
    w.set_tile(Tile(x=5, y=5, z=7, ground=100))
    res = validate_synthesis(w)
    assert isinstance(res, WorldValidationResult)
    assert res.passed
    print("  [OK] test_module_level_validate_synthesis")


def test_module_level_attach_ai_architect():
    """attach_ai_architect() should attach the architect to the world."""
    architect = AIArchitect()
    w = WorldModel()
    attach_ai_architect(w, architect)
    assert w._ai_architect is architect
    print("  [OK] test_module_level_attach_ai_architect")


def test_module_level_attach_blueprint_registry():
    """attach_blueprint_registry() should attach the registry to the world."""
    from core.registry import BlueprintRegistry

    w = WorldModel()
    reg = BlueprintRegistry()
    attach_blueprint_registry(w, reg)
    assert w._blueprint_registry is reg
    print("  [OK] test_module_level_attach_blueprint_registry")


def test_synthesize_end_to_end_pipeline():
    """Full end-to-end pipeline: prompt -> world -> synthesizer."""
    architect = AIArchitect()
    plan = architect.plan(
        "Generate Issavi city with 2 hunts level 200 and a boss",
        world_width=TEST_W,
        world_height=TEST_H,
    )
    synth = WorldSynthesizer(seed=42)
    world = synth.synthesize(plan, ai_architect=architect)
    assert world.tile_count() > 0
    assert world.structure_count() >= 1
    assert world._ai_architect is architect
    print("  [OK] test_synthesize_end_to_end_pipeline")


def test_generate_then_synthesize():
    """generate_from_prompt + synthesize integration."""
    world = generate_from_prompt(
        "Generate Issavi city with 1 hunt level 200 and a boss",
        seed=42,
        world_width=TEST_W,
        world_height=TEST_H,
    )
    assert world.tile_count() > 0
    res = validate_synthesis(world)
    assert res.passed, res.summary()
    print("  [OK] test_generate_then_synthesize")


# =============================================================================
# Runner
# =============================================================================


def run_all():
    tests = [
        test_synthesizer_creation,
        test_synthesizer_creation_with_seed,
        test_synthesize_accepts_plan,
        test_synthesize_accepts_continent_result,
        test_synthesize_creates_report,
        test_synthesize_report_includes_all_fields,
        test_synthesize_attaches_ai_architect,
        test_synthesize_attaches_blueprint_registry,
        test_synthesize_validates_by_default,
        test_synthesize_validation_pass,
        test_synthesize_deterministic_with_seed,
        test_synthesize_supports_auto_validate_false,
        test_synthesize_with_dependencies_injection,
        test_synthesizer_merge_empty,
        test_synthesizer_merge_single,
        test_synthesizer_merge_multiple,
        test_synthesizer_merge_combines_structures,
        test_synthesizer_merge_combines_regions,
        test_synthesizer_merge_normalizes_negative_coords,
        test_synthesize_normalize,
        test_synthesis_report_to_dict,
        test_synthesis_report_includes_themes,
        test_module_level_synthesize,
        test_module_level_merge,
        test_module_level_validate_synthesis,
        test_module_level_attach_ai_architect,
        test_module_level_attach_blueprint_registry,
        test_synthesize_end_to_end_pipeline,
        test_generate_then_synthesize,
    ]
    print("=" * 60)
    print("  HITO 16 - WORLD SYNTHESIZER - TESTS")
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
