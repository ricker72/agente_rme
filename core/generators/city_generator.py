"""
City Generator — generates city layouts (temple, depot, market, houses, roads)
as WorldModel instances.

Produces:
    - Temple (central landmark)
    - Depot (storage area)
    - Market (trading area)
    - Houses (residential zones)
    - Roads (connecting paths)
    - Monster spawns (low density, appropriate for city)
"""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .base_generator import BaseGenerator
from .theme_generator import ThemeGenerator, ThemeDefinition
from .spawn_generator import SpawnGenerator
from core.world import WorldModel, Tile, Spawn, Structure, Region

logger = logging.getLogger(__name__)


class CityGenerator(BaseGenerator):
    """
    Generates city layouts from a configuration dict.

    Usage:
        cg = CityGenerator()
        world = cg.generate(WorldModel(), {
            "theme": "issavi",
            "level_min": 50,
            "level_max": 200,
        })
    """

    # Default city size
    DEFAULT_WIDTH = 100
    DEFAULT_HEIGHT = 100
    DEFAULT_Z = 7

    # Road parameters
    ROAD_WIDTH = 3
    BUILDING_MIN_SIZE = 6
    BUILDING_MAX_SIZE = 12

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._theme_gen = ThemeGenerator()
        self._spawn_gen = SpawnGenerator(seed=seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        world: Optional[WorldModel] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorldModel:
        """
        Generate a complete city layout.

        Args:
            world: Optional WorldModel to populate.
            context: Configuration dict with:
                - theme (str): Theme name
                - level_min, level_max (int): Level range
                - width, height (int): City dimensions (default 100x100)
                - origin_x, origin_y (int): World position

        Returns:
            Populated WorldModel.
        """
        if world is None:
            world = WorldModel()
        if context is None:
            context = {}

        theme_name = context.get("theme", "generic")
        level_min = context.get("level_min", 1)
        level_max = context.get("level_max", 9999)
        width = context.get("width", self.DEFAULT_WIDTH)
        height = context.get("height", self.DEFAULT_HEIGHT)
        ox = context.get("origin_x", 0)
        oy = context.get("origin_y", 0)
        z = context.get("z", self.DEFAULT_Z)

        # Resolve theme
        theme_def = self._theme_gen.resolve(theme_name)
        context["theme_def"] = theme_def

        # Create region
        region = Region(
            name=f"city_{theme_def.theme}_{ox}_{oy}",
            theme=theme_def.theme,
            min_level=level_min,
            max_level=level_max,
            tags=["city", theme_def.theme],
        )
        world.add_region(region)

        # Generate city layout
        center_x = ox + width // 2
        center_y = oy + height // 2

        # 1. Generate base ground
        self._generate_ground(world, theme_def, ox, oy, width, height, z)

        # 2. Generate road grid
        self._generate_roads(world, theme_def, ox, oy, width, height, z)

        # 3. Place temple at center
        self._place_temple(world, theme_def, center_x, center_y, z)

        # 4. Generate building blocks
        self._generate_buildings(world, theme_def, ox, oy, width, height, z)

        # 5. Generate spawns (low density for city)
        spawn_context = {
            "theme_def": theme_def,
            "level_min": level_min,
            "level_max": level_max,
            "density": "low",
            "area": (ox, oy, ox + width, oy + height),
        }
        self._spawn_gen.generate(world, spawn_context)

        # 6. Add structure metadata
        structure = Structure(
            name=f"city_{region.name}",
            category="city",
            x=ox,
            y=oy,
            z=z,
            width=width,
            height=height,
            tile_count=world.tile_count(),
            tags=["city", theme_def.theme],
        )
        world.add_structure(structure)

        # 7. Validate
        from core.world import WorldValidator
        validator = WorldValidator()
        result = validator.validate(world)
        if not result.passed:
            logger.warning(f"CityGenerator validation:\n{result.summary()}")

        logger.info(
            f"CityGenerator: generated '{theme_def.theme}' city "
            f"({width}x{height}) with {world.tile_count()} tiles"
        )
        return world

    # ------------------------------------------------------------------
    # Generation methods
    # ------------------------------------------------------------------

    def _generate_ground(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        ox: int, oy: int,
        width: int, height: int,
        z: int,
    ) -> None:
        """Fill the city area with ground tiles."""
        grounds = theme_def.grounds if theme_def.grounds else [396]
        for x in range(ox, ox + width):
            for y in range(oy, oy + height):
                ground_id = self._rng.choice(grounds)
                world.set_tile(Tile(x=x, y=y, z=z, ground=ground_id))

    def _generate_roads(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        ox: int, oy: int,
        width: int, height: int,
        z: int,
    ) -> None:
        """Generate a grid of roads through the city."""
        # Use a distinct ground ID for roads (or first ground if only one)
        road_ground = theme_def.grounds[0] if theme_def.grounds else 396

        # Horizontal road at center
        road_y = oy + height // 2
        half_road = self.ROAD_WIDTH // 2
        for y in range(road_y - half_road, road_y + half_road + 1):
            for x in range(ox, ox + width):
                tile = world.get_tile(x, y, z)
                if tile:
                    tile.ground = road_ground

        # Vertical road at center
        road_x = ox + width // 2
        for x in range(road_x - half_road, road_x + half_road + 1):
            for y in range(oy, oy + height):
                tile = world.get_tile(x, y, z)
                if tile:
                    tile.ground = road_ground

        # Additional horizontal roads at quarters
        for qy in [oy + height // 4, oy + 3 * height // 4]:
            for y in range(qy, qy + 1):  # single-tile paths
                for x in range(ox, ox + width):
                    tile = world.get_tile(x, y, z)
                    if tile:
                        tile.ground = road_ground

        # Additional vertical roads at quarters
        for qx in [ox + width // 4, ox + 3 * width // 4]:
            for x in range(qx, qx + 1):
                for y in range(oy, oy + height):
                    tile = world.get_tile(x, y, z)
                    if tile:
                        tile.ground = road_ground

    def _place_temple(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        cx: int, cy: int,
        z: int,
    ) -> None:
        """Place a temple structure at the city center."""
        temple_size = 14
        half = temple_size // 2
        temple_x = cx - half
        temple_y = cy - half

        # Use a distinct ground for temple floor
        temple_ground = theme_def.grounds[-1] if theme_def.grounds else 396

        for x in range(temple_x, temple_x + temple_size):
            for y in range(temple_y, temple_y + temple_size):
                tile = world.get_tile(x, y, z)
                if tile:
                    tile.ground = temple_ground
                    tile.zone = "temple"

        structure = Structure(
            name="temple",
            category="temple",
            x=temple_x,
            y=temple_y,
            z=z,
            width=temple_size,
            height=temple_size,
            tile_count=temple_size * temple_size,
        )
        world.add_structure(structure)

    def _generate_buildings(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        ox: int, oy: int,
        width: int, height: int,
        z: int,
    ) -> None:
        """Generate building blocks in the city quadrants."""
        building_ground = theme_def.grounds[0] if theme_def.grounds else 396
        cx = ox + width // 2
        cy = oy + height // 2

        building_areas = [
            # (x1, y1, x2, y2) — offsets from origin
            (ox + 5, oy + 5, cx - 10, cy - 5),           # NW
            (cx + 10, oy + 5, ox + width - 5, cy - 5),   # NE
            (ox + 5, cy + 10, cx - 10, oy + height - 5), # SW
            (cx + 10, cy + 10, ox + width - 5, oy + height - 5), # SE
        ]

        for bx1, by1, bx2, by2 in building_areas:
            self._generate_building_block(
                world, bx1, by1, bx2, by2, z, building_ground
            )

    def _generate_building_block(
        self,
        world: WorldModel,
        x1: int, y1: int,
        x2: int, y2: int,
        z: int,
        ground_id: int,
    ) -> None:
        """Generate a block of buildings separated by small paths."""
        step = self.BUILDING_MIN_SIZE + 2  # building + path
        for bx in range(x1, x2, step):
            for by in range(y1, y2, step):
                bw = self._rng.randint(
                    self.BUILDING_MIN_SIZE, self.BUILDING_MAX_SIZE
                )
                bh = self._rng.randint(
                    self.BUILDING_MIN_SIZE, self.BUILDING_MAX_SIZE
                )
                # Clamp to area
                bw = min(bw, x2 - bx)
                bh = min(bh, y2 - by)
                if bw < self.BUILDING_MIN_SIZE or bh < self.BUILDING_MIN_SIZE:
                    continue

                # Place building tiles
                for x in range(bx, bx + bw):
                    for y in range(by, by + bh):
                        tile = world.get_tile(x, y, z)
                        if tile:
                            tile.ground = ground_id
                            tile.zone = "building"

                # Register as a structure
                structure = Structure(
                    name=f"building_{bx}_{by}",
                    category="building",
                    x=bx,
                    y=by,
                    z=z,
                    width=bw,
                    height=bh,
                    tile_count=bw * bh,
                    tags=["city"],
                )
                world.add_structure(structure)