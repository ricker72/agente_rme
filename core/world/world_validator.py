from __future__ import annotations

from typing import Any, List

from .tile import Tile
from .world_model import WorldModel


class WorldValidationResult:
    """Result of validating a WorldModel."""

    def __init__(self):
        self.passed: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.passed = False

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def __bool__(self) -> bool:
        return self.passed

    def summary(self) -> str:
        status = "PASSED" if self.passed else "FAILED"
        lines = [f"WorldModel validation: {status}"]
        if self.warnings:
            lines.append(f"  Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"    - {w}")
        if self.errors:
            lines.append(f"  Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"    - {e}")
        return "\n".join(lines)


class WorldValidator:
    """
    Validates the entire WorldModel for consistency and correctness.

    Checks:
      - Valid tile coordinates (no negatives, within reasonable bounds)
      - No duplicate tiles (no two tiles with same x:y:z key)
      - Valid spawns (monster names exist in asset registry if provided)
      - Valid items (item IDs exist in asset registry if provided)
      - Valid ground IDs (exist in asset registry if provided)
      - Structure integrity (bounds check)

    Usage:
        validator = WorldValidator(asset_registry)
        result = validator.validate(world_model)
        if not result:
            print(result.summary())
    """

    # Maximum reasonable coordinate values
    MAX_COORD = 65535
    MIN_COORD = 0

    def __init__(self, asset_registry: Any = None):
        """
        Args:
            asset_registry: Optional AssetRegistry to validate items/monsters.
        """
        self._asset_registry = asset_registry

    # ------------------------------------------------------------------
    # Main validation
    # ------------------------------------------------------------------

    def validate(self, world: WorldModel) -> WorldValidationResult:
        """Run all validation checks on a WorldModel."""
        result = WorldValidationResult()

        self._validate_tile_count(world, result)
        self._validate_tile_coordinates(world, result)
        self._validate_tile_keys(world, result)
        self._validate_spawns(world, result)
        self._validate_items(world, result)
        self._validate_structures(world, result)
        self._validate_chunks(world, result)

        return result

    def validate_tile(self, tile: Tile) -> WorldValidationResult:
        """Validate a single tile."""
        result = WorldValidationResult()
        self._check_tile_coords(tile, result)
        self._check_tile_items(tile, result)
        return result

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _validate_tile_count(
        self, world: WorldModel, result: WorldValidationResult
    ) -> None:
        """Check that the tile count is valid."""
        tc = world.tile_count()
        if tc < 0:
            result.add_error(f"Negative tile count: {tc}")
        if tc > 10_000_000:
            result.add_warning(f"Very large tile count: {tc}")

    def _validate_tile_coordinates(
        self, world: WorldModel, result: WorldValidationResult
    ) -> None:
        """Check that all tiles have valid coordinates."""
        for tile in world.tiles.values():
            self._check_tile_coords(tile, result)

    def _check_tile_coords(self, tile: Tile, result: WorldValidationResult) -> None:
        """Check a single tile's coordinates."""
        if tile.x < self.MIN_COORD:
            result.add_error(f"Tile at ({tile.x},{tile.y},z={tile.z}) has negative X")
        if tile.y < self.MIN_COORD:
            result.add_error(f"Tile at ({tile.x},{tile.y},z={tile.z}) has negative Y")
        if tile.z < 0 or tile.z > 15:
            result.add_warning(
                f"Tile at ({tile.x},{tile.y},z={tile.z}) has unusual Z layer"
            )
        if tile.x > self.MAX_COORD:
            result.add_warning(f"Tile at ({tile.x},{tile.y},z={tile.z}) exceeds max X")
        if tile.y > self.MAX_COORD:
            result.add_warning(f"Tile at ({tile.x},{tile.y},z={tile.z}) exceeds max Y")

    def _validate_tile_keys(
        self, world: WorldModel, result: WorldValidationResult
    ) -> None:
        """Verify tile dict keys match tile coordinates."""
        for key, tile in world.tiles.items():
            expected_key = tile.key
            if key != expected_key:
                result.add_error(
                    f"Tile key mismatch: dict key '{key}' but tile key is '{expected_key}'"
                )

    def _validate_spawns(
        self, world: WorldModel, result: WorldValidationResult
    ) -> None:
        """Validate spawns if asset registry is available."""
        if self._asset_registry is None:
            return

        monsters = self._asset_registry.get_monsters()
        if not monsters:
            return  # No monster data to compare against

        for tile in world.tiles.values():
            if tile.spawn is not None:
                name = (
                    tile.spawn.monster
                    if hasattr(tile.spawn, "monster")
                    else tile.spawn.get("name", "")
                )
                if name and name not in monsters:
                    result.add_warning(
                        f"Tile ({tile.x},{tile.y},z={tile.z}): spawn monster '{name}' not in asset registry"
                    )

    def _validate_items(self, world: WorldModel, result: WorldValidationResult) -> None:
        """Validate item IDs if asset registry is available."""
        if self._asset_registry is None:
            return

        for tile in world.tiles.values():
            self._check_tile_items(tile, result)

    def _check_tile_items(self, tile: Tile, result: WorldValidationResult) -> None:
        """Validate items on a single tile."""
        if self._asset_registry is None:
            return

        for item in tile.items:
            item_id = (
                item.itemid
                if hasattr(item, "itemid")
                else item.get("itemid", item.get("id", 0))
            )
            item_name = self._asset_registry.get_item_name(item_id)
            if item_name is None:
                result.add_warning(
                    f"Tile ({tile.x},{tile.y},z={tile.z}): item ID {item_id} not found in asset registry"
                )

    def _validate_structures(
        self, world: WorldModel, result: WorldValidationResult
    ) -> None:
        """Validate structures."""
        for i, s in enumerate(world.structures):
            if not s.name:
                result.add_warning(f"Structure at index {i} has no name")
            if s.width <= 0 or s.height <= 0:
                result.add_warning(
                    f"Structure '{s.name}' has non-positive dimensions ({s.width}x{s.height})"
                )
            if s.x < 0 or s.y < 0:
                result.add_warning(
                    f"Structure '{s.name}' has negative position ({s.x},{s.y})"
                )

    def _validate_chunks(
        self, world: WorldModel, result: WorldValidationResult
    ) -> None:
        """Validate chunk consistency."""
        for chunk in world.chunks.values():
            if chunk.chunk_size <= 0:
                result.add_warning(
                    f"Chunk ({chunk.chunk_x},{chunk.chunk_y}) has non-positive chunk size: {chunk.chunk_size}"
                )
