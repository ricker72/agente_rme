"""
Tests for DungeonGenerator.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.generators import DungeonGenerator
from core.world import WorldModel, WorldValidator


def test_dungeon_generator_basic():
    """Test that DungeonGenerator produces a WorldModel with tiles."""
    dg = DungeonGenerator(seed=42)
    world = dg.generate(
        WorldModel(),
        {
            "theme": "library",
            "level_min": 200,
            "level_max": 400,
        },
    )
    assert len(world.tiles) > 0, f"Expected > 0 tiles, got {len(world.tiles)}"
    assert world.tile_count() > 0
    assert world.region_count() == 1


def test_dungeon_generator_structures():
    """Test that dungeon contains expected structures."""
    dg = DungeonGenerator(seed=42)
    world = dg.generate(
        WorldModel(),
        {
            "theme": "library",
            "level_min": 200,
            "level_max": 400,
        },
    )
    # Should have entrance, boss_room, exit, and rooms
    all_structures = world.structures
    names = [s.name for s in all_structures]
    assert "entrance" in names, f"Expected 'entrance' in {names}"
    assert "boss_room" in names, f"Expected 'boss_room' in {names}"
    assert "exit" in names, f"Expected 'exit' in {names}"


def test_dungeon_generator_boss_spawn():
    """Test that the boss room has a boss spawn."""
    dg = DungeonGenerator(seed=42)
    world = dg.generate(
        WorldModel(),
        {
            "theme": "library",
            "level_min": 200,
            "level_max": 400,
        },
    )
    # Check for boss spawns (respawn >= 120)
    boss_spawns = [
        t
        for t in world.tiles.values()
        if t.spawn is not None and t.spawn.respawn >= 120
    ]
    assert len(boss_spawns) > 0, "Expected at least one boss spawn"


def test_dungeon_generator_different_themes():
    """Test dungeon generation with different themes."""
    dg = DungeonGenerator(seed=42)

    world_library = dg.generate(
        WorldModel(),
        {
            "theme": "library",
        },
    )
    assert world_library.tile_count() > 0

    dg2 = DungeonGenerator(seed=42)
    world_issavi = dg2.generate(
        WorldModel(),
        {
            "theme": "issavi",
        },
    )
    assert world_issavi.tile_count() > 0


def test_dungeon_generator_rooms():
    """Test that dungeon generates rooms."""
    dg = DungeonGenerator(seed=42)
    world = dg.generate(
        WorldModel(),
        {
            "theme": "library",
            "num_rooms": 4,
        },
    )
    dungeon_rooms = world.get_structures_by_category("dungeon_room")
    assert len(dungeon_rooms) > 0, f"Expected rooms, got {len(dungeon_rooms)}"


def test_dungeon_generator_validation():
    """Test that generated dungeon passes basic validation."""
    dg = DungeonGenerator(seed=42)
    world = dg.generate(
        WorldModel(),
        {
            "theme": "library",
            "level_min": 200,
            "level_max": 400,
        },
    )

    validator = WorldValidator()
    result = validator.validate(world)
    assert result.passed, f"Validation failed: {result.summary()}"


if __name__ == "__main__":
    test_dungeon_generator_basic()
    test_dungeon_generator_structures()
    test_dungeon_generator_boss_spawn()
    test_dungeon_generator_different_themes()
    test_dungeon_generator_rooms()
    test_dungeon_generator_validation()
    print("All dungeon_generator tests passed!")
