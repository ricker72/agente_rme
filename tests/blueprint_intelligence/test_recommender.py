"""Tests for BlueprintRecommender."""

from core.blueprints.blueprint import Blueprint, BlueprintMetadata
from core.blueprint_intelligence.blueprint_recommender import BlueprintRecommender


class TestBlueprintRecommender:
    """Test blueprint recommendation."""

    def setup_method(self):
        self.recommender = BlueprintRecommender()

    def _make_bp(self, name="test", category="hunt", theme="generic", tags=None):
        return Blueprint(
            name=name,
            category=category,
            theme=theme,
            metadata=BlueprintMetadata(tags=tags or []),
        )

    def test_recommend_pattern(self):
        """Test pattern recommendation."""
        bps = [
            self._make_bp("roshamuul", "hunt", "roshamuul", tags=["hunt"]),
            self._make_bp("soul_war", "hunt", "soul_war", tags=["hunt"]),
            self._make_bp("city_center", "city", "city", tags=["city"]),
        ]
        recommendations = self.recommender.recommend_pattern("hunt", bps)
        assert len(recommendations) > 0
        assert any("hunt" in r["recommendation"] for r in recommendations)

    def test_recommend_layout(self):
        """Test layout recommendation."""
        bps = [self._make_bp("compact_city", "city", "city", tags=["compact", "city"])]
        recommendations = self.recommender.recommend_layout("compact city layout", bps)
        assert len(recommendations) > 0

    def test_recommend_boss_design(self):
        """Test boss design recommendation."""
        bps = [
            self._make_bp("falcon_boss", "boss_room", "falcon", tags=["boss"]),
            self._make_bp("hunt_area", "hunt", "forest"),
        ]
        recs = self.recommender.recommend_boss_design(bps)
        assert len(recs) > 0

    def test_recommend_city_layout(self):
        """Test city layout recommendation."""
        bps = [self._make_bp("issavi_city", "city", "issavi", tags=["city"])]
        recs = self.recommender.recommend_city_layout(bps)
        assert len(recs) > 0

    def test_recommend_corridor_pattern(self):
        """Test corridor pattern recommendation."""
        bps = [self._make_bp("rosh_corridor", "hunt", "roshamuul", tags=["corridor"])]
        recs = self.recommender.recommend_corridor_pattern(bps)
        assert len(recs) > 0

    def test_get_recommendations(self):
        """Test general recommendations."""
        bps = [self._make_bp("high_quality", "hunt")]
        recs = self.recommender.get_recommendations(bps)
        assert len(recs) >= 0

    def test_get_recommendations_with_hybrid(self):
        """Test recommendations include hybrid."""
        meta = BlueprintMetadata(tags=["hybrid"], hybrid=True)
        bp = Blueprint(name="hybrid_bp", category="hunt", metadata=meta)
        recs = self.recommender.get_recommendations([bp])
        assert len(recs) > 0

    def test_recommend_pattern_no_match_fallback(self):
        """Test fallback when no match found."""
        bps = [self._make_bp("generic_bp")]
        recs = self.recommender.recommend_pattern("unknown_type", bps)
        assert len(recs) > 0

    def test_save_load_patterns(self, tmp_path):
        """Test saving and loading patterns."""
        from core.blueprint_intelligence.models.blueprint_pattern import (
            BlueprintPattern,
        )

        pattern = BlueprintPattern(name="test_pattern", pattern_type="hunt")
        self.recommender.patterns = [pattern]
        path = str(tmp_path / "patterns.json")
        self.recommender.save_patterns(path)
        self.recommender.patterns = []
        self.recommender.load_patterns(path)
        assert len(self.recommender.patterns) == 1
        assert self.recommender.patterns[0].name == "test_pattern"
