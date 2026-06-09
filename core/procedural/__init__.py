"""
HITO 16 - Procedural World Generation
=====================================

Turns a `WorldPlan` (from HITO 15's AIArchitect) into a fully
populated `WorldModel` (from HITO 14's world engine).

Modules:
    biome_generator    — biome surface (grass, sand, snow, ...)
    terrain_generator  — mountains, hills, water bodies, lava, forest
    road_generator     — road network + city street grid + bridges
    river_generator    — flowing rivers with banks
    continent_generator — top-level orchestrator (plan -> world)
    world_synthesizer  — final assembly + validation + merging

Usage:
    from core.architect import AIArchitect
    from core.procedural import (
        generate_continent, synthesize, generate_from_prompt,
    )

    architect = AIArchitect()
    plan = architect.plan("Generate Issavi city with 3 hunts and a boss")
    world = synthesize(plan, seed=42)
"""

from __future__ import annotations

# -----------------------------------------------------------------------------
# Biome generator
# -----------------------------------------------------------------------------
from .biome_generator import (
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

# -----------------------------------------------------------------------------
# Terrain generator
# -----------------------------------------------------------------------------
from .terrain_generator import (
    TerrainGenerator,
    TerrainFeature,
    generate_terrain,
    generate_mountains,
    generate_hills,
    generate_water_bodies,
    generate_lava_fields,
    get_terrain_ground_id,
    value_noise_2d,
    fbm_noise_2d,
    TERRAIN_GROUND_IDS,
    noise_generator_script,
)

# -----------------------------------------------------------------------------
# Road generator
# -----------------------------------------------------------------------------
from .road_generator import (
    RoadGenerator,
    RoadSegment,
    RoadNetwork,
    Point,
    generate_road,
    connect_zones,
    build_city_grid,
    build_bridge,
    get_road_ground_id,
    get_bridge_ground_id,
    ROAD_GROUND_IDS,
    BRIDGE_GROUND_IDS,
    road_generator_lua,
)

# -----------------------------------------------------------------------------
# River generator
# -----------------------------------------------------------------------------
from .river_generator import (
    RiverGenerator,
    River,
    RiverPoint,
    generate_river,
    generate_rivers,
    get_river_ground_id,
    get_river_bank_id,
    RIVER_GROUND_IDS,
    RIVER_BANK_IDS,
)

# -----------------------------------------------------------------------------
# Continent generator (top-level orchestrator)
# -----------------------------------------------------------------------------
from .continent_generator import (
    ContinentGenerator,
    ContinentResult,
    generate_continent,
    generate_from_prompt,
)

# -----------------------------------------------------------------------------
# World synthesizer (final assembly)
# -----------------------------------------------------------------------------
from .world_synthesizer import (
    WorldSynthesizer,
    SynthesisReport,
    synthesize,
    merge,
    validate_synthesis,
    attach_ai_architect,
    attach_blueprint_registry,
)


__all__ = [
    # Biome
    "BiomeGenerator",
    "BiomeTile",
    "generate_biome",
    "generate_continental_biome",
    "generate_zone_biome",
    "get_biome_palette",
    "pick_ground_for_tag",
    "pick_primary_tag",
    "BIOME_PALETTES",
    "BIOME_TAG_BY_THEME",
    "biome_generator_lua",
    # Terrain
    "TerrainGenerator",
    "TerrainFeature",
    "generate_terrain",
    "generate_mountains",
    "generate_hills",
    "generate_water_bodies",
    "generate_lava_fields",
    "get_terrain_ground_id",
    "value_noise_2d",
    "fbm_noise_2d",
    "TERRAIN_GROUND_IDS",
    "noise_generator_script",
    # Road
    "RoadGenerator",
    "RoadSegment",
    "RoadNetwork",
    "Point",
    "generate_road",
    "connect_zones",
    "build_city_grid",
    "build_bridge",
    "get_road_ground_id",
    "get_bridge_ground_id",
    "ROAD_GROUND_IDS",
    "BRIDGE_GROUND_IDS",
    "road_generator_lua",
    # River
    "RiverGenerator",
    "River",
    "RiverPoint",
    "generate_river",
    "generate_rivers",
    "get_river_ground_id",
    "get_river_bank_id",
    "RIVER_GROUND_IDS",
    "RIVER_BANK_IDS",
    # Continent
    "ContinentGenerator",
    "ContinentResult",
    "generate_continent",
    "generate_from_prompt",
    # Synthesizer
    "WorldSynthesizer",
    "SynthesisReport",
    "synthesize",
    "merge",
    "validate_synthesis",
    "attach_ai_architect",
    "attach_blueprint_registry",
]
