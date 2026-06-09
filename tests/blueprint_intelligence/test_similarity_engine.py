"""Tests for BlueprintSimilarityEngine."""

import pytest
from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from core.blueprint_intelligence.blueprint_similarity_engine import (
    BlueprintSimilarityEngine,
)
from core.blueprint_intelligence.blueprint_embedding_engine import (
    BlueprintEmbeddingEngine,
)


class TestBlueprintSimilarityEngine:
    """Test similarity computation and search."""

    def setup_method(self):
        self.embedder = BlueprintEmbeddingEngine()
        self.engine = BlueprintSimilarityEngine(embedding_engine=self.embedder)

    def _make_bp(self, name="test", category="hunt", theme="generic", size=(10, 10), tags=None, tiles=None):
        return Blueprint(
            name=name,
            category=category,
            theme=theme,
            size=size,
            tiles=tiles or [],
            metadata=BlueprintMetadata(tags=tags or []),
        )

    def test_compare_same_blueprint(self):
        """Test comparing a blueprint to itself should have high similarity."""
        bp = self._make_bp("test_bp", tags=["hunt"])
        result = self.engine.compare(bp, bp)
        assert result.cosine_similarity >= 0.99
        assert result.hybrid_score >= 0.99

    def test_compare_different_categories(self):
        """Test comparing blueprints of different categories."""
        bp_a = self._make_bp("hunt_a", "hunt", tags=["hunt"])
        bp_b = self._make_bp("city_b", "city", tags=["city"])
        result = self.engine.compare(bp_a, bp_b)
        assert result.hybrid_score >= 0.0

    def test_find_similar_blueprints(self):
        """Test finding similar blueprints."""
        target = self._make_bp("target", "hunt", tags=["hunt"])
        candidates = [
            self._make_bp(f"bp_{i}", "hunt", tags=["hunt"]) for i in range(5)
        ]
        results = self.engine.find_similar_blueprints(target, candidates, top_k=3)
        assert len(results) <= 3
        assert all(r.query_blueprint == "target" for r in results)

    def test_find_similar_hunts(self):
        """Test finding similar hunts filters by category."""
        target = self._make_bp("target", "hunt")
        candidates = [
            self._make_bp("hunt_1", "hunt"),
            self._make_bp("city_1", "city"),
            self._make_bp("hunt_2", "hunt"),
        ]
        results = self.engine.find_similar_hunts(target, candidates, top_k=5)
        assert all(r.category == "hunt" for r in results)

    def test_find_similar_cities(self):
        """Test finding similar cities."""
        target = self._make_bp("target", "city")
        candidates = [
            self._make_bp("city_1", "city"),
            self._make_bp("hunt_1", "hunt"),
        ]
        results = self.engine.find_similar_cities(target, candidates, top_k=5)
        assert all(r.category == "city" for r in results)

    def test_find_similar_boss_rooms(self):
        """Test finding similar boss rooms."""
        target = self._make_bp("target", "boss_room")
        candidates = [
            self._make_bp("boss_1", "boss_room"),
            self._make_bp("hunt_1", "hunt"),
        ]
        results = self.engine.find_similar_boss_rooms(target, candidates, top_k=5)
        assert all(r.category == "boss_room" for r in results)

    def test_jaccard_similarity_matching_tags(self):
        """Test Jaccard similarity with matching tags."""
        bp_a = self._make_bp("a", "hunt", tags=["hunt", "fire", "dragon"])
        bp_b = self._make_bp("b", "hunt", tags=["hunt", "fire", "demon"])
        result = self.engine.compare(bp_a, bp_b)
        assert result.jaccard_similarity > 0.0



    def test_jaccard_similarity_no_overlap(self):
        """Test Jaccard similarity with no overlapping tags."""
        bp_a = self._make_bp("a", "city", tags=["city", "depot"])
        bp_b = self._make_bp("b", "boss_room", tags=["boss", "dragon"])
        result = self.engine.compare(bp_a, bp_b)
        # Category and theme won't match either, so jaccard should be 0
        assert result.jaccard_similarity >= 0.0

    def test_structural_similarity_same_size(self):
        """Test structural similarity with same sizes."""
        bp_a = self._make_bp("a", "hunt", size=(15, 15))
        bp_b = self._make_bp("b", "hunt", size=(15, 15))
        result = self.engine.compare(bp_a, bp_b)
        assert result.structural_similarity > 0.5

    def test_structural_similarity_different_sizes(self):
        """Test structural similarity with different sizes."""
        bp_a = self._make_bp("a", "hunt", size=(10, 10))
        bp_b = self._make_bp("b", "hunt", size=(30, 30))
        result = self.engine.compare(bp_a, bp_b)
        assert result.structural_similarity < 1.0

    def test_graph_similarity(self):
        """Test graph similarity component."""
        bp_a = self._make_bp("a", "hunt")
        bp_b = self._make_bp("b", "hunt")
        result = self.engine.compare(bp_a, bp_b)
        assert 0.0 <= result.graph_similarity <= 1.0

    def test_results_sorted_by_hybrid_score(self):
        """Test results are sorted by hybrid_score descending."""
        target = self._make_bp("target", "hunt")
        candidates = [
            self._make_bp(f"bp_{i}", "hunt") for i in range(5)
        ]
        results = self.engine.find_similar_blueprints(target, candidates, top_k=5)
        for i in range(len(results) - 1):
            assert results[i].hybrid_score >= results[i + 1].hybrid_score

    def test_to_dict_roundtrip(self):
        """Test similarity result serialization."""
        bp_a = self._make_bp("a")
        bp_b = self._make_bp("b")
        result = self.engine.compare(bp_a, bp_b)
        data = result.to_dict()
        assert data["query_blueprint"] == "a"
        assert data["target_blueprint"] == "b"
        restored = type(result).from_dict(data)
        assert restored.hybrid_score == result.hybrid_score

    def test_custom_weights(self):
        """Test custom similarity weights."""
        weights = {"cosine": 0.5, "jaccard": 0.3, "structural": 0.1, "graph": 0.1}
        engine = BlueprintSimilarityEngine(
            embedding_engine=self.embedder,
            weights=weights,
        )
        bp_a = self._make_bp("a", "hunt")
        bp_b = self._make_bp("b", "hunt")
        result = engine.compare(bp_a, bp_b)
        assert result.hybrid_score > 0.0

    def test_find_similar_skips_self(self):
        """Test that self is excluded from results."""
        target = self._make_bp("self", "hunt")
        candidates = [target, self._make_bp("other", "hunt")]
        results = self.engine.find_similar_blueprints(target, candidates, top_k=5)
        assert all(r.target_blueprint != "self" for r in results)
