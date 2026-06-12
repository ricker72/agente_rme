"""
Hunt Generator — generates complete hunt zones as WorldModel instances.

This is the first fully functional generator. It converts a prompt like:
    {"theme": "issavi", "level_min": 300, "level_max": 500}

into a populated WorldModel with:
    - Ground tiles with theme-appropriate IDs
    - Walls/boundaries
    - Decorative elements (statues, torches, etc.)
    - Monster spawns appropriate for the level range
    - A named Region

Flow:
    1. Select blueprint base if available
    2. Place blueprint tiles
    3. Generate ground terrain
    4. Generate decoration
    5. Generate spawns
    6. Validate
"""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, Optional

from .base_generator import BaseGenerator
from .theme_generator import ThemeGenerator, ThemeDefinition
from .spawn_generator import SpawnGenerator
from core.world import WorldModel, Tile, Structure, Region

logger = logging.getLogger(__name__)


class HuntGenerator(BaseGenerator):
    """
    Generates complete hunt zones from a configuration dict.

    Args:
        seed: Optional random seed for reproducible generation.

    Usage:
        hg = HuntGenerator()
        world = hg.generate(WorldModel(), {
            "theme": "issavi",
            "level_min": 300,
            "level_max": 500,
        })
        print(len(world.tiles))  # > 0
    """

    # Default zone dimensions
    DEFAULT_WIDTH = 50
    DEFAULT_HEIGHT = 50
    DEFAULT_Z = 7

    def __init__(self, seed: Optional[int] = None, **kwargs):
        self._rng = random.Random(seed)
        self._theme_gen = ThemeGenerator()
        self._spawn_gen = SpawnGenerator(seed=seed)
        # Backward compatibility: accept width/height kwargs (used by pipeline_runner.py)
        self._legacy_width = kwargs.get("width", self.DEFAULT_WIDTH)
        self._legacy_height = kwargs.get("height", self.DEFAULT_HEIGHT)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        world: Optional[WorldModel] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorldModel:
        """
        Generate a complete hunt zone.

        Args:
            world: Optional WorldModel to populate. Creates a new one if None.
            context: Configuration dict with:
                - theme (str): Theme name (e.g., "issavi", "roshamuul")
                - level_min (int): Minimum player level
                - level_max (int): Maximum player level
                - density (str): Spawn density ("low", "medium", "high")
                - width (int): Zone width in tiles (default 50)
                - height (int): Zone height in tiles (default 50)
                - origin_x, origin_y (int): World position origin (default 0, 0)
                - z (int): Z layer (default 7)

        Returns:
            Populated WorldModel instance.
        """
        if world is None:
            world = WorldModel()
        if context is None:
            context = {}

        # --- 1. Extract & normalize parameters ---
        theme_name = context.get("theme", "generic")
        level_min = context.get("level_min", 1)
        level_max = context.get("level_max", 9999)
        density = context.get("density", "medium")
        width = context.get("width", self.DEFAULT_WIDTH)
        height = context.get("height", self.DEFAULT_HEIGHT)
        ox = context.get("origin_x", 0)
        oy = context.get("origin_y", 0)
        z = context.get("z", self.DEFAULT_Z)

        # --- 2. Resolve theme ---
        theme_def = self._theme_gen.resolve(theme_name)
        context["theme_def"] = theme_def

        # --- 3. Create region ---
        region_name = f"hunt_{theme_def.theme}_{ox}_{oy}"
        region = Region(
            name=region_name,
            theme=theme_def.theme,
            min_level=level_min,
            max_level=level_max,
            tags=["hunt", theme_def.theme],
        )
        world.add_region(region)

        # --- 4. Generate ground terrain ---
        self._generate_ground(world, theme_def, ox, oy, width, height, z)

        # --- 5. Generate walls/boundaries ---
        self._generate_walls(world, theme_def, ox, oy, width, height, z)

        # --- 6. Generate decorations ---
        self._generate_decorations(world, theme_def, ox, oy, width, height, z)

        # --- 7. Generate spawns ---
        spawn_context = {
            "theme_def": theme_def,
            "level_min": level_min,
            "level_max": level_max,
            "density": density,
            "area": (ox, oy, ox + width, oy + height),
        }
        self._spawn_gen.generate(world, spawn_context)

        # --- 8. Add structure metadata ---
        structure = Structure(
            name=f"hunt_zone_{region_name}",
            category="hunt",
            x=ox,
            y=oy,
            z=z,
            width=width,
            height=height,
            tile_count=width * height,
            tags=["hunt", theme_def.theme],
        )
        world.add_structure(structure)

        # --- 9. Validate and return ---
        from core.world import WorldValidator

        validator = WorldValidator()
        result = validator.validate(world)
        if not result.passed:
            logger.warning(f"HuntGenerator validation warnings:\n{result.summary()}")

        logger.info(
            f"HuntGenerator: generated '{theme_def.theme}' hunt zone ({width}x{height}) with {world.tile_count()} tiles"
        )
        return world

    # ------------------------------------------------------------------
    # Terrain generation
    # ------------------------------------------------------------------

    def _generate_ground(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        ox: int,
        oy: int,
        width: int,
        height: int,
        z: int,
    ) -> None:
        """Fill the zone with ground tiles using theme-appropriate IDs."""
        grounds = theme_def.grounds if theme_def.grounds else [396]

        for x in range(ox, ox + width):
            for y in range(oy, oy + height):
                ground_id = self._rng.choice(grounds)
                tile = Tile(x=x, y=y, z=z, ground=ground_id)
                world.set_tile(tile)

    def _generate_walls(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        ox: int,
        oy: int,
        width: int,
        height: int,
        z: int,
    ) -> None:
        """Add boundary walls around the hunt zone."""
        walls = theme_def.walls if theme_def.walls else [1498]
        wall_id = walls[0]

        # Top and bottom edges
        for x in range(ox, ox + width):
            self._place_wall(world, x, oy, z, wall_id)  # top
            self._place_wall(world, x, oy + height - 1, z, wall_id)  # bottom

        # Left and right edges (excluding corners already placed)
        for y in range(oy + 1, oy + height - 1):
            self._place_wall(world, ox, y, z, wall_id)  # left
            self._place_wall(world, ox + width - 1, y, z, wall_id)  # right

    def _place_wall(
        self,
        world: WorldModel,
        x: int,
        y: int,
        z: int,
        wall_id: int,
    ) -> None:
        """Place a wall on a tile, preserving any existing ground."""
        existing = world.get_tile(x, y, z)
        if existing:
            existing.ground = wall_id
        else:
            world.set_tile(Tile(x=x, y=y, z=z, ground=wall_id))

    def _generate_decorations(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        ox: int,
        oy: int,
        width: int,
        height: int,
        z: int,
        density: float = 0.03,
    ) -> None:
        """Add decorative items (statues, torches, etc.) to the zone."""
        decorations = theme_def.decorations if theme_def.decorations else []

        if not decorations:
            return

        for tile in world.tiles.values():
            if tile.z != z:
                continue
            if (
                tile.x == ox
                or tile.x == ox + width - 1
                or tile.y == oy
                or tile.y == oy + height - 1
            ):
                continue  # skip walls
            if self._rng.random() < density:
                deco_id = self._rng.choice(decorations)
                tile.items.append({"id": deco_id})
