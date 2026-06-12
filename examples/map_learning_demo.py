"""
Map Learning AI Demo - Demonstrates the map learning capabilities.

This script shows how to use the LearningPipeline to:
1. Learn from existing maps
2. Find similar maps
3. Generate new blueprints from learned patterns
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.learning import (
    LearningPipeline,
)
from core.learning.learning_pipeline import LearningConfig


def demo_basic_learning():
    """Demonstrate basic learning pipeline usage."""
    print("=" * 60)
    print("MAP LEARNING AI DEMO")
    print("=" * 60)

    # Create learning configuration
    config = LearningConfig(
        maps_directory="templates",  # Use templates directory for demo
        dataset_path="data/demo_dataset.json",
        embeddings_path="data/demo_embeddings.json",
        style_profiles_path="data/demo_style_profiles.json",
        pattern_profiles_path="data/demo_pattern_profiles.json",
        similarity_index_path="data/demo_similarity_index.json",
        blueprints_path="data/demo_blueprints",
    )

    # Initialize pipeline
    pipeline = LearningPipeline(config)

    # Create sample dataset for demonstration
    print("\n1. Creating sample dataset...")
    sample_dataset = create_sample_dataset()

    # Train the pipeline
    print("\n2. Training learning pipeline...")
    metrics = pipeline.train(sample_dataset)
    print(f"   Training completed in {metrics.training_time_seconds:.2f} seconds")
    print(f"   Quality score: {metrics.quality_score:.2f}")
    print(f"   Regions processed: {metrics.regions_extracted}")
    print(f"   Styles learned: {metrics.styles_learned}")
    print(f"   Patterns learned: {metrics.patterns_learned}")

    return pipeline


def demo_similarity_search(pipeline: LearningPipeline):
    """Demonstrate similarity search capabilities."""
    print("\n" + "=" * 60)
    print("SIMILARITY SEARCH DEMO")
    print("=" * 60)

    # Query for similar maps
    print("\n3. Searching for maps similar to Roshamuul...")
    results = pipeline.find_similar("Find maps similar to Roshamuul", top_k=5)

    if results:
        for i, result in enumerate(results[:3], 1):
            print(f"   Result {i}: {result['matched_id']}")
            print(f"      Similarity: {result['similarity_score']:.2f}")
            print(f"      Style: {result['metadata'].get('style', 'unknown')}")
    else:
        print("   No results found (expected with sample data)")

    # Search by type
    print("\n4. Searching for dungeons...")
    results = pipeline.find_similar("Find dungeons", top_k=5)

    if results:
        for i, result in enumerate(results[:3], 1):
            print(f"   Result {i}: {result['matched_id']}")
    else:
        print("   No results found (expected with sample data)")


def demo_blueprint_generation(pipeline: LearningPipeline):
    """Demonstrate blueprint generation."""
    print("\n" + "=" * 60)
    print("BLUEPRINT GENERATION DEMO")
    print("=" * 60)

    # Generate blueprints
    print("\n5. Generating new map blueprints...")
    blueprints = pipeline.generate_blueprint(style="roshamuul", count=3)

    for i, blueprint in enumerate(blueprints, 1):
        print(f"\n   Blueprint {i}:")
        print(f"      ID: {blueprint.blueprint_id}")
        print(f"      Style: {blueprint.style}")
        print(f"      Type: {blueprint.region_type}")
        print(f"      Layout: {blueprint.layout_pattern}")
        print(f"      Rooms: {len(blueprint.rooms)}")
        print(f"      Corridors: {len(blueprint.corridors)}")
        print(f"      Features: {len(blueprint.features)}")


def demo_statistics(pipeline: LearningPipeline):
    """Demonstrate statistics retrieval."""
    print("\n" + "=" * 60)
    print("STATISTICS DEMO")
    print("=" * 60)

    # Get statistics
    print("\n6. Retrieving learning statistics...")
    stats = pipeline.get_statistics()

    if "dataset" in stats:
        print("   Dataset statistics:")
        for key, value in stats["dataset"].items():
            print(f"      {key}: {value}")

    if "styles" in stats:
        print("\n   Style statistics:")
        for style, style_stats in stats["styles"].items():
            print(f"      {style}: {style_stats}")

    if "quality_score" in stats:
        print(f"\n   Overall quality score: {stats['quality_score']:.2f}")


def demo_export(pipeline: LearningPipeline):
    """Demonstrate exporting learned data."""
    print("\n" + "=" * 60)
    print("EXPORT DEMO")
    print("=" * 60)

    # Export for generation
    print("\n7. Exporting learned data for generation...")
    export_data = pipeline.export_for_generation("data/export_for_generation.json")

    if export_data:
        print(f"   Exported at: {export_data.get('exported_at', 'unknown')}")
        print(f"   Style guides: {len(export_data.get('style_guides', {}))}")
        print(f"   Pattern guides: {len(export_data.get('pattern_guides', {}))}")
        print(
            f"   Similarity clusters: {len(export_data.get('similarity_clusters', {}))}"
        )


def demo_recommendations(pipeline: LearningPipeline):
    """Demonstrate getting recommendations."""
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS DEMO")
    print("=" * 60)

    # Get recommendations
    print("\n8. Getting generation recommendations...")
    recommendations = pipeline.get_recommendations(style="roshamuul")

    if "style_recommendations" in recommendations:
        for rec in recommendations["style_recommendations"]:
            print(f"\n   Style: {rec['style']}")
            print(f"   Confidence: {rec['confidence']:.2f}")
            if "suggestions" in rec:
                print(
                    f"   Suggested grounds: {rec['suggestions'].get('ground_tiles', [])}"
                )
                print(f"   Suggested walls: {rec['suggestions'].get('wall_tiles', [])}")

    if "combination_suggestions" in recommendations:
        print("\n   Combination suggestions:")
        for suggestion in recommendations["combination_suggestions"][:3]:
            print(
                f"      {suggestion['primary']} + {suggestion['secondary']} "
                f"({suggestion['blend_ratio']})"
            )


def create_sample_dataset() -> dict:
    """Create a sample dataset for demonstration."""
    return {
        "version": "1.0",
        "total_maps": 6,
        "total_regions": 12,
        "metadata": [
            {
                "file_path": "templates/roshamuul.json",
                "map_name": "Roshamuul",
                "width": 100,
                "height": 100,
                "floors": 3,
            },
            {
                "file_path": "templates/issavi.json",
                "map_name": "Issavi",
                "width": 80,
                "height": 80,
                "floors": 2,
            },
            {
                "file_path": "templates/library_dungeon.lua",
                "map_name": "Library",
                "width": 60,
                "height": 60,
                "floors": 4,
            },
            {
                "file_path": "templates/yalahar.json",
                "map_name": "Yalahar",
                "width": 90,
                "height": 90,
                "floors": 2,
            },
            {
                "file_path": "templates/ice.json",
                "map_name": "Ice Dungeon",
                "width": 50,
                "height": 50,
                "floors": 3,
            },
            {
                "file_path": "templates/jungle.json",
                "map_name": "Jungle",
                "width": 70,
                "height": 70,
                "floors": 1,
            },
        ],
        "regions": [
            # Roshamuul regions
            {
                "region_id": "roshamuul_r1",
                "map_file": "templates/roshamuul.json",
                "region_type": "dungeon",
                "style": "roshamuul",
                "features": {"dark": True, "prison": True},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "roshamuul_stone", "walkable": True},
                    {"x": 1, "y": 0, "ground": "roshamuul_stone", "walkable": True},
                    {"x": 0, "y": 1, "ground": "prison_floor", "walkable": True},
                    {"x": 1, "y": 1, "ground": "dark_tile", "walkable": False},
                ],
                "rooms": [
                    {
                        "id": "room_0",
                        "x": 0,
                        "y": 0,
                        "width": 10,
                        "height": 8,
                        "area": 80,
                        "shape": "rectangular",
                    },
                    {
                        "id": "room_1",
                        "x": 15,
                        "y": 0,
                        "width": 12,
                        "height": 10,
                        "area": 120,
                        "shape": "rectangular",
                    },
                ],
                "corridors": [
                    {"from": "room_0", "to": "room_1", "length": 5, "width": 2}
                ],
                "connections": [{"from": "room_0", "to": "room_1"}],
                "bounds": {"width": 30, "height": 20},
            },
            {
                "region_id": "roshamuul_r2",
                "map_file": "templates/roshamuul.json",
                "region_type": "boss_room",
                "style": "roshamuul",
                "features": {"boss": "deathslicer"},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "roshamuul_stone", "walkable": True},
                    {"x": 1, "y": 0, "ground": "roshamuul_stone", "walkable": True},
                ],
                "rooms": [
                    {
                        "id": "boss_room",
                        "x": 0,
                        "y": 0,
                        "width": 15,
                        "height": 15,
                        "area": 225,
                        "shape": "rectangular",
                    }
                ],
                "corridors": [],
                "connections": [],
                "bounds": {"width": 20, "height": 20},
            },
            # Issavi regions
            {
                "region_id": "issavi_r1",
                "map_file": "templates/issavi.json",
                "region_type": "city",
                "style": "issavi",
                "features": {"desert": True, "ancient": True},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "sand", "walkable": True},
                    {"x": 1, "y": 0, "ground": "ancient_stone", "walkable": True},
                    {"x": 0, "y": 1, "ground": "desert_tile", "walkable": True},
                    {"x": 1, "y": 1, "ground": "sandstone", "walkable": True},
                ],
                "rooms": [
                    {
                        "id": "room_0",
                        "x": 0,
                        "y": 0,
                        "width": 20,
                        "height": 15,
                        "area": 300,
                        "shape": "rectangular",
                    },
                    {
                        "id": "room_1",
                        "x": 25,
                        "y": 0,
                        "width": 18,
                        "height": 12,
                        "area": 216,
                        "shape": "rectangular",
                    },
                    {
                        "id": "room_2",
                        "x": 0,
                        "y": 20,
                        "width": 15,
                        "height": 15,
                        "area": 225,
                        "shape": "irregular",
                    },
                ],
                "corridors": [
                    {"from": "room_0", "to": "room_1", "length": 5, "width": 3},
                    {"from": "room_0", "to": "room_2", "length": 5, "width": 3},
                ],
                "connections": [
                    {"from": "room_0", "to": "room_1"},
                    {"from": "room_0", "to": "room_2"},
                ],
                "bounds": {"width": 50, "height": 40},
            },
            # Library regions
            {
                "region_id": "library_r1",
                "map_file": "templates/library_dungeon.lua",
                "region_type": "dungeon",
                "style": "library",
                "features": {"bookshelves": True, "study": True},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "library_floor", "walkable": True},
                    {"x": 1, "y": 0, "ground": "wooden_floor", "walkable": True},
                ],
                "rooms": [
                    {
                        "id": "room_0",
                        "x": 0,
                        "y": 0,
                        "width": 12,
                        "height": 10,
                        "area": 120,
                        "shape": "rectangular",
                    },
                    {
                        "id": "room_1",
                        "x": 15,
                        "y": 5,
                        "width": 10,
                        "height": 8,
                        "area": 80,
                        "shape": "rectangular",
                    },
                ],
                "corridors": [
                    {"from": "room_0", "to": "room_1", "length": 5, "width": 2}
                ],
                "connections": [{"from": "room_0", "to": "room_1"}],
                "bounds": {"width": 30, "height": 20},
            },
            # Falcon regions
            {
                "region_id": "falcon_r1",
                "map_file": "templates/issavi.json",
                "region_type": "tower",
                "style": "falcon",
                "features": {"noble": True, "bird_motif": True},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "falcon_tile", "walkable": True},
                    {"x": 1, "y": 0, "ground": "marble_floor", "walkable": True},
                ],
                "rooms": [
                    {
                        "id": "room_0",
                        "x": 0,
                        "y": 0,
                        "width": 8,
                        "height": 8,
                        "area": 64,
                        "shape": "rectangular",
                    },
                    {
                        "id": "room_1",
                        "x": 0,
                        "y": 10,
                        "width": 8,
                        "height": 8,
                        "area": 64,
                        "shape": "rectangular",
                    },
                    {
                        "id": "room_2",
                        "x": 0,
                        "y": 20,
                        "width": 8,
                        "height": 8,
                        "area": 64,
                        "shape": "rectangular",
                    },
                ],
                "corridors": [
                    {"from": "room_0", "to": "room_1", "length": 2, "width": 2},
                    {"from": "room_1", "to": "room_2", "length": 2, "width": 2},
                ],
                "connections": [
                    {"from": "room_0", "to": "room_1"},
                    {"from": "room_1", "to": "room_2"},
                ],
                "bounds": {"width": 10, "height": 30},
            },
            # Cobra regions
            {
                "region_id": "cobra_r1",
                "map_file": "templates/jungle.json",
                "region_type": "dungeon",
                "style": "cobra",
                "features": {"serpent": True, "exotic": True},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "cobra_tile", "walkable": True},
                    {"x": 1, "y": 0, "ground": "serpent_stone", "walkable": True},
                ],
                "rooms": [
                    {
                        "id": "room_0",
                        "x": 0,
                        "y": 0,
                        "width": 15,
                        "height": 12,
                        "area": 180,
                        "shape": "irregular",
                    },
                    {
                        "id": "room_1",
                        "x": 20,
                        "y": 5,
                        "width": 10,
                        "height": 10,
                        "area": 100,
                        "shape": "rectangular",
                    },
                ],
                "corridors": [
                    {"from": "room_0", "to": "room_1", "length": 5, "width": 3}
                ],
                "connections": [{"from": "room_0", "to": "room_1"}],
                "bounds": {"width": 35, "height": 20},
            },
            # Additional regions for variety
            {
                "region_id": "yalahar_r1",
                "map_file": "templates/yalahar.json",
                "region_type": "city",
                "style": "yalahar",
                "features": {"mysterious": True},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "yalahar_stone", "walkable": True},
                    {"x": 1, "y": 0, "ground": "mystery_tile", "walkable": True},
                ],
                "rooms": [
                    {
                        "id": "room_0",
                        "x": 0,
                        "y": 0,
                        "width": 25,
                        "height": 20,
                        "area": 500,
                        "shape": "rectangular",
                    }
                ],
                "corridors": [],
                "connections": [],
                "bounds": {"width": 30, "height": 25},
            },
            {
                "region_id": "ice_r1",
                "map_file": "templates/ice.json",
                "region_type": "cave",
                "style": "unknown",
                "features": {"ice": True},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "ice", "walkable": True},
                    {"x": 1, "y": 0, "ground": "snow", "walkable": True},
                ],
                "rooms": [
                    {
                        "id": "room_0",
                        "x": 0,
                        "y": 0,
                        "width": 20,
                        "height": 15,
                        "area": 300,
                        "shape": "irregular",
                    }
                ],
                "corridors": [],
                "connections": [],
                "bounds": {"width": 25, "height": 20},
            },
            {
                "region_id": "jungle_r1",
                "map_file": "templates/jungle.json",
                "region_type": "cave",
                "style": "unknown",
                "features": {"jungle": True},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "grass", "walkable": True},
                    {"x": 1, "y": 0, "ground": "dirt", "walkable": True},
                ],
                "rooms": [
                    {
                        "id": "room_0",
                        "x": 0,
                        "y": 0,
                        "width": 18,
                        "height": 12,
                        "area": 216,
                        "shape": "organic",
                    }
                ],
                "corridors": [],
                "connections": [],
                "bounds": {"width": 22, "height": 16},
            },
            # Temple regions
            {
                "region_id": "issavi_temple_r1",
                "map_file": "templates/issavi.json",
                "region_type": "temple",
                "style": "issavi",
                "features": {"temple": True, "sacred": True},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "ancient_stone", "walkable": True},
                    {"x": 1, "y": 0, "ground": "sand", "walkable": True},
                ],
                "rooms": [
                    {
                        "id": "room_0",
                        "x": 0,
                        "y": 0,
                        "width": 20,
                        "height": 20,
                        "area": 400,
                        "shape": "rectangular",
                    }
                ],
                "corridors": [],
                "connections": [],
                "bounds": {"width": 25, "height": 25},
            },
            {
                "region_id": "roshamuul_temple_r1",
                "map_file": "templates/roshamuul.json",
                "region_type": "temple",
                "style": "roshamuul",
                "features": {"temple": True, "dark": True},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "roshamuul_stone", "walkable": True},
                    {"x": 1, "y": 0, "ground": "dark_tile", "walkable": True},
                ],
                "rooms": [
                    {
                        "id": "room_0",
                        "x": 0,
                        "y": 0,
                        "width": 18,
                        "height": 18,
                        "area": 324,
                        "shape": "rectangular",
                    }
                ],
                "corridors": [],
                "connections": [],
                "bounds": {"width": 22, "height": 22},
            },
            {
                "region_id": "library_boss_r1",
                "map_file": "templates/library_dungeon.lua",
                "region_type": "boss_room",
                "style": "library",
                "features": {"boss": "bookworm"},
                "tiles": [
                    {"x": 0, "y": 0, "ground": "library_floor", "walkable": True}
                ],
                "rooms": [
                    {
                        "id": "boss_room",
                        "x": 0,
                        "y": 0,
                        "width": 20,
                        "height": 20,
                        "area": 400,
                        "shape": "rectangular",
                    }
                ],
                "corridors": [],
                "connections": [],
                "bounds": {"width": 25, "height": 25},
            },
        ],
        "features": [],
        "statistics": {
            "style_distribution": {
                "roshamuul": 3,
                "issavi": 3,
                "library": 2,
                "falcon": 1,
                "cobra": 1,
                "yalahar": 1,
                "unknown": 2,
            },
            "type_distribution": {
                "dungeon": 3,
                "city": 2,
                "boss_room": 2,
                "tower": 1,
                "cave": 2,
                "temple": 2,
            },
            "avg_map_size": 4900,
            "total_files": 6,
        },
    }


def main():
    """Run all demos."""
    # Create data directory
    os.makedirs("data", exist_ok=True)

    # Run demos
    pipeline = demo_basic_learning()
    demo_similarity_search(pipeline)
    demo_blueprint_generation(pipeline)
    demo_statistics(pipeline)
    demo_export(pipeline)
    demo_recommendations(pipeline)

    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print("\nThe map learning AI system is ready for use.")
    print("Generated files can be found in the 'data/' directory.")


if __name__ == "__main__":
    main()
