"""
Tests for HuntGenerator — the first fully functional generator.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.generators import HuntGenerator
from core.world import WorldModel, WorldValidator


def test_hunt_generator_basic():
    """Test that HuntGenerator produces a WorldModel with tiles."""
    hg = HuntGenerator(seed=42)
    world = hg.generate(WorldModel(), {
        "theme": "issavi",
        "level_min": 300,
        "level_max": 500,
    })
    assert len(world.tiles) > 0, f"Expected > 0 tiles, got {len(world.tiles)}"
    assert world.tile_count() > 0
    assert world.region_count() == 1
    assert world.structure_count() == 1


def test_hunt_generator_theme_resolution():
    """Test that different themes produce different ground tiles."""
    hg = HuntGenerator(seed=42)
    world_issavi = hg.generate(WorldModel(), {
        "theme": "issavi",
        "level_min": 100,
        "level_max": 200,
    })
    issavi_grounds = set()
    for tile in world_issavi.tiles.values():
        if tile.ground is not None:
            issavi_grounds.add(tile.ground)

    hg2 = HuntGenerator(seed=42)
    world_roshamuul = hg2.generate(WorldModel(), {
        "theme": "roshamuul",
        "level_min": 100,
        "level_max": 200,
    })
    roshamuul_grounds = set()
    for tile in world_roshamuul.tiles.values():
        if tile.ground is not None:
            roshamuul_grounds.add(tile.ground)

    # Themes should have different ground IDs
    assert issavi_grounds != roshamuul_grounds


def test_hunt_generator_spawns():
    """Test that spawns are placed on some tiles."""
    hg = HuntGenerator(seed=42)
    world = hg.generate(WorldModel(), {
        "theme": "issavi",
        "level_min": 300,
        "level_max": 500,
        "density": "high",
    })
    spawn_count = sum(1 for t in world.tiles.values() if t.spawn is not None)
    assert spawn_count > 0, f"Expected spawns, got {spawn_count}"


def test_hunt_generator_dimensions():
    """Test custom dimensions."""
    hg = HuntGenerator(seed=42)
    world = hg.generate(WorldModel(), {
        "theme": "issavi",
        "level_min": 100,
        "level_max": 200,
        "width": 25,
        "height": 25,
    })
    # 25x25 = 625 tiles
    assert world.tile_count() >= 625, f"Expected >= 625 tiles, got {world.tile_count()}"


def test_hunt_generator_default_world():
    """Test that WorldModel is created when not provided."""
    hg = HuntGenerator(seed=42)
    world = hg.generate(context={
        "theme": "issavi",
        "level_min": 100,
        "level_max": 200,
    })
    assert world is not None
    assert world.tile_count() > 0


def test_hunt_generator_validation():
    """Test that generated world passes basic validation."""
    hg = HuntGenerator(seed=42)
    world = hg.generate(WorldModel(), {
        "theme": "issavi",
        "level_min": 300,
        "level_max": 500,
    })

    validator = WorldValidator()
    result = validator.validate(world)
    # Should pass (no errors)
    assert result.passed, f"Validation failed: {result.summary()}"


def test_hunt_generator_roshamuul():
    """Test Roshamuul hunt generation."""
    hg = HuntGenerator(seed=42)
    world = hg.generate(WorldModel(), {
        "theme": "roshamuul",
        "level_min": 400,
        "level_max": 600,
    })
    assert len(world.tiles) > 0
    assert world.region_count() == 1
    # Check that region has correct theme
    region = world.regions[0]
    assert region.theme == "roshamuul"
    assert region.min_level == 400
    assert region.max_level == 600


if __name__ == "__main__":
    test_hunt_generator_basic()
    test_hunt_generator_theme_resolution()
    test_hunt_generator_spawns()
    test_hunt_generator_dimensions()
    test_hunt_generator_default_world()
    test_hunt_generator_validation()
    test_hunt_generator_roshamuul()
    print("All hunt_generator tests passed!")