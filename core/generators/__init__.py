"""
core.generators — procedural world generators that produce WorldModel instances.

All generators in this package build and return a populated WorldModel
directly, rather than emitting Lua scripts. This is the intended pipeline:

    Asset Registry → Blueprint Registry → World Model → World Generator
    → QA → Lua Export → OTBM Export

Available generators:
    - BaseGenerator      — abstract base class for all generators
    - ThemeGenerator     — resolves theme strings into ThemeDefinition
    - SpawnGenerator     — places monster spawns on existing tiles
    - HuntGenerator      — complete hunt zones with terrain and spawns
    - CityGenerator      — city layout with streets, buildings, districts
    - DungeonGenerator   — underground dungeon with rooms and corridors
    - WorldGenerator     — orchestrates all generators from a prompt
"""

from .base_generator import BaseGenerator
from .theme_generator import ThemeGenerator, ThemeDefinition
from .spawn_generator import SpawnGenerator
from .hunt_generator import HuntGenerator
from .city_generator import CityGenerator
from .dungeon_generator import DungeonGenerator
from .world_generator import WorldGenerator

__all__ = [
    "BaseGenerator",
    "ThemeGenerator",
    "ThemeDefinition",
    "SpawnGenerator",
    "HuntGenerator",
    "CityGenerator",
    "DungeonGenerator",
    "WorldGenerator",
]
