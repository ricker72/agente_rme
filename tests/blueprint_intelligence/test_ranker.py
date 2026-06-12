"""Tests for BlueprintRanker."""

from core.blueprints.blueprint import Blueprint, BlueprintMetadata
from core.blueprint_intelligence.blueprint_ranker import BlueprintRanker


class TestBlueprintRanker:
    """Test blueprint ranking."""

    def setup_method(self):
        self.ranker = BlueprintRanker()

    def _make_bp(self, name="test", category="hunt", tiles=None, tags=None, raw=None):
        return Blueprint(
            name=name,
            category=category,
            tiles=tiles or [],
            metadata=BlueprintMetadata(tags=tags or []),
            _raw=raw or {},
        )

    def test_rank_single(self):
        """Test ranking a single blueprint."""
        bp = self._make_bp(
            "test_hunt", raw={"critic_score": 80.0, "playtest_score": 70.0}
        )
        ranked = self.ranker.rank_single(bp)
        assert ranked.blueprint_name == "test_hunt"
        assert ranked.overall_rank > 0.0
        assert ranked.critic_score > 0.0

    def test_rank_multiple(self):
        """Test ranking multiple blueprints."""
        bps = [
            self._make_bp("bp_a", raw={"critic_score": 90.0, "playtest_score": 85.0}),
            self._make_bp("bp_b", raw={"critic_score": 70.0, "playtest_score": 65.0}),
            self._make_bp("bp_c", raw={"critic_score": 50.0, "playtest_score": 45.0}),
        ]
        ranked = self.ranker.rank(bps)
        assert len(ranked) == 3
        assert ranked[0].critic_score >= ranked[1].critic_score

    def test_rank_top_k(self):
        """Test ranking with top_k limit."""
        bps = [
            self._make_bp(f"bp_{i}", raw={"critic_score": float(100 - i * 10)})
            for i in range(10)
        ]
        ranked = self.ranker.rank(bps, top_k=3)
        assert len(ranked) == 3

    def test_rank_reuse_score(self):
        """Test reuse score calculation."""
        bp_reusable = self._make_bp("reusable", tags=["hybrid", "template"])
        bp_normal = self._make_bp("normal")
        ranked_reusable = self.ranker.rank_single(bp_reusable)
        ranked_normal = self.ranker.rank_single(bp_normal)
        assert ranked_reusable.reuse_score > ranked_normal.reuse_score

    def test_rank_knowledge_score(self):
        """Test knowledge score calculation."""
        bp = self._make_bp("knowledge_test")
        ranked = self.ranker.rank_single(bp)
        assert ranked.knowledge_score >= 0.0

    def test_rank_complexity_score(self):
        """Test complexity score calculation."""
        bp = self._make_bp("simple")
        ranked = self.ranker.rank_single(bp)
        assert ranked.complexity_score >= 0.0

    def test_rank_hybrid_boost(self):
        """Test hybrid blueprints get reuse boost."""
        meta = BlueprintMetadata(tags=["hybrid"], hybrid=True)
        bp = Blueprint(name="hybrid", category="hunt", metadata=meta)
        ranked = self.ranker.rank_single(bp)
        assert ranked.reuse_score > 50.0

    def test_custom_weights(self):
        """Test custom ranking weights."""
        weights = {
            "critic": 0.5,
            "playtest": 0.5,
            "reuse": 0.0,
            "knowledge": 0.0,
            "complexity": 0.0,
        }
        ranker = BlueprintRanker(weights=weights)
        bp = self._make_bp(
            "weighted", raw={"critic_score": 90.0, "playtest_score": 80.0}
        )
        ranked = ranker.rank_single(bp)
        assert ranked.critic_score == 90.0
        assert ranked.playtest_score == 80.0
        assert ranked.overall_rank == 85.0

    def test_empty_blueprint(self):
        """Test ranking empty blueprint."""
        bp = self._make_bp("empty")
        ranked = self.ranker.rank_single(bp)
        assert ranked.overall_rank > 0
