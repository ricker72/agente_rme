"""Tests for pattern mining (integrated in BlueprintIntelligenceEngine)."""

from core.blueprints.blueprint import Blueprint, BlueprintMetadata
from core.blueprint_intelligence.blueprint_intelligence_engine import (
    BlueprintIntelligenceEngine,
)


class TestPatternMiner:
    """Test pattern mining functionality."""

    def setup_method(self):
        self.engine = BlueprintIntelligenceEngine()

    def _make_bp(self, name="test", category="hunt", tags=None):
        return Blueprint(
            name=name,
            category=category,
            metadata=BlueprintMetadata(tags=tags or [category]),
        )

    def test_mine_city_patterns(self):
        """Test mining city patterns."""
        bps = [
            self._make_bp("issavi", "city", ["city"]),
            self._make_bp("venore", "city", ["city"]),
        ]
        self.engine.load_blueprints(bps)
        patterns = self.engine.mine_patterns()
        city_patterns = [p for p in patterns if p.pattern_type == "city"]
        assert len(city_patterns) == 1

    def test_mine_hunt_patterns(self):
        """Test mining hunt patterns."""
        bps = [
            self._make_bp("roshamuul", "hunt", ["hunt"]),
            self._make_bp("soul_war", "hunt", ["hunt"]),
        ]
        self.engine.load_blueprints(bps)
        patterns = self.engine.mine_patterns()
        hunt_patterns = [p for p in patterns if p.pattern_type == "hunt"]
        assert len(hunt_patterns) == 1

    def test_mine_boss_patterns(self):
        """Test mining boss patterns."""
        bps = [
            self._make_bp("falcon_boss", "boss_room", ["boss"]),
        ]
        self.engine.load_blueprints(bps)
        patterns = self.engine.mine_patterns()
        boss_patterns = [p for p in patterns if p.pattern_type == "boss"]
        assert len(boss_patterns) == 1

    def test_mine_multiple_patterns(self):
        """Test mining multiple pattern types."""
        bps = [
            self._make_bp("city_bp", "city", ["city"]),
            self._make_bp("hunt_bp", "hunt", ["hunt"]),
            self._make_bp("boss_bp", "boss_room", ["boss"]),
        ]
        self.engine.load_blueprints(bps)
        patterns = self.engine.mine_patterns()
        types = {p.pattern_type for p in patterns}
        assert "city" in types
        assert "hunt" in types

    def test_mine_patterns_empty(self):
        """Test mining with no blueprints."""
        patterns = self.engine.mine_patterns()
        assert len(patterns) == 0


class TestClusterEngine:
    """Test clustering functionality."""

    def setup_method(self):
        self.engine = BlueprintIntelligenceEngine()

    def _make_bp(self, name="test", category="hunt"):
        return Blueprint(
            name=name,
            category=category,
            metadata=BlueprintMetadata(tags=[category]),
        )

    def test_cluster_by_category(self):
        """Test clustering blueprints by category."""
        bps = [
            self._make_bp("roshamuul", "hunt"),
            self._make_bp("soul_war", "hunt"),
            self._make_bp("issavi", "city"),
        ]
        self.engine.load_blueprints(bps)
        clusters = self.engine.cluster()
        categories = {c.dominant_category for c in clusters}
        assert "hunt" in categories
        assert "city" in categories

    def test_cluster_empty(self):
        """Test clustering with no blueprints."""
        clusters = self.engine.cluster()
        assert len(clusters) == 0

    def test_cluster_single_blueprint(self):
        """Test clustering a single blueprint."""
        bp = self._make_bp("lonely", "hunt")
        self.engine.load_blueprints([bp])
        clusters = self.engine.cluster()
        assert len(clusters) == 1
        assert clusters[0].size == 1

    def test_cluster_centroid(self):
        """Test cluster centroid calculation."""
        bps = [self._make_bp(f"bp_{i}", "hunt") for i in range(3)]
        self.engine.load_blueprints(bps)
        self.engine.build_embeddings()
        clusters = self.engine.cluster()
        hunt_cluster = [c for c in clusters if c.dominant_category == "hunt"]
        if hunt_cluster:
            assert len(hunt_cluster[0].centroid) == 12
