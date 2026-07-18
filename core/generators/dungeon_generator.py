"""
Dungeon Generator — generates underground dungeon layouts (entrance, loops,
branches, boss_room, exit) as WorldModel instances.

Produces:
    - Entrance (staircase down)
    - Room loops (connected rooms)
    - Branches (corridors off main loop)
    - Boss room (large chamber with boss spawn)
    - Exit (staircase up)
    - Monster spawns appropriate for level range
"""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, List, Optional, Tuple

from .base_generator import BaseGenerator
from .theme_generator import ThemeGenerator, ThemeDefinition
from .spawn_generator import SpawnGenerator
from core.world import WorldModel, Tile, Spawn, Structure, Region

logger = logging.getLogger(__name__)


class DungeonGenerator(BaseGenerator):
    """
    Generates dungeon layouts from a configuration dict.

    Usage:
        dg = DungeonGenerator()
        world = dg.generate(WorldModel(), {
            "theme": "library",
            "level_min": 200,
            "level_max": 400,
        })
    """

    # Default dungeon dimensions
    DEFAULT_WIDTH = 60
    DEFAULT_HEIGHT = 60
    DEFAULT_Z = 7

    # Room generation parameters
    MIN_ROOM_SIZE = 5
    MAX_ROOM_SIZE = 10
    CORRIDOR_WIDTH = 2
    NUM_ROOMS = 8

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
        Generate a complete dungeon layout.

        Args:
            world: Optional WorldModel to populate.
            context: Configuration dict with:
                - theme (str): Theme name
                - level_min, level_max (int): Level range
                - width, height (int): Dungeon dimensions (default 60x60)
                - origin_x, origin_y (int): World position
                - num_rooms (int): Number of rooms (default 8)

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
        num_rooms = context.get("num_rooms", self.NUM_ROOMS)

        # Resolve theme
        theme_def = self._theme_gen.resolve(theme_name)
        context["theme_def"] = theme_def

        # Create region
        region = Region(
            name=f"dungeon_{theme_def.theme}_{ox}_{oy}",
            theme=theme_def.theme,
            min_level=level_min,
            max_level=level_max,
            tags=["dungeon", theme_def.theme],
        )
        world.add_region(region)

        # 1. Generate entrance
        entrance_x, entrance_y = self._generate_entrance(
            world, theme_def, ox, oy, width, z
        )

        # 2. Generate rooms and corridors (loops + branches)
        rooms = self._generate_rooms(
            world, theme_def, ox, oy, width, height, z, num_rooms
        )

        # 3. Connect rooms with corridors
        self._connect_rooms(world, theme_def, rooms, z)

        # 4. Generate boss room
        boss_room = self._generate_boss_room(world, theme_def, ox, oy, width, height, z)

        # 5. Generate exit near boss room
        self._generate_exit(world, theme_def, boss_room, z)

        # 6. Generate spawns (high density for dungeon)
        spawn_context = {
            "theme_def": theme_def,
            "level_min": level_min,
            "level_max": level_max,
            "density": "high",
            "area": (ox, oy, ox + width, oy + height),
        }
        self._spawn_gen.generate(world, spawn_context)

        # 7. Add structure metadata
        structure = Structure(
            name=f"dungeon_{region.name}",
            category="dungeon",
            x=ox,
            y=oy,
            z=z,
            width=width,
            height=height,
            tile_count=world.tile_count(),
            tags=["dungeon", theme_def.theme],
        )
        world.add_structure(structure)

        # 8. Validate
        from core.world import WorldValidator

        validator = WorldValidator()
        result = validator.validate(world)
        if not result.passed:
            logger.warning(f"DungeonGenerator validation:\n{result.summary()}")

        logger.info(
            f"DungeonGenerator: generated '{theme_def.theme}' dungeon "
            f"({width}x{height}, {len(rooms)} rooms) with {world.tile_count()} tiles"
        )
        return world

    # ------------------------------------------------------------------
    # Generation methods
    # ------------------------------------------------------------------

    def _generate_entrance(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        ox: int,
        oy: int,
        width: int,
        z: int,
    ) -> Tuple[int, int]:
        """Generate the dungeon entrance (staircase)."""
        ex = ox + self._rng.randint(2, width - 3)
        ey = oy + 2

        ground_id = theme_def.grounds[0] if theme_def.grounds else 396

        # Create entrance platform (3x3)
        for x in range(ex - 1, ex + 2):
            for y in range(ey - 1, ey + 2):
                tile = Tile(x=x, y=y, z=z, ground=ground_id)
                tile.zone = "entrance"
                # Add staircase item (ID 130 — typical staircase down)
                tile.items.append({"id": 130})
                world.set_tile(tile)

        structure = Structure(
            name="entrance",
            category="entrance",
            x=ex - 1,
            y=ey - 1,
            z=z,
            width=3,
            height=3,
            tile_count=9,
            tags=["dungeon"],
        )
        world.add_structure(structure)

        return ex, ey

    def _generate_rooms(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        ox: int,
        oy: int,
        width: int,
        height: int,
        z: int,
        num_rooms: int,
    ) -> List[Dict[str, int]]:
        """
        Generate rooms within the dungeon area.

        Returns:
            List of room dicts with {x, y, w, h, cx, cy} (cx, cy = center).
        """
        rooms: List[Dict[str, int]] = []
        ground_id = theme_def.grounds[0] if theme_def.grounds else 396
        padding = 3  # Minimum distance between rooms

        for _ in range(num_rooms * 3):  # Try more to find valid placements
            if len(rooms) >= num_rooms:
                break

            rw = self._rng.randint(self.MIN_ROOM_SIZE, self.MAX_ROOM_SIZE)
            rh = self._rng.randint(self.MIN_ROOM_SIZE, self.MAX_ROOM_SIZE)
            rx = self._rng.randint(ox + 5, ox + width - rw - 5)
            ry = self._rng.randint(oy + 10, oy + height - rh - 10)

            # Check for collisions with existing rooms
            collision = False
            for existing in rooms:
                if not (
                    rx + rw + padding < existing["x"]
                    or rx > existing["x"] + existing["w"] + padding
                    or ry + rh + padding < existing["y"]
                    or ry > existing["y"] + existing["h"] + padding
                ):
                    collision = True
                    break

            if collision:
                continue

            # Place room tiles
            for x in range(rx, rx + rw):
                for y in range(ry, ry + rh):
                    tile = Tile(x=x, y=y, z=z, ground=ground_id)
                    tile.zone = "room"
                    world.set_tile(tile)

            room_data = {
                "x": rx,
                "y": ry,
                "w": rw,
                "h": rh,
                "cx": rx + rw // 2,
                "cy": ry + rh // 2,
            }
            rooms.append(room_data)

            structure = Structure(
                name=f"room_{rx}_{ry}",
                category="dungeon_room",
                x=rx,
                y=ry,
                z=z,
                width=rw,
                height=rh,
                tile_count=rw * rh,
                tags=["dungeon"],
            )
            world.add_structure(structure)

        return rooms

    def _connect_rooms(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        rooms: List[Dict[str, int]],
        z: int,
    ) -> None:
        """Connect rooms with corridors."""
        if len(rooms) < 2:
            return

        ground_id = theme_def.grounds[0] if theme_def.grounds else 396

        # Connect each room to the next (forming a loop)
        for i in range(len(rooms)):
            room_a = rooms[i]
            room_b = rooms[(i + 1) % len(rooms)]

            # L-shaped corridor
            self._carve_corridor(
                world,
                room_a["cx"],
                room_a["cy"],
                room_b["cx"],
                room_a["cy"],
                z,
                ground_id,
                "corridor_h",
            )
            self._carve_corridor(
                world,
                room_b["cx"],
                room_a["cy"],
                room_b["cx"],
                room_b["cy"],
                z,
                ground_id,
                "corridor_v",
            )

    def _carve_corridor(
        self,
        world: WorldModel,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        z: int,
        ground_id: int,
        zone: str,
    ) -> None:
        """Carve a corridor between two points."""
        if x1 == x2:
            # Vertical corridor
            start_y, end_y = (y1, y2) if y1 < y2 else (y2, y1)
            for y in range(start_y, end_y + 1):
                for dx in range(self.CORRIDOR_WIDTH):
                    tile = Tile(x=x1 + dx, y=y, z=z, ground=ground_id)
                    tile.zone = zone
                    world.set_tile(tile)
        elif y1 == y2:
            # Horizontal corridor
            start_x, end_x = (x1, x2) if x1 < x2 else (x2, x1)
            for x in range(start_x, end_x + 1):
                for dy in range(self.CORRIDOR_WIDTH):
                    tile = Tile(x=x, y=y1 + dy, z=z, ground=ground_id)
                    tile.zone = zone
                    world.set_tile(tile)

    def _generate_boss_room(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        ox: int,
        oy: int,
        width: int,
        height: int,
        z: int,
    ) -> Dict[str, int]:
        """Generate a large boss room at the far end of the dungeon."""
        boss_size = 14
        bx = ox + width - boss_size - 5
        by = oy + height // 2 - boss_size // 2
        ground_id = theme_def.grounds[-1] if theme_def.grounds else 396

        for x in range(bx, bx + boss_size):
            for y in range(by, by + boss_size):
                tile = Tile(x=x, y=y, z=z, ground=ground_id)
                tile.zone = "boss"
                world.set_tile(tile)

        # Add boss spawn
        boss_cx = bx + boss_size // 2
        boss_cy = by + boss_size // 2
        boss_tile = world.get_tile(boss_cx, boss_cy, z)
        if boss_tile:
            boss_monsters = [
                m
                for m in theme_def.monsters
                if m in ["Frazzlemaw", "Guzzlemaw", "Cloak Of Terror", "Vexclaw"]
            ] or (theme_def.monsters[:1] if theme_def.monsters else ["Demon"])
            boss_tile.spawn = Spawn(
                monster=boss_monsters[0],
                respawn=180,
                radius=7,
            )

        structure = Structure(
            name="boss_room",
            category="boss",
            x=bx,
            y=by,
            z=z,
            width=boss_size,
            height=boss_size,
            tile_count=boss_size * boss_size,
            tags=["dungeon", "boss"],
        )
        world.add_structure(structure)

        return {
            "x": bx,
            "y": by,
            "w": boss_size,
            "h": boss_size,
            "cx": boss_cx,
            "cy": boss_cy,
        }

    def _generate_exit(
        self,
        world: WorldModel,
        theme_def: ThemeDefinition,
        boss_room: Dict[str, int],
        z: int,
    ) -> None:
        """Generate the exit staircase near the boss room."""
        ex = boss_room["x"] + boss_room["w"] + 2
        ey = boss_room["y"] + boss_room["h"] // 2

        ground_id = theme_def.grounds[0] if theme_def.grounds else 396

        for x in range(ex - 1, ex + 2):
            for y in range(ey - 1, ey + 2):
                tile = Tile(x=x, y=y, z=z, ground=ground_id)
                tile.zone = "exit"
                # Add staircase up item (ID 138 — typical staircase up)
                tile.items.append({"id": 138})
                world.set_tile(tile)

        structure = Structure(
            name="exit",
            category="exit",
            x=ex - 1,
            y=ey - 1,
            z=z,
            width=3,
            height=3,
            tile_count=9,
            tags=["dungeon"],
        )
        world.add_structure(structure)
