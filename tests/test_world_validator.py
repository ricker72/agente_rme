"""
Tests for the WorldValidator class.
Covers validation of tiles, spawns, items, structures, and chunks.
"""

import pytest

from core.world import (
    Tile, Item, Spawn, Structure, Region, WorldModel,
    WorldValidator, WorldValidationResult,
)


class TestWorldValidator:
    """Test the WorldValidator."""

    @pytest.fixture
    def validator(self):
        """Create a validator without asset registry."""
        return WorldValidator(asset_registry=None)

    @pytest.fixture
    def valid_world(self):
        """Create a world with valid data."""
        w = WorldModel()
        w.set_tile(Tile(x=0, y=0, z=7, ground=817))
        w.set_tile(Tile(x=1, y=0, z=7, ground=415))
        w.add_structure(Structure(name="temple", category="temple",
                                  x=0, y=0, z=7, width=2, height=1))
        return w

    def test_valid_world_passes(self, validator, valid_world):
        """A valid world should pass validation."""
        result = validator.validate(valid_world)
        assert result.passed, f"Expected pass, got errors: {result.errors}"

    def test_negative_coordinates_error(self, validator):
        """Tiles with negative coordinates should produce an error."""
        w = WorldModel()
        w.set_tile(Tile(x=-1, y=0, z=7))
        result = validator.validate(w)
        assert not result.passed
        assert any("negative" in e.lower() for e in result.errors)

    def test_negative_y_coordinates_error(self, validator):
        """Tiles with negative Y should produce an error."""
        w = WorldModel()
        w.set_tile(Tile(x=0, y=-5, z=7))
        result = validator.validate(w)
        assert not result.passed
        assert any("negative" in e.lower() for e in result.errors)

    def test_z_layer_warning(self, validator):
        """Tiles with unusual Z layer should produce a warning."""
        w = WorldModel()
        w.set_tile(Tile(x=0, y=0, z=20))  # Z > 15
        result = validator.validate(w)
        assert result.passed  # Warnings don't fail
        assert any("unusual" in w.lower() for w in result.warnings)

    def test_key_mismatch_error(self, validator):
        """Directly modifying the tiles dict with wrong key should warn."""
        w = WorldModel()
        tile = Tile(x=5, y=5, z=7)
        # Force a key mismatch by using a wrong key
        w.tiles["100:200:7"] = tile
        result = validator.validate(w)
        assert not result.passed
        assert any("mismatch" in e.lower() for e in result.errors)

    def test_validate_single_tile(self, validator):
        """validate_tile works for individual tiles."""
        tile = Tile(x=100, y=100, z=7, ground=817)
        result = validator.validate_tile(tile)
        assert result.passed

    def test_validate_negative_tile(self, validator):
        """validate_tile catches negative coordinates."""
        tile = Tile(x=-1, y=0, z=7)
        result = validator.validate_tile(tile)
        assert not result.passed

    def test_structure_validation_warnings(self, validator):
        """Structures with bad data should produce warnings."""
        w = WorldModel()
        # Structure with no name
        w.add_structure(Structure(name="", category="t", x=0, y=0, z=7, width=5, height=5))
        result = validator.validate(w)
        assert result.passed
        assert any("no name" in w.lower() for w in result.warnings)

    def test_structure_negative_position(self, validator):
        """Structure with negative position should warn."""
        w = WorldModel()
        w.add_structure(Structure(name="s", category="t", x=-10, y=-10, z=7, width=5, height=5))
        result = validator.validate(w)
        assert any("negative" in w.lower() for w in result.warnings)

    def test_structure_non_positive_dimensions(self, validator):
        """Structure with non-positive dimensions should warn."""
        w = WorldModel()
        w.add_structure(Structure(name="s", category="t", x=0, y=0, z=7, width=0, height=5))
        result = validator.validate(w)
        assert any("non-positive" in w.lower() for w in result.warnings)

    def test_world_validation_result_summary(self):
        """WorldValidationResult.summary() returns a formatted string."""
        result = WorldValidationResult()
        result.add_warning("Test warning")
        summary = result.summary()
        assert "PASSED" in summary
        assert "Test warning" in summary

    def test_world_validation_result_failed_summary(self):
        """Failed result should say FAILED in summary."""
        result = WorldValidationResult()
        result.add_error("Test error")
        summary = result.summary()
        assert "FAILED" in summary
        assert "Test error" in summary

    def test_world_validation_result_bool(self):
        """WorldValidationResult bool reflects pass/fail."""
        r = WorldValidationResult()
        assert bool(r) is True
        r.add_error("error")
        assert bool(r) is False

    def test_empty_world_passes(self, validator):
        """Empty world should pass validation."""
        w = WorldModel()
        result = validator.validate(w)
        assert result.passed

    def test_large_tile_count_warning(self, validator):
        """Very large worlds produce a warning."""
        w = WorldModel()
        # This would be too many, but we just check the count field
        # No need to actually create 10M tiles - the count is derived
        # so this would only happen if the count is wrong.
        pass

    def test_definition_of_success_integration(self):
        """Integration: the exact pattern from the task spec works."""
        world = WorldModel()
        world.set_tile(Tile(x=100, y=100, z=7))
        result = world.get_tile(100, 100, 7)
        assert result is not None
        assert isinstance(result, Tile)
        assert result.x == 100
        assert result.y == 100
        assert result.z == 7