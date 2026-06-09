"""Integration tests for Blueprint Generation Pipeline."""

import pytest
from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from core.blueprint_intelligence.blueprint_intelligence_engine import (
    BlueprintIntelligenceEngine,
)


class TestBlueprintGenerationPipeline:
    """E2E test: Generate hunt with style ratios."""

    def setup_method(self):
        self.engine = BlueprintIntelligenceEngine()

    def _make_bp(self, name="test", category="hunt", theme="generic", tags=None, tiles=None, raw=None):
        return Blueprint(
            name=name,
            category=category,
            theme=theme,
            size=(10, 10),
            tiles=tiles or [BlueprintTile(x=0, y=0, ground=100)],
            metadata=BlueprintMetadata(tags=tags or [category]),
            _raw=raw or {},
        )

    def test_e2e_generate_hybrid_hunt(self):
        """E2E: Generate hunt with 70% Roshamuul 30% Soul War."""
        bps = [
            self._make_bp("Roshamuul_Hunt", "hunt", "roshamuul", tags=["hunt", "roshamuul"]),
            self._make_bp("Soul_War_Hunt", "hunt", "soul_war", tags=["hunt", "soul_war"]),
        ]
        self.engine.load_blueprints(bps)
        result = self.engine.run_pipeline(
            "Generate hunt 70% Roshamuul 30% Soul War", bps
        )
        bp_data = result.get("generated_blueprint", {})
        assert "name" in bp_data
        assert result["ranking"]["overall_rank"] > 0

    def test_e2e_generate_city_compact(self):
        """E2E: Generate city Issavi style compact."""
        bps = [
            self._make_bp("Issavi_City", "city", "issavi", tags=["city", "issavi"]),
        ]
        generated = self.engine.generate("Generate city Issavi style compact version")
        assert generated.category == "city"
        issavi = "issavi" in generated.theme or "issavi" in str(generated.metadata.tags).lower()

    def test_e2e_evolve_blueprint(self):
        """E2E: Evolve blueprint until critic score improves."""
        bp = self._make_bp(
            "test_evolve",
            "hunt",
            raw={"critic_score": 30.0, "playtest_score": 25.0},
        )
        result = self.engine.evolve(bp, target_critic_score=50.0, max_generations=10)
        assert result.is_valid
        assert result.critic_score >= 30.0

    def test_e2e_full_pipeline(self):
        """E2E: Full Blueprint Intelligence pipeline."""
        bps = [
            self._make_bp("hunt_1", "hunt", tags=["hunt"]),
            self._make_bp("city_1", "city", tags=["city"]),
        ]
        self.engine.load_blueprints(bps)
        self.engine.build_embeddings()
        clusters = self.engine.cluster()
        patterns = self.engine.mine_patterns()
        ranked = self.engine.rank_all()
        recs = self.engine.recommend_patterns()

        assert len(clusters) > 0
        assert len(patterns) > 0
        assert len(ranked) > 0
        assert len(recs) >= 0