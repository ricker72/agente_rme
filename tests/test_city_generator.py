"""
Tests for CityGenerator.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.generators import CityGenerator
from core.world import WorldModel, WorldValidator


def test_city_generator_basic():
    """Test that CityGenerator produces a WorldModel with tiles."""
    cg = CityGenerator(seed=42)
    world = cg.generate(
        WorldModel(),
        {
            "theme": "issavi",
            "level_min": 50,
            "level_max": 200,
        },
    )
    assert len(world.tiles) > 0, f"Expected > 0 tiles, got {len(world.tiles)}"
    assert world.tile_count() > 0
    assert world.region_count() == 1


def test_city_generator_structure():
    """Test that city contains a temple structure."""
    cg = CityGenerator(seed=42)
    world = cg.generate(
        WorldModel(),
        {
            "theme": "issavi",
            "level_min": 50,
            "level_max": 200,
        },
    )
    structures = world.get_structures_by_category("temple")
    assert len(structures) == 1, f"Expected 1 temple, got {len(structures)}"


def test_city_generator_buildings():
    """Test that city generates buildings."""
    cg = CityGenerator(seed=42)
    world = cg.generate(
        WorldModel(),
        {
            "theme": "issavi",
            "level_min": 50,
            "level_max": 200,
        },
    )
    buildings = world.get_structures_by_category("building")
    assert len(buildings) > 0, f"Expected buildings, got {len(buildings)}"


def test_city_generator_different_themes():
    """Test city generation with different themes."""
    cg = CityGenerator(seed=42)

    world_issavi = cg.generate(
        WorldModel(),
        {
            "theme": "issavi",
        },
    )
    assert world_issavi.tile_count() > 0

    cg2 = CityGenerator(seed=42)
    world_roshamuul = cg2.generate(
        WorldModel(),
        {
            "theme": "roshamuul",
        },
    )
    assert world_roshamuul.tile_count() > 0


def test_city_generator_custom_size():
    """Test custom city dimensions."""
    cg = CityGenerator(seed=42)
    world = cg.generate(
        WorldModel(),
        {
            "theme": "issavi",
            "width": 30,
            "height": 30,
        },
    )
    # At minimum, all tiles in the area should be covered
    assert world.tile_count() >= 900, f"Expected >= 900 tiles, got {world.tile_count()}"


def test_city_generator_validation():
    """Test that generated city passes basic validation."""
    cg = CityGenerator(seed=42)
    world = cg.generate(
        WorldModel(),
        {
            "theme": "issavi",
        },
    )

    validator = WorldValidator()
    result = validator.validate(world)
    assert result.passed, f"Validation failed: {result.summary()}"


if __name__ == "__main__":
    test_city_generator_basic()
    test_city_generator_structure()
    test_city_generator_buildings()
    test_city_generator_different_themes()
    test_city_generator_custom_size()
    test_city_generator_validation()
    print("All city_generator tests passed!")
