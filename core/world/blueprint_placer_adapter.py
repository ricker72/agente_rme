"""
Adapter layer that bridges BlueprintPlacer with the new WorldModel.

This ensures the BlueprintPlacer from core/blueprints/ can place blueprints
into the unified WorldModel from core/world/.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

from core.world import Tile, Item, Spawn, Structure, WorldModel
from core.blueprints import Blueprint, BlueprintTile
from core.blueprints.blueprint_placer import BlueprintPlacer as BasePlacer


class UnifiedBlueprintPlacer(BasePlacer):
    """
    Enhanced BlueprintPlacer that places into the unified WorldModel.

    Usage:
        placer = UnifiedBlueprintPlacer()

        # Places tiles and registers the structure
        placer.place(temple, world=unified_world, x=1000, y=1000, z=7)
    """

    def place(
        self,
        blueprint: Blueprint,
        x: int = 0,
        y: int = 0,
        z: int = 7,
        world: Optional[WorldModel] = None,
        check_collision: bool = True,
        offset_x: int = 0,
        offset_y: int = 0,
    ) -> WorldModel:
        """
        Place a blueprint into the unified WorldModel.

        Args:
            blueprint: The Blueprint to place.
            x, y, z: World position.
            world: A WorldModel instance. If None, creates a new one.
            check_collision: If True, skip tiles that are already occupied.
            offset_x, offset_y: Optional offset inside the blueprint.

        Returns:
            The WorldModel with placed tiles and structure.
        """
        if world is None:
            world = WorldModel()

        self._place_count += 1

        if blueprint.is_tile_based:
            tiles_placed = self._place_tile_based(
                blueprint, world, x, y, z, check_collision, offset_x, offset_y,
            )
        else:
            tiles_placed = self._place_descriptive(
                blueprint, world, x, y, z, check_collision, offset_x, offset_y,
            )

        # Register the structure
        structure = Structure(
            name=blueprint.name,
            category=blueprint.category,
            x=x + offset_x,
            y=y + offset_y,
            z=z,
            width=blueprint.width,
            height=blueprint.height,
            tile_count=tiles_placed,
            tags=list(blueprint.tags),
        )
        world.add_structure(structure)

        return world

    # ------------------------------------------------------------------
    # Tile-based placement
    # ------------------------------------------------------------------

    def _place_tile_based(
        self,
        bp: Blueprint,
        world: WorldModel,
        base_x: int,
        base_y: int,
        z: int,
        check_collision: bool,
        offset_x: int,
        offset_y: int,
    ) -> int:
        """Place tile-based blueprint into unified WorldModel. Returns tile count."""
        tiles_placed = 0

        for bt in bp.tiles:
            wx = base_x + bt.x + offset_x
            wy = base_y + bt.y + offset_y

            # Collision check
            if check_collision and world.has_tile(wx, wy, z):
                continue

            tile = Tile(x=wx, y=wy, z=z, ground=bt.ground if bt.ground else None)

            # Add item
            if bt.item is not None:
                tile.items.append(Item(itemid=bt.item))

            # Add decoration as item
            if bt.decoration is not None:
                tile.items.append(Item(itemid=bt.decoration))

            # Add spawn
            if bt.spawn is not None:
                tile.spawn = Spawn.from_dict(bt.spawn)

            # Determine zone from category
            tile.zone = bp.category

            world.set_tile(tile)
            tiles_placed += 1

        return tiles_placed

    # ------------------------------------------------------------------
    # Descriptive placement
    # ------------------------------------------------------------------

    def _place_descriptive(
        self,
        bp: Blueprint,
        world: WorldModel,
        base_x: int,
        base_y: int,
        z: int,
        check_collision: bool,
        offset_x: int,
        offset_y: int,
    ) -> int:
        """Place descriptive blueprint into unified WorldModel. Returns tile count."""
        tiles_placed = 0

        w, h = bp.size
        ground_ids = bp.grounds or [0]

        for iy in range(h):
            for ix in range(w):
                wx = base_x + ix + offset_x
                wy = base_y + iy + offset_y

                if check_collision and world.has_tile(wx, wy, z):
                    continue

                gid = ground_ids[(ix + iy) % len(ground_ids)]
                tile = Tile(x=wx, y=wy, z=z, ground=gid if gid else None)
                tile.zone = bp.category
                world.set_tile(tile)
                tiles_placed += 1

        # Place features
        for feature in bp.features:
            pos = feature.get("position")
            if not pos or len(pos) != 2:
                continue
            fx, fy = pos
            wx = base_x + fx + offset_x
            wy = base_y + fy + offset_y

            tile = world.get_tile(wx, wy, z)
            if tile is None:
                tile = Tile(x=wx, y=wy, z=z)
                world.set_tile(tile)

            item_id = feature.get("item_id")
            if item_id is not None:
                tile.items.append(Item(itemid=item_id))

            monster = feature.get("monster")
            if monster is not None:
                tile.spawn = Spawn(monster=monster)

        return tiles_placed