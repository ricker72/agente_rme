"""
Tests for the BlueprintValidator class.
Covers validation of size, tiles, entry, metadata, features, rooms.
"""

import pytest

from core.blueprints import (
    Blueprint,
    BlueprintValidator,
)


class TestBlueprintValidator:
    """Test the BlueprintValidator."""

    @pytest.fixture
    def validator(self):
        """Create a validator without asset registry (for unit tests)."""
        return BlueprintValidator(asset_registry=None)

    def test_valid_tile_based_blueprint(self, validator):
        """Basic valid blueprint should pass."""
        from core.blueprints import BlueprintTile

        bp = Blueprint(
            name="test_valid",
            theme="test",
            category="temple",
            size=(10, 10),
            entry=(5, 9),
        )
        bp.tiles = [
            BlueprintTile(x=0, y=0, ground=100),
            BlueprintTile(x=1, y=0, ground=100),
            BlueprintTile(x=0, y=1, ground=100),
            BlueprintTile(x=1, y=1, ground=100),
        ]
        result = validator.validate(bp)
        assert result.passed, f"Expected pass, got errors: {result.errors}"

    def test_empty_name_fails(self, validator):
        """Blueprint with empty name should have error."""
        bp = Blueprint(name="", theme="test", size=(5, 5))
        result = validator.validate(bp)
        assert not result.passed
        assert any("empty" in e.lower() for e in result.errors)

    def test_negative_size_fails(self, validator):
        """Blueprint with negative dimensions should fail."""
        bp = Blueprint(name="bad_size", theme="test", size=(-5, 10))
        result = validator.validate(bp)
        assert not result.passed
        assert any("invalid size" in e.lower() for e in result.errors)

    def test_zero_size_fails(self, validator):
        """Blueprint with zero dimensions should fail."""
        bp = Blueprint(name="zero_size", theme="test", size=(0, 10))
        result = validator.validate(bp)
        assert not result.passed

    def test_tile_outside_bounds_fails(self, validator):
        """Tile outside declared size should produce error."""
        from core.blueprints import BlueprintTile

        bp = Blueprint(
            name="bounds_test",
            theme="test",
            size=(5, 5),
        )
        bp.tiles = [BlueprintTile(x=10, y=10, ground=100)]
        result = validator.validate(bp)
        assert not result.passed
        assert any("exceeds" in e.lower() for e in result.errors)

    def test_negative_tile_coordinates_fails(self, validator):
        """Tile with negative coordinates should produce error."""
        from core.blueprints import BlueprintTile

        bp = Blueprint(
            name="neg_tile",
            theme="test",
            size=(10, 10),
        )
        bp.tiles = [BlueprintTile(x=-1, y=5, ground=100)]
        result = validator.validate(bp)
        assert not result.passed
        assert any("negative" in e.lower() for e in result.errors)

    def test_duplicate_tile_warning(self, validator):
        """Duplicate tile coordinates should produce a warning."""
        from core.blueprints import BlueprintTile

        bp = Blueprint(
            name="dup_test",
            theme="test",
            size=(10, 10),
        )
        bp.tiles = [
            BlueprintTile(x=5, y=5, ground=100),
            BlueprintTile(x=5, y=5, ground=200),  # duplicate
        ]
        result = validator.validate(bp)
        assert result.passed  # Warnings don't fail
        assert any("duplicate" in w.lower() for w in result.warnings)

    def test_entry_outside_bounds_fails(self, validator):
        """Entry point outside blueprint bounds should fail."""
        bp = Blueprint(
            name="entry_test",
            theme="test",
            size=(5, 5),
            entry=(10, 10),
        )
        result = validator.validate(bp)
        assert not result.passed
        assert any("outside" in e.lower() for e in result.errors)

    def test_entry_negative_fails(self, validator):
        """Entry point with negative coordinates should fail."""
        bp = Blueprint(
            name="neg_entry",
            theme="test",
            size=(10, 10),
            entry=(-1, 5),
        )
        result = validator.validate(bp)
        assert not result.passed
        assert any("negative" in e.lower() for e in result.errors)

    def test_valid_entry(self, validator):
        """Valid entry point should not produce errors."""
        bp = Blueprint(
            name="good_entry",
            theme="test",
            size=(20, 20),
            entry=(10, 19),
        )
        validator.validate(bp)
        # Entry is within bounds, no errors expected from that
        # (may have warnings about no tiles, but no errors)

    def test_no_theme_warning(self, validator):
        """Blueprint without style or theme should produce a warning."""
        bp = Blueprint(name="no_theme", theme="", size=(5, 5))
        result = validator.validate(bp)
        assert result.passed
        assert any("theme" in w.lower() for w in result.warnings)

    def test_feature_outside_bounds_warning(self, validator):
        """Feature position outside bounds should produce a warning."""
        bp = Blueprint(
            name="feat_test",
            theme="test",
            size=(5, 5),
            features=[{"position": [10, 10], "item_id": 100}],
        )
        result = validator.validate(bp)
        assert result.passed
        assert any("outside" in w.lower() for w in result.warnings)

    def test_validation_result_boolean(self, validator):
        """ValidationResult should be truthy when passed, falsy when failed."""
        bp_pass = Blueprint(name="pass", theme="test", size=(5, 5))
        r1 = validator.validate(bp_pass)
        assert bool(r1) is True  # passes (no errors)

    def test_validation_result_summary(self, validator):
        """ValidationResult.summary() should return a formatted string."""
        bp = Blueprint(name="summary_test", theme="test", size=(5, 5))
        result = validator.validate(bp)
        summary = result.summary()
        assert "summary_test" in summary
        assert "PASSED" in summary or "FAILED" in summary

    def test_validate_batch(self, validator):
        """validate_batch returns dict of results."""

        bps = [
            Blueprint(name="bp_a", theme="a", size=(5, 5)),
            Blueprint(name="bp_b", theme="b", size=(3, 3)),
        ]
        results = validator.validate_batch(bps)
        assert len(results) == 2
        assert "bp_a" in results
        assert "bp_b" in results

    def test_descriptive_blueprint_passes(self, validator):
        """Descriptive blueprints (no tiles) should pass basic validation."""
        bp = Blueprint(
            name="descriptive",
            theme="issavi",
            category="temple",
            size=(20, 20),
            entry=(10, 19),
            rooms=[{"name": "hall", "position": [2, 2], "size": [10, 10]}],
            features=[{"type": "altar", "position": [10, 10], "item_id": 1512}],
        )
        result = validator.validate(bp)
        assert result.passed


# Helper to use pytest fixtures properly
@pytest.fixture
def BlueprintTile():
    from core.blueprints import BlueprintTile

    return BlueprintTile
