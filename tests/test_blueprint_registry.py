"""
Tests for the BlueprintRegistry class.
Covers the main API: get, list, by_theme, by_category, search, summary.
"""

import pytest
from pathlib import Path

from core.blueprints import BlueprintRegistry, Blueprint


class TestBlueprintRegistry:
    """Test the BlueprintRegistry query API."""

    @pytest.fixture
    def registry(self):
        """Create a registry pre-loaded with data blueprints."""
        reg = BlueprintRegistry()
        data_dir = Path(__file__).parent.parent / "data" / "blueprints"
        count = reg.load_all(data_dir)
        assert count > 0, f"No blueprints loaded from {data_dir}"
        return reg

    def test_get_existing(self, registry):
        """registry.get() returns a Blueprint for an existing name."""
        bp = registry.get("issavi_temple_small")
        assert bp is not None
        assert isinstance(bp, Blueprint)
        assert bp.name == "issavi_temple_small"
        assert bp.theme == "issavi"

    def test_get_missing(self, registry):
        """registry.get() returns None for a non-existent name."""
        bp = registry.get("nonexistent_blueprint_xyz")
        assert bp is None

    def test_list(self, registry):
        """registry.list() returns all blueprints."""
        all_bps = registry.list()
        assert len(all_bps) > 0
        assert all(isinstance(bp, Blueprint) for bp in all_bps)

    def test_by_theme_issavi(self, registry):
        """registry.by_theme('issavi') returns all Issavi blueprints."""
        issavi_bps = registry.by_theme("issavi")
        assert len(issavi_bps) > 0
        for bp in issavi_bps:
            assert bp.theme.lower() == "issavi"

    def test_by_theme_roshamuul(self, registry):
        """registry.by_theme('roshamuul') returns all Roshamuul blueprints."""
        rosha_bps = registry.by_theme("roshamuul")
        assert len(rosha_bps) > 0
        for bp in rosha_bps:
            assert bp.theme.lower() == "roshamuul"

    def test_by_theme_generic(self, registry):
        """registry.by_theme('generic') returns generic blueprints."""
        generic_bps = registry.by_theme("generic")
        assert len(generic_bps) > 0
        for bp in generic_bps:
            assert bp.theme.lower() == "generic"

    def test_by_category_temple(self, registry):
        """registry.by_category('temple') returns all temples."""
        temples = registry.by_category("temple")
        assert len(temples) >= 2  # issavi_temple_small + issavi_temple_large
        for bp in temples:
            assert bp.category.lower() == "temple"

    def test_by_category_bridge(self, registry):
        """registry.by_category('bridge') returns all bridges."""
        bridges = registry.by_category("bridge")
        assert len(bridges) >= 2  # issavi_bridge + stone_bridge
        for bp in bridges:
            assert bp.category.lower() == "bridge"

    def test_search_by_keyword(self, registry):
        """registry.search() finds blueprints matching keywords."""
        results = registry.search("market")
        assert len(results) >= 1
        assert any("market" in bp.name.lower() for bp in results)

        results2 = registry.search("roshamuul")
        assert len(results2) >= 2

    def test_names(self, registry):
        """registry.names() returns sorted blueprint names."""
        names = registry.names()
        assert len(names) > 0
        assert names == sorted(names)
        assert "issavi_temple_small" in names

    def test_count(self, registry):
        """registry.count() returns the number of blueprints."""
        assert registry.count() > 0
        assert registry.count() == len(registry.list())

    def test_summary(self, registry):
        """registry.summary() returns a structured summary."""
        summary = registry.summary()
        assert "total" in summary
        assert summary["total"] > 0
        assert "by_theme" in summary
        assert "by_category" in summary
        assert "issavi" in summary["by_theme"]
        assert "roshamuul" in summary["by_theme"]

    def test_register(self, registry):
        """registry.register() adds a new blueprint programmatically."""
        bp = Blueprint(name="test_bp", theme="test", category="test")
        registry.register(bp)
        loaded = registry.get("test_bp")
        assert loaded is not None
        assert loaded.name == "test_bp"
        assert loaded.theme == "test"

    def test_clear(self, registry):
        """registry.clear() removes all blueprints."""
        registry.clear()
        assert registry.count() == 0
        assert registry.list() == []
