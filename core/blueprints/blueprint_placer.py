from __future__ import annotations

import logging
from typing import Any, List, Tuple

from .blueprint import Blueprint

logger = logging.getLogger(__name__)


class BlueprintPlacerError(Exception):
    """Raised when a blueprint cannot be placed."""


class BlueprintPlacer:
    """
    Places a Blueprint into a WorldModel at a given (x, y, z) coordinate.

    Supports both:
      - Tile-based blueprints (with explicit tiles list)
      - Descriptive blueprints (with rooms, features, grounds, etc.)

    Descriptive blueprints are expanded into tiles on-the-fly during placement.

    Usage:
        placer = BlueprintPlacer()
        placer.place(blueprint, x=1000, y=1000, z=7)

        # With collision detection:
        success = placer.place(blueprint, x=1000, y=1000, z=7, world_model=world)
        if not success:
            print("Area occupied!")
    """

    def __init__(self):
        self._place_count = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def place(
        self,
        blueprint: Blueprint,
        x: int = 0,
        y: int = 0,
        z: int = 7,
        world_model: Any = None,
        check_collision: bool = True,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> Any:
        """
        Place a blueprint into a WorldModel at the given position.

        Args:
            blueprint: The Blueprint to place.
            x: Base X coordinate (world position).
            y: Base Y coordinate (world position).
            z: Z layer (floor).
            world_model: A WorldModel instance. If None, creates a new one.
            check_collision: If True, skip tiles that are already occupied.
            offset_x: Optional offset inside the blueprint (for partial placement).
            offset_y: Optional offset inside the blueprint (for partial placement).

        Returns:
            The WorldModel with placed tiles.

        Raises:
            BlueprintPlacerError: If placement fails.
        """
        self._place_count += 1

        if world_model is None:
            from core.world_engine.world_engine import WorldModel

            world_model = WorldModel()

        if blueprint.is_tile_based:
            self._place_tile_based(
                blueprint,
                world_model,
                x,
                y,
                z,
                check_collision,
                offset_x,
                offset_y,
            )
        else:
            self._place_descriptive(
                blueprint,
                world_model,
                x,
                y,
                z,
                check_collision,
                offset_x,
                offset_y,
            )

        return world_model

    def place_batch(
        self,
        blueprints: List[Tuple[Blueprint, int, int, int]],
        world_model: Any = None,
        check_collision: bool = True,
    ) -> Any:
        """
        Place multiple blueprints at once.

        Args:
            blueprints: List of (blueprint, x, y, z) tuples.
            world_model: Optional existing WorldModel.
            check_collision: Whether to check for collisions.

        Returns:
            WorldModel with all blueprints placed.
        """
        if world_model is None:
            from core.world_engine.world_engine import WorldModel

            world_model = WorldModel()

        for bp, bx, by, bz in blueprints:
            self.place(
                bp,
                x=bx,
                y=by,
                z=bz,
                world_model=world_model,
                check_collision=check_collision,
            )

        return world_model

    # ------------------------------------------------------------------
    # Tile-based placement
    # ------------------------------------------------------------------

    def _place_tile_based(
        self,
        bp: Blueprint,
        world_model: Any,
        base_x: int,
        base_y: int,
        z: int,
        check_collision: bool,
        offset_x: int,
        offset_y: int,
    ) -> None:
        """Place a tile-based blueprint into the world model."""
        from core.world_engine.world_engine import Tile

        tiles_placed = 0
        tiles_skipped = 0

        for bt in bp.tiles:
            wx = base_x + bt.x + offset_x
            wy = base_y + bt.y + offset_y
            key = f"{wx}:{wy}:{z}"

            # Collision check
            if check_collision and key in world_model.tiles:
                tiles_skipped += 1
                continue

            tile = Tile(
                x=wx,
                y=wy,
                z=z,
                ground=str(bt.ground) if bt.ground else "0",
                items=[],
                decorations=[],
            )

            # Add items
            if bt.item is not None:
                tile.items.append({"id": bt.item})

            # Add decorations
            if bt.decoration is not None:
                tile.decorations.append(str(bt.decoration))

            # Add spawn
            if bt.spawn is not None:
                tile.spawn = bt.spawn

            world_model.add_tile(tile)
            tiles_placed += 1

        bp.tile_count if hasattr(bp, "tile_count") else len(bp.tiles)
        logger.info(
            f"Placed '{bp.name}' at ({base_x},{base_y},z={z}): {tiles_placed}/{tiles_placed + tiles_skipped} tiles"
        )

    # ------------------------------------------------------------------
    # Descriptive (non-tile) placement
    # ------------------------------------------------------------------

    def _place_descriptive(
        self,
        bp: Blueprint,
        world_model: Any,
        base_x: int,
        base_y: int,
        z: int,
        check_collision: bool,
        offset_x: int,
        offset_y: int,
    ) -> None:
        """Place a descriptive blueprint by expanding rooms/features into tiles."""
        from core.world_engine.world_engine import Tile

        w, h = bp.size
        tiles_placed = 0
        tiles_skipped = 0

        # Build a ground layer from the grounds list
        ground_ids = bp.grounds or [0]

        # Determine which ground to use (cycle through if multiple)
        for iy in range(h):
            for ix in range(w):
                wx = base_x + ix + offset_x
                wy = base_y + iy + offset_y
                key = f"{wx}:{wy}:{z}"

                if check_collision and key in world_model.tiles:
                    tiles_skipped += 1
                    continue

                # Pick a ground ID (cycle through available)
                gid = ground_ids[(ix + iy) % len(ground_ids)]

                tile = Tile(
                    x=wx,
                    y=wy,
                    z=z,
                    ground=str(gid),
                    items=[],
                    decorations=[],
                )

                world_model.add_tile(tile)
                tiles_placed += 1

        # Place features (decorative items)
        for feature in bp.features:
            pos = feature.get("position")
            if not pos or len(pos) != 2:
                continue
            fx, fy = pos
            wx = base_x + fx + offset_x
            wy = base_y + fy + offset_y
            key = f"{wx}:{wy}:{z}"

            tile = world_model.tiles.get(key)
            if tile is None:
                tile = Tile(x=wx, y=wy, z=z, ground="0")
                world_model.add_tile(tile)

            item_id = feature.get("item_id")
            if item_id is not None:
                tile.items.append({"id": item_id, **feature.get("attributes", {})})

            monster = feature.get("monster")
            if monster is not None:
                tile.spawn = {"name": monster, **feature.get("spawn_attributes", {})}

        # Place entry point as a special tile if defined
        if bp.entry is not None:
            ex, ey = bp.entry
            wx = base_x + ex + offset_x
            wy = base_y + ey + offset_y
            key = f"{wx}:{wy}:{z}"

            if key not in world_model.tiles:
                tile = Tile(x=wx, y=wy, z=z, ground="0")
                world_model.add_tile(tile)

        logger.info(
            f"Placed descriptive '{bp.name}' at ({base_x},{base_y},z={z}): "
            f"{tiles_placed} ground tiles, {len(bp.features)} features"
        )

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def get_place_count(self) -> int:
        """Return total number of place operations performed."""
        return self._place_count

    def create_world_model(self) -> Any:
        """Create a fresh WorldModel instance."""
        from core.world_engine.world_engine import WorldModel

        return WorldModel()
