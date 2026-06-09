"""
Unified World Model — the single source of truth for the entire map.

All subsystems (blueprints, export, preview, QA, playtest) use this
representation instead of working with raw tiles, items, and spawns separately.
"""

from .tile import Tile
from .item import Item
from .spawn import Spawn
from .structure import Structure
from .region import Region
from .chunk import Chunk
from .world_model import WorldModel
from .world_validator import WorldValidator, WorldValidationResult

__all__ = [
    "Tile",
    "Item",
    "Spawn",
    "Structure",
    "Region",
    "Chunk",
    "WorldModel",
    "WorldValidator",
    "WorldValidationResult",
]