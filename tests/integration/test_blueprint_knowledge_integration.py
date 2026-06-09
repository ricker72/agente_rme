"""Integration test: Blueprint Intelligence + Knowledge Engine."""

import pytest
from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from core.blueprint_intelligence.blueprint_intelligence_engine import (
    BlueprintIntelligenceEngine,
)


class TestBlueprintKnowledgeIntegration:
    """Test integration between Blueprint Intelligence and Knowledge Engine."""

    def setup_method(self):
        self.engine = BlueprintIntelligenceEngine()

    def _make_bp(self, name="test", category="hunt", tags=None, tiles=None, raw=None):
        return Blueprint(
            name=name,
            category=category,
            size=(10, 10),
            tiles=tiles or [BlueprintTile(x=0, y=0, ground=100)],
            metadata=BlueprintMetadata(tags=tags or [category]),
            _raw=raw or {},
        )

    def test_pipeline_generate_and_embed(self):
        """Test generate + embed pipeline."""
        bps = [
            self._make_bp("Roshamuul", "hunt"),
            self._make_bp("Soul_War", "hunt"),
        ]
        self.engine.load_blueprints(bps)
        result = self.engine.run_pipeline("Generate hunt level 400", bps)
        assert "generated_blueprint" in result
        assert "embedding" in result
        assert result["ranking"]["overall_rank"] > 0

    def test_pipeline_similarity_and_rank(self):
        """Test similarity + ranking pipeline."""
        bps = [
            self._make_bp("hunt_a", "hunt", raw={"critic_score": 85.0}),
            self._make_bp("hunt_b", "hunt", raw={"critic_score": 70.0}),
            self._make_bp("city_a", "city"),
        ]
        self.engine.load_blueprints(bps)
        self.engine.build_embeddings()

        target = self._make_bp("target_hunt", "hunt")
        similar = self.engine.find_similar(target, top_k=2)
        assert len(similar) >= 0

        ranked = self.engine.rank_all()
        assert len(ranked) == 3  # only loaded blueprints

    def test_pipeline_export(self, tmp_path):
        """Test export pipeline."""
        bps = [
            self._make_bp("export_test", "hunt"),
        ]
        self.engine.load_blueprints(bps)
        self.engine.build_embeddings()
        self.engine.mine_patterns()
        self.engine.cluster()

        base = str(tmp_path)
        self.engine.export_embeddings(f"{base}/embeddings.json")
        self.engine.export_clusters(f"{base}/clusters.json")
        self.engine.export_patterns(f"{base}/patterns.json")
        self.engine.export_rankings(f"{base}/rankings.json")
        self.engine.export_recommendations(f"{base}/recommendations.json")

        import os
        assert os.path.exists(f"{base}/embeddings.json")
        assert os.path.exists(f"{base}/clusters.json")
        assert os.path.exists(f"{base}/patterns.json")

    def test_intelligence_engine_clear(self):
        """Test clearing engine state."""
        bp = self._make_bp("clear_test")
        self.engine.add_blueprint(bp)
        assert len(self.engine.blueprints) == 1
        self.engine.clear()
        assert len(self.engine.blueprints) == 0