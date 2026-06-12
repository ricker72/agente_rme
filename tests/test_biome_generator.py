"""
HITO 16 - Procedural World Generation: Biome Generator tests
============================================================

Verifies the biome generator's behaviour:
    - It writes the expected number of tiles
    - It respects the theme palette
    - It honours primary_tag overrides
    - It is deterministic for the same seed
    - get_biome_palette handles both ThemeAssets and theme-name strings
    - The data classes serialize cleanly
    - It does NOT overwrite existing tiles unless asked to
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make sure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.world import WorldModel, Tile
from core.procedural.biome_generator import (
    BiomeGenerator,
    BiomeTile,
    generate_biome,
    generate_continental_biome,
    generate_zone_biome,
    get_biome_palette,
    pick_ground_for_tag,
    pick_primary_tag,
    BIOME_PALETTES,
    BIOME_TAG_BY_THEME,
    biome_generator_lua,
)

# =============================================================================
# Test data
# =============================================================================


class FakeTheme:
    """A minimal stand-in for ThemeAssets for tests."""

    def __init__(self, name="issavi", biome="desert", **extras):
        self.name = name
        self.metadata = {"biome": biome}
        for k, v in extras.items():
            setattr(self, k, v)


# =============================================================================
# Tests
# =============================================================================


def test_biome_palette_known_theme():
    """A known theme should return its palette."""
    palette = get_biome_palette("issavi")
    assert "grass" in palette
    assert "sand" in palette
    assert "water" in palette
    assert len(palette["sand"]) > 0
    print("  [OK] test_biome_palette_known_theme")


def test_biome_palette_unknown_theme_falls_back_to_generic():
    """An unknown theme should return the generic palette."""
    palette = get_biome_palette("does_not_exist_xxx")
    assert palette == get_biome_palette("generic")
    print("  [OK] test_biome_palette_unknown_theme_falls_back_to_generic")


def test_biome_palette_accepts_theme_assets():
    """Palette should accept a ThemeAssets-like object."""
    theme = FakeTheme(name="issavi", biome="desert")
    palette = get_biome_palette(theme)
    assert palette == get_biome_palette("issavi")
    print("  [OK] test_biome_palette_accepts_theme_assets")


def test_pick_primary_tag_from_theme_metadata():
    """pick_primary_tag should inspect the theme's biome metadata."""
    desert = FakeTheme(biome="desert")
    snow = FakeTheme(biome="arctic")
    jungle = FakeTheme(biome="tropical")
    assert pick_primary_tag(desert) == "sand"
    assert pick_primary_tag(snow) == "snow"
    assert pick_primary_tag(jungle) == "grass"
    print("  [OK] test_pick_primary_tag_from_theme_metadata")


def test_pick_ground_for_tag_rotates():
    """The salt parameter should rotate through palette options."""
    palette = get_biome_palette("issavi")
    g0 = pick_ground_for_tag(palette, "sand", 0)
    g1 = pick_ground_for_tag(palette, "sand", 1)
    g2 = pick_ground_for_tag(palette, "sand", 2)
    # Different salts should generally yield different IDs (palette has 3)
    assert g0 in palette["sand"]
    assert g1 in palette["sand"]
    assert g2 in palette["sand"]
    # At least one rotation must differ
    assert len({g0, g1, g2}) > 1
    print("  [OK] test_pick_ground_for_tag_rotates")


def test_biome_generator_basic_count():
    """The generator should write tiles for the whole rectangle."""
    world = WorldModel()
    gen = BiomeGenerator(seed=42)
    count = gen.generate(world, 0, 0, 19, 19, 7, "issavi")
    assert count == 20 * 20
    assert world.tile_count() == 400
    print("  [OK] test_biome_generator_basic_count")


def test_biome_generator_deterministic_with_seed():
    """The same seed should produce the same world."""
    w1 = WorldModel()
    w2 = WorldModel()
    BiomeGenerator(seed=99).generate(w1, 0, 0, 19, 19, 7, "issavi")
    BiomeGenerator(seed=99).generate(w2, 0, 0, 19, 19, 7, "issavi")
    assert w1.tile_count() == w2.tile_count()
    for key, t1 in w1.tiles.items():
        t2 = w2.tiles.get(key)
        assert t2 is not None
        assert t1.ground == t2.ground
    print("  [OK] test_biome_generator_deterministic_with_seed")


def test_biome_generator_different_seeds_differ():
    """Different seeds should produce different worlds (with high probability)."""
    w1 = WorldModel()
    w2 = WorldModel()
    BiomeGenerator(seed=1).generate(w1, 0, 0, 19, 19, 7, "issavi")
    BiomeGenerator(seed=2).generate(w2, 0, 0, 19, 19, 7, "issavi")
    # Compare ground IDs - at least some should differ
    diffs = sum(1 for k in w1.tiles if w1.tiles[k].ground != w2.tiles.get(k).ground)
    assert diffs > 0
    print("  [OK] test_biome_generator_different_seeds_differ")


def test_biome_generator_does_not_overwrite_by_default():
    """Without overwrite, existing tiles should be preserved."""
    world = WorldModel()
    world.set_tile(Tile(x=5, y=5, z=7, ground=9999))
    gen = BiomeGenerator(seed=42)
    gen.generate(world, 0, 0, 9, 9, 7, "issavi")
    # The pre-existing tile should be unchanged
    assert world.get_tile(5, 5, 7).ground == 9999
    print("  [OK] test_biome_generator_does_not_overwrite_by_default")


def test_biome_generator_overwrite_when_asked():
    """With overwrite=True, the generator should replace existing tiles."""
    world = WorldModel()
    world.set_tile(Tile(x=5, y=5, z=7, ground=9999))
    gen = BiomeGenerator(
        seed=42,
    )
    gen.generate(world, 0, 0, 9, 9, 7, "issavi", overwrite=True)
    # The pre-existing tile should now have a biome ground
    new_ground = world.get_tile(5, 5, 7).ground
    assert new_ground != 9999
    print("  [OK] test_biome_generator_overwrite_when_asked")


def test_biome_generator_uses_primary_tag():
    """Passing primary_tag should drive the surface choice."""
    world = WorldModel()
    gen = BiomeGenerator(seed=42)
    gen.generate(world, 0, 0, 9, 9, 7, "issavi", primary_tag="sand", water_chance=0.0)
    # We should have at least some sand tiles
    ground_ids = {t.ground for t in world.tiles.values()}
    palette = get_biome_palette("issavi")
    sand_set = set(palette["sand"])
    assert ground_ids & sand_set
    print("  [OK] test_biome_generator_uses_primary_tag")


def test_biome_generator_water_chance():
    """Increasing water_chance should produce water tiles."""
    world = WorldModel()
    gen = BiomeGenerator(seed=1)
    gen.generate(world, 0, 0, 99, 99, 7, "issavi", water_chance=0.5)
    palette = get_biome_palette("issavi")
    water_set = set(palette["water"])
    water_tiles = sum(1 for t in world.tiles.values() if t.ground in water_set)
    assert water_tiles > 0
    print("  [OK] test_biome_generator_water_chance")


def test_biome_generator_normalizes_bounds():
    """The generator should swap bounds if x2 < x1 or y2 < y1."""
    world = WorldModel()
    gen = BiomeGenerator(seed=42)
    count = gen.generate(world, 9, 9, 0, 0, 7, "issavi")
    assert count == 100  # (9-0+1) * (9-0+1)
    print("  [OK] test_biome_generator_normalizes_bounds")


def test_biome_generator_sets_zone_tag():
    """Every generated tile should carry a 'biome:' zone tag."""
    world = WorldModel()
    gen = BiomeGenerator(seed=42)
    gen.generate(world, 0, 0, 9, 9, 7, "issavi")
    for t in world.tiles.values():
        assert t.zone is not None
        assert t.zone.startswith("biome:")
    print("  [OK] test_biome_generator_sets_zone_tag")


def test_module_level_generate_biome():
    """generate_biome should work as a one-shot helper."""
    world = WorldModel()
    n = generate_biome(world, 0, 0, 9, 9, 7, "issavi", seed=42)
    assert n == 100
    assert world.tile_count() == 100
    print("  [OK] test_module_level_generate_biome")


def test_module_level_generate_continental_biome():
    """generate_continental_biome should fill a world-sized area."""
    world = WorldModel()
    n = generate_continental_biome(world, 50, 50, 7, "jungle", seed=42)
    # inclusive bounds: (0..50, 0..50) = 51 * 51 = 2601
    assert n == 51 * 51
    print("  [OK] test_module_level_generate_continental_biome")


def test_module_level_generate_zone_biome():
    """generate_zone_biome should fill a (x,y,w,h) area."""
    world = WorldModel()
    n = generate_zone_biome(world, 10, 10, 20, 20, 7, "ice", seed=42)
    assert n == 20 * 20
    # All tiles should be in the requested rectangle
    for t in world.tiles.values():
        assert 10 <= t.x <= 29
        assert 10 <= t.y <= 29
    print("  [OK] test_module_level_generate_zone_biome")


def test_biome_palettes_dict_has_all_themes():
    """BIOME_PALETTES should contain at least the standard themes."""
    for name in (
        "generic",
        "issavi",
        "roshamuul",
        "soul_war",
        "library",
        "yalahar",
        "falcon",
        "cobra",
        "ice",
        "jungle",
        "thais",
        "venore",
        "ankrahmun",
    ):
        assert name in BIOME_PALETTES
        assert "grass" in BIOME_PALETTES[name]
        assert "water" in BIOME_PALETTES[name]
    print("  [OK] test_biome_palettes_dict_has_all_themes")


def test_biome_tag_by_theme_covers_known_biomes():
    """BIOME_TAG_BY_THEME should map every well-known biome."""
    for biome in (
        "desert",
        "arctic",
        "tropical",
        "temperate",
        "nightmare",
        "nether",
        "arcane",
        "swamp",
        "mountain",
    ):
        assert biome in BIOME_TAG_BY_THEME
    print("  [OK] test_biome_tag_by_theme_covers_known_biomes")


def test_biome_tile_dataclass_serializes():
    """BiomeTile should round-trip via to_dict."""
    bt = BiomeTile(x=1, y=2, z=7, ground=415, tag="grass")
    d = bt.to_dict()
    assert d["x"] == 1 and d["y"] == 2 and d["z"] == 7
    assert d["ground"] == 415
    assert d["tag"] == "grass"
    print("  [OK] test_biome_tile_dataclass_serializes")


def test_legacy_biome_generator_lua_returns_string():
    """The legacy lua alias should still work."""
    s = biome_generator_lua("ice", 0, 0, 10, 10, 7)
    assert isinstance(s, str)
    assert "app.transaction" in s
    assert "7" in s
    print("  [OK] test_legacy_biome_generator_lua_returns_string")


def test_biome_generator_threshold_alignment():
    """The biome generator should still work for a 1x1 rectangle."""
    world = WorldModel()
    gen = BiomeGenerator(seed=42)
    count = gen.generate(world, 0, 0, 0, 0, 7, "issavi")
    assert count == 1
    assert world.tile_count() == 1
    print("  [OK] test_biome_generator_threshold_alignment")


# =============================================================================
# Runner
# =============================================================================


def run_all():
    tests = [
        test_biome_palette_known_theme,
        test_biome_palette_unknown_theme_falls_back_to_generic,
        test_biome_palette_accepts_theme_assets,
        test_pick_primary_tag_from_theme_metadata,
        test_pick_ground_for_tag_rotates,
        test_biome_generator_basic_count,
        test_biome_generator_deterministic_with_seed,
        test_biome_generator_different_seeds_differ,
        test_biome_generator_does_not_overwrite_by_default,
        test_biome_generator_overwrite_when_asked,
        test_biome_generator_uses_primary_tag,
        test_biome_generator_water_chance,
        test_biome_generator_normalizes_bounds,
        test_biome_generator_sets_zone_tag,
        test_module_level_generate_biome,
        test_module_level_generate_continental_biome,
        test_module_level_generate_zone_biome,
        test_biome_palettes_dict_has_all_themes,
        test_biome_tag_by_theme_covers_known_biomes,
        test_biome_tile_dataclass_serializes,
        test_legacy_biome_generator_lua_returns_string,
        test_biome_generator_threshold_alignment,
    ]
    print("=" * 60)
    print("  HITO 16 - BIOME GENERATOR - TESTS")
    print("=" * 60)
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, f"{type(e).__name__}: {e}"))
            print(f"  [FAIL] {t.__name__}: {type(e).__name__}: {e}")

    print("=" * 60)
    print(f"  Results: {len(tests) - len(failures)}/{len(tests)} tests passed")
    if failures:
        print("  Failures:")
        for name, err in failures:
            print(f"    - {name}: {err}")
    else:
        print("  ALL TESTS PASSED")
    print("=" * 60)
    return len(failures) == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
