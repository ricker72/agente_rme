"""
Tests for WorldGenerator — the main orchestrator.

This is the most important test: it validates the full pipeline from
prompt string to validated WorldModel.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.generators import WorldGenerator
from core.world import WorldModel, WorldValidator


def test_world_generator_basic_prompt():
    """Test that WorldGenerator accepts a string prompt and produces tiles.

    This is the mandatory test from the spec:
        generator = WorldGenerator()
        world = generator.generate("Generate Issavi hunt level 300")
        print(len(world.tiles))
        Result: 1250 or any positive amount of tiles
    """
    generator = WorldGenerator(seed=42)
    world = generator.generate("Generate Issavi hunt level 300")
    assert len(world.tiles) > 0, f"Expected > 0 tiles, got {len(world.tiles)}"
    assert world.tile_count() > 0
    # Check region was created
    assert world.region_count() == 1


def test_world_generator_hunt_config():
    """Test with structured config dict for hunt."""
    generator = WorldGenerator(seed=42)
    world = generator.generate({
        "type": "hunt",
        "theme": "issavi",
        "level_min": 300,
        "level_max": 500,
    })
    assert world.tile_count() > 0
    assert world.region_count() == 1


def test_world_generator_city_config():
    """Test with structured config dict for city."""
    generator = WorldGenerator(seed=42)
    world = generator.generate({
        "type": "city",
        "theme": "issavi",
        "level_min": 50,
        "level_max": 200,
    })
    assert world.tile_count() > 0
    assert world.region_count() == 1


def test_world_generator_dungeon_config():
    """Test with structured config dict for dungeon."""
    generator = WorldGenerator(seed=42)
    world = generator.generate({
        "type": "dungeon",
        "theme": "library",
        "level_min": 200,
        "level_max": 400,
    })
    assert world.tile_count() > 0
    assert world.region_count() == 1


def test_world_generator_theme_detection():
    """Test theme detection from prompt."""
    generator = WorldGenerator(seed=42)

    world = generator.generate("Generate Issavi hunt level 300")
    region = world.regions[0]
    assert region.theme == "issavi", f"Expected 'issavi', got '{region.theme}'"


def test_world_generator_prompt_city():
    """Test city detection from prompt."""
    generator = WorldGenerator(seed=42)
    world = generator.generate("Generate a city in issavi theme")
    assert world.tile_count() > 0


def test_world_generator_prompt_dungeon():
    """Test dungeon detection from prompt."""
    generator = WorldGenerator(seed=42)
    world = generator.generate("Generate a dungeon in library theme")
    assert world.tile_count() > 0


def test_world_generator_validation():
    """Test that generated world passes basic WorldValidator."""
    generator = WorldGenerator(seed=42)
    world = generator.generate("Generate Issavi hunt level 300")

    validator = WorldValidator()
    result = validator.validate(world)
    assert result.passed, f"Validation failed: {result.summary()}"


def test_world_generator_multiple_calls():
    """Test that multiple generations work correctly."""
    generator = WorldGenerator(seed=42)

    world1 = generator.generate("Generate Issavi hunt level 300")
    assert world1.tile_count() > 0

    world2 = generator.generate("Generate Roshamuul dungeon level 400")
    assert world2.tile_count() > 0

    # Worlds should be independent
    assert world1 is not world2


def test_world_generator_existing_world():
    """Test passing an existing WorldModel."""
    generator = WorldGenerator(seed=42)
    existing = WorldModel()
    world = generator.generate(existing, {
        "type": "hunt",
        "theme": "issavi",
    })
    assert world is existing  # Same instance
    assert world.tile_count() > 0


if __name__ == "__main__":
    test_world_generator_basic_prompt()
    test_world_generator_hunt_config()
    test_world_generator_city_config()
    test_world_generator_dungeon_config()
    test_world_generator_theme_detection()
    test_world_generator_prompt_city()
    test_world_generator_prompt_dungeon()
    test_world_generator_validation()
    test_world_generator_multiple_calls()
    test_world_generator_existing_world()
    print("All world_generator tests passed!")