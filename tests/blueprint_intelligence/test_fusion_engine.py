"""Tests for BlueprintFusionEngine."""

import pytest
from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from core.blueprint_intelligence.blueprint_fusion_engine import (
    BlueprintFusionEngine,
    _merge_list,
    _interleave_list,
)


class TestBlueprintFusionEngine:
    """Test blueprint fusion functionality."""

    def setup_method(self):
        self.engine = BlueprintFusionEngine()

    def _make_bp(self, name="test", category="hunt", tiles=None, rooms=None, zones=None, features=None, grounds=None):
        return Blueprint(
            name=name,
            category=category,
            tiles=tiles or [],
            rooms=rooms or [],
            zones=zones or [],
            features=features or [],
            grounds=grounds or [],
        )

    def test_fuse_weighted(self):
        """Test weighted fusion creates hybrid."""
        bp_a = self._make_bp("roshamuul", tiles=[
            BlueprintTile(x=0, y=0, ground=100),
            BlueprintTile(x=1, y=0, ground=100),
        ])
        bp_b = self._make_bp("soul_war", tiles=[
            BlueprintTile(x=0, y=0, ground=200),
            BlueprintTile(x=0, y=1, ground=200),
        ])
        result = self.engine.fuse(bp_a, bp_b, ratio=0.7)
        assert result.is_valid
        assert result.source_a == "roshamuul"
        assert result.source_b == "soul_war"
        assert result.fusion_ratio == 0.7
        assert result.blueprint is not None

    def test_fuse_interleave(self):
        """Test interleave fusion."""
        bp_a = self._make_bp("a", tiles=[BlueprintTile(x=0, y=0, ground=100)])
        bp_b = self._make_bp("b", tiles=[BlueprintTile(x=1, y=1, ground=200)])
        result = self.engine.fuse(bp_a, bp_b, ratio=0.5, method="interleave")
        assert result.is_valid
        assert result.fusion_method == "interleave"

    def test_fuse_blend(self):
        """Test blend fusion."""
        bp_a = self._make_bp("a", tiles=[BlueprintTile(x=0, y=0, ground=100)])
        bp_b = self._make_bp("b", tiles=[BlueprintTile(x=0, y=0, ground=200)])
        result = self.engine.fuse(bp_a, bp_b, ratio=0.5, method="blend")
        assert result.is_valid
        assert result.fusion_method == "blend"

    def test_fuse_ratio_clamping(self):
        """Test fusion ratio is clamped to [0, 1]."""
        bp_a = self._make_bp("a")
        bp_b = self._make_bp("b")
        result_high = self.engine.fuse(bp_a, bp_b, ratio=1.5)
        result_low = self.engine.fuse(bp_a, bp_b, ratio=-0.5)
        assert 0.0 <= result_high.fusion_ratio <= 1.0
        assert 0.0 <= result_low.fusion_ratio <= 1.0

    def test_fuse_custom_name(self):
        """Test custom name for hybrid."""
        bp_a = self._make_bp("a")
        bp_b = self._make_bp("b")
        result = self.engine.fuse(bp_a, bp_b, name="custom_hybrid")
        assert result.name == "custom_hybrid"

    def test_fuse_hybrid_category(self):
        """Test hybrid blueprint has hybrid category."""
        bp_a = self._make_bp("a")
        bp_b = self._make_bp("b")
        result = self.engine.fuse(bp_a, bp_b)
        assert result.blueprint is not None
        assert result.blueprint.category == "hybrid"

    def test_fuse_hybrid_metadata(self):
        """Test hybrid metadata includes both sources."""
        bp_a = self._make_bp("a", tiles=[BlueprintTile(x=0, y=0, ground=100)])
        bp_b = self._make_bp("b", tiles=[BlueprintTile(x=1, y=1, ground=200)])
        result = self.engine.fuse(bp_a, bp_b)
        assert result.blueprint is not None
        assert result.blueprint.metadata.hybrid is True

    def test_fuse_empty(self):
        """Test fusion with empty blueprints."""
        bp_a = self._make_bp("empty_a")
        bp_b = self._make_bp("empty_b")
        result = self.engine.fuse(bp_a, bp_b)
        assert result.is_valid
        assert result.blueprint is not None

    def test_merge_list_helper(self):
        """Test _merge_list helper function."""
        list_a = [1, 2, 3, 4, 5]
        list_b = [6, 7, 8, 9, 10]
        merged = _merge_list(list_a, list_b, 0.6)
        assert len(merged) == 5
        assert all(x in merged for x in merged)

    def test_interleave_list_helper(self):
        """Test _interleave_list helper function."""
        list_a = [1, 2, 3]
        list_b = [4, 5, 6]
        interleaved = _interleave_list(list_a, list_b)
        assert len(interleaved) == 6
        assert interleaved[0] == 1
        assert interleaved[1] == 4

    def test_interleave_list_uneven(self):
        """Test interleave with uneven lists."""
        list_a = [1, 2]
        list_b = [3, 4, 5]
        interleaved = _interleave_list(list_a, list_b)
        assert len(interleaved) == 5