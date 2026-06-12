from __future__ import annotations

from typing import Any, Dict, List, Tuple

from .blueprint import Blueprint, BlueprintTile


class ValidationError(Exception):
    """Raised when a blueprint fails validation."""


class ValidationResult:
    """Result of validating a blueprint."""

    def __init__(self, blueprint_name: str):
        self.blueprint_name = blueprint_name
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
        lines = [f"Blueprint '{self.blueprint_name}': {status}"]
        if self.warnings:
            lines.append(f"  Warnings ({len(self.warnings)}):")
            for w in self.warnings:
                lines.append(f"    - {w}")
        if self.errors:
            lines.append(f"  Errors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"    - {e}")
        return "\n".join(lines)


class BlueprintValidator:
    """
    Validates blueprints for correctness and consistency.

    Checks:
      - Valid size (positive, reasonable bounds)
      - Valid tiles (coordinates within bounds, no negatives)
      - Valid item IDs (if AssetRegistry provided)
      - Valid spawn entries (if AssetRegistry provided)
      - Valid entry point (within bounds)
      - Tile uniqueness (no duplicate coordinates)

    Usage:
        validator = BlueprintValidator(asset_registry)
        result = validator.validate(blueprint)
        if not result:
            print(result.summary())
    """

    # Maximum reasonable blueprint size
    MAX_SIZE = 256
    # Maximum reasonable tile count
    MAX_TILES = 65536

    def __init__(self, asset_registry: Any = None):
        """
        Args:
            asset_registry: Optional AssetRegistry instance to validate
                            item IDs and monster names against.
        """
        self._asset_registry = asset_registry

    # ------------------------------------------------------------------
    # Main validation
    # ------------------------------------------------------------------

    def validate(self, blueprint: Blueprint) -> ValidationResult:
        """
        Run all validation checks on a blueprint.

        Args:
            blueprint: The Blueprint instance to validate.

        Returns:
            ValidationResult with pass/fail status and messages.
        """
        result = ValidationResult(blueprint.name)

        self._validate_name(blueprint, result)
        self._validate_size(blueprint, result)
        self._validate_tiles(blueprint, result)
        self._validate_entry(blueprint, result)
        self._validate_features(blueprint, result)
        self._validate_metadata(blueprint, result)
        self._validate_rooms(blueprint, result)
        self._validate_grounds(blueprint, result)

        return result

    def validate_batch(
        self, blueprints: List[Blueprint]
    ) -> Dict[str, ValidationResult]:
        """Validate multiple blueprints. Returns dict of name -> result."""
        return {bp.name: self.validate(bp) for bp in blueprints}

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------

    def _validate_name(self, bp: Blueprint, result: ValidationResult) -> None:
        """Check that the blueprint has a valid name."""
        if not bp.name or not bp.name.strip():
            result.add_error("Blueprint name is empty or missing")
        elif len(bp.name) > 128:
            result.add_error(f"Blueprint name too long ({len(bp.name)} chars, max 128)")

    def _validate_size(self, bp: Blueprint, result: ValidationResult) -> None:
        """Check that blueprint dimensions are valid."""
        w, h = bp.size

        if w <= 0 or h <= 0:
            result.add_error(f"Invalid size [{w}, {h}]: dimensions must be positive")
            return

        if w > self.MAX_SIZE or h > self.MAX_SIZE:
            result.add_warning(
                f"Large blueprint size [{w}, {h}] (max recommended: {self.MAX_SIZE}x{self.MAX_SIZE})"
            )

        if bp.is_tile_based:
            # Check that no tile exceeds the declared size
            for tile in bp.tiles:
                if tile.x >= w or tile.y >= h:
                    result.add_error(
                        f"Tile [{tile.x}, {tile.y}] exceeds declared size [{w}, {h}]"
                    )
                if tile.x < 0 or tile.y < 0:
                    result.add_error(
                        f"Tile has negative coordinates [{tile.x}, {tile.y}]"
                    )

    def _validate_tiles(self, bp: Blueprint, result: ValidationResult) -> None:
        """Check tile validity and uniqueness."""
        if not bp.is_tile_based:
            return

        tiles = bp.tiles
        if len(tiles) > self.MAX_TILES:
            result.add_error(f"Too many tiles ({len(tiles)}, max {self.MAX_TILES})")
            return

        # Check each tile
        for i, tile in enumerate(tiles):
            if not isinstance(tile, BlueprintTile):
                result.add_error(f"Tile at index {i} is not a BlueprintTile instance")
                continue
            if tile.ground == 0:
                result.add_warning(
                    f"Tile [{tile.x}, {tile.y}] has ground=0 (no ground set)"
                )
            self._validate_tile_items(tile, i, result)

        # Check for duplicate coordinates
        seen: set[Tuple[int, int]] = set()
        for tile in tiles:
            key = (tile.x, tile.y)
            if key in seen:
                result.add_warning(f"Duplicate tile at [{tile.x}, {tile.y}]")
            seen.add(key)

    def _validate_tile_items(
        self, tile: BlueprintTile, index: int, result: ValidationResult
    ) -> None:
        """Validate items and spawn on a single tile."""
        if self._asset_registry is None:
            return

        if tile.ground != 0:
            item_name = self._asset_registry.get_item_name(tile.ground)
            if item_name is None:
                result.add_warning(
                    f"Tile [{tile.x}, {tile.y}] (index {index}): ground ID {tile.ground} not found in asset registry"
                )

        if tile.item is not None:
            item_name = self._asset_registry.get_item_name(tile.item)
            if item_name is None:
                result.add_warning(
                    f"Tile [{tile.x}, {tile.y}] (index {index}): item ID {tile.item} not found in asset registry"
                )

        if tile.spawn is not None:
            monster_name = tile.spawn.get("name", "")
            if monster_name and self._asset_registry.get_monsters():
                monsters = self._asset_registry.get_monsters()
                if monster_name not in monsters:
                    result.add_warning(
                        f"Tile [{tile.x}, {tile.y}]: spawn monster '{monster_name}' not in known monsters list"
                    )

    def _validate_entry(self, bp: Blueprint, result: ValidationResult) -> None:
        """Check that entry point is valid."""
        if bp.entry is None:
            # Entry is optional - just warn
            result.add_warning("No entry point defined (entry field missing)")
            return

        ex, ey = bp.entry
        w, h = bp.size

        if ex < 0 or ey < 0:
            result.add_error(f"Entry point [{ex}, {ey}] has negative coordinates")
        elif ex >= w or ey >= h:
            result.add_error(
                f"Entry point [{ex}, {ey}] is outside blueprint bounds [{w}, {h}]"
            )

    def _validate_features(self, bp: Blueprint, result: ValidationResult) -> None:
        """Validate features if present (descriptive mode)."""
        for i, feature in enumerate(bp.features):
            pos = feature.get("position")
            if pos and len(pos) == 2:
                x, y = pos
                if x < 0 or y < 0:
                    result.add_warning(f"Feature {i} has negative position [{x}, {y}]")
                elif x >= bp.width or y >= bp.height:
                    result.add_warning(
                        f"Feature {i} position [{x}, {y}] outside blueprint bounds"
                    )

            # Validate item_id if present and registry is available
            item_id = feature.get("item_id")
            if item_id is not None and self._asset_registry is not None:
                item_name = self._asset_registry.get_item_name(item_id)
                if item_name is None:
                    result.add_warning(
                        f"Feature {i}: item_id {item_id} not found in asset registry"
                    )

    def _validate_metadata(self, bp: Blueprint, result: ValidationResult) -> None:
        """Validate metadata fields."""
        meta = bp.metadata
        if not meta.style and not bp.theme:
            result.add_warning("No style or theme defined")

        if bp.version:
            parts = bp.version.split(".")
            if len(parts) != 3:
                result.add_warning(f"Unusual version format: '{bp.version}'")
            for p in parts:
                if not p.isdigit():
                    result.add_warning(f"Version part '{p}' is not numeric")

    def _validate_rooms(self, bp: Blueprint, result: ValidationResult) -> None:
        """Validate rooms if present (descriptive mode)."""
        for i, room in enumerate(bp.rooms):
            pos = room.get("position")
            size = room.get("size")
            if pos and len(pos) == 2:
                x, y = pos
                if x < 0 or y < 0:
                    result.add_warning(f"Room {i} has negative position [{x}, {y}]")
            if size and len(size) == 2:
                sw, sh = size
                if sw <= 0 or sh <= 0:
                    result.add_warning(f"Room {i} has non-positive size [{sw}, {sh}]")

    def _validate_grounds(self, bp: Blueprint, result: ValidationResult) -> None:
        """Validate ground IDs if present and registry is available."""
        if not bp.grounds or self._asset_registry is None:
            return

        for gid in bp.grounds:
            item_name = self._asset_registry.get_item_name(gid)
            if item_name is None:
                result.add_warning(f"Ground ID {gid} not found in asset registry")
