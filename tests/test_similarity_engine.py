"""
Tests for HITO 17 — Similarity Engine.

Covers cosine similarity, style/pattern matching, the search API,
clustering, statistics, persistence, and the natural-language
``query()`` helper.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from typing import Any, Dict, List

from core.learning.similarity_engine import (
    SimilarityEngine,
    SimilarityResult,
    SimilarityIndex,
)


class _Emb:
    """Tiny stand-in for a MapEmbedding object."""

    def __init__(
        self,
        region_id: str,
        vector: List[float],
        style: str = "generic",
        region_type: str = "unknown",
    ) -> None:
        self.region_id = region_id
        self.vector = vector
        self.style = style
        self.region_type = region_type
        self.dimensions = (10, 10)
        self.embedding_id = region_id


def _make_engine(num_regions: int = 5) -> SimilarityEngine:
    """Build a similarity engine with ``num_regions`` simple embeddings."""
    engine = SimilarityEngine()
    embeddings: List[_Emb] = []
    region_data: Dict[str, Dict[str, Any]] = {}

    for i in range(num_regions):
        region_id = f"region_{i}"
        # Distinct vectors that point in different directions
        vector = [float(i == j) for j in range(5)]
        style = "issavi" if i % 2 == 0 else "roshamuul"
        region_type = ["temple", "dungeon", "market", "city", "hunt"][i % 5]
        embeddings.append(_Emb(region_id, vector, style=style, region_type=region_type))
        region_data[region_id] = {"name": region_id, "type": region_type}
    engine.build_index(embeddings, region_data=region_data)
    return engine


class TestSimilarityEngineInit(unittest.TestCase):
    def test_default_state(self):
        engine = SimilarityEngine()
        self.assertIsNone(engine.index)
        self.assertIsNone(engine.embedding_matrix)
        self.assertFalse(engine._built)

    def test_index_path_is_optional(self):
        engine = SimilarityEngine(index_path=None)
        self.assertIsNone(engine.index_path)


class TestSimilarityEngineIndex(unittest.TestCase):
    def test_build_index_creates_matrix(self):
        engine = _make_engine(5)
        self.assertTrue(engine._built)
        self.assertIsNotNone(engine.embedding_matrix)
        self.assertEqual(engine.embedding_matrix.shape[0], 5)

    def test_index_has_expected_fields(self):
        engine = _make_engine(3)
        idx = engine.index
        self.assertIsInstance(idx, SimilarityIndex)
        self.assertEqual(len(idx.embeddings), 3)
        self.assertEqual(len(idx.styles), 3)
        self.assertEqual(len(idx.metadata), 3)
        self.assertEqual(len(idx.region_data), 3)

    def test_build_empty_index(self):
        engine = SimilarityEngine()
        engine.build_index([], region_data={})
        self.assertTrue(engine._built)
        self.assertEqual(len(engine.index.embeddings), 0)


class TestSimilarityEngineSimilarity(unittest.TestCase):
    def setUp(self):
        self.engine = _make_engine(5)

    def test_cosine_identical_vectors(self):
        score = self.engine._cosine_similarity([1, 0, 0], [1, 0, 0])
        self.assertAlmostEqual(score, 1.0)

    def test_cosine_orthogonal_vectors(self):
        score = self.engine._cosine_similarity([1, 0, 0], [0, 1, 0])
        self.assertAlmostEqual(score, 0.0)

    def test_cosine_opposite_vectors(self):
        score = self.engine._cosine_similarity([1, 0], [-1, 0])
        self.assertAlmostEqual(score, -1.0)

    def test_cosine_zero_vector(self):
        score = self.engine._cosine_similarity([0, 0, 0], [1, 2, 3])
        self.assertEqual(score, 0.0)

    def test_style_similarity_identical(self):
        self.assertEqual(self.engine._style_similarity("issavi", "issavi"), 1.0)

    def test_style_similarity_grouped(self):
        # Both bright group
        self.assertEqual(self.engine._style_similarity("issavi", "thais"), 0.7)

    def test_style_similarity_unrelated(self):
        self.assertEqual(self.engine._style_similarity("issavi", "roshamuul"), 0.3)

    def test_pattern_similarity_with_dicts(self):
        a = {"grid_score": 0.5, "symmetry_score": 0.6}
        b = {"grid_score": 0.5, "symmetry_score": 0.6}
        score = self.engine._pattern_similarity(a, b)
        self.assertAlmostEqual(score, 1.0)

    def test_pattern_similarity_empty(self):
        score = self.engine._pattern_similarity({}, {"grid_score": 0.5})
        self.assertEqual(score, 0.5)


class TestSimilaritySearch(unittest.TestCase):
    def setUp(self):
        self.engine = _make_engine(5)

    def test_find_similar_excludes_self(self):
        results = self.engine.find_similar("region_0", top_k=5)
        ids = [r.matched_id for r in results]
        self.assertNotIn("region_0", ids)

    def test_find_similar_returns_results(self):
        results = self.engine.find_similar("region_0", top_k=3)
        self.assertLessEqual(len(results), 3)
        for r in results:
            self.assertIsInstance(r, SimilarityResult)
            self.assertEqual(r.query_id, "region_0")
            self.assertGreaterEqual(r.similarity_score, 0.0)

    def test_find_similar_sorted_desc(self):
        results = self.engine.find_similar("region_0", top_k=5)
        scores = [r.similarity_score for r in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_find_similar_unknown_id(self):
        results = self.engine.find_similar("does_not_exist")
        self.assertEqual(results, [])

    def test_find_similar_by_style(self):
        results = self.engine.find_similar_by_style("issavi")
        for r in results:
            self.assertEqual(r.metadata["style"], "issavi")
            self.assertEqual(r.match_type, "style_exact")

    def test_find_similar_by_type(self):
        results = self.engine.find_similar_by_type("temple")
        for r in results:
            self.assertEqual(r.metadata.get("region_type"), "temple")
            self.assertEqual(r.match_type, "type_exact")

    def test_find_similar_to_vector(self):
        v = [1, 0, 0, 0, 0]
        results = self.engine.find_similar_to_vector(v, top_k=3)
        self.assertGreater(len(results), 0)
        # region_0 should be the closest since its vector is the same
        self.assertEqual(results[0].matched_id, "region_0")

    def test_find_similar_to_vector_min_similarity(self):
        v = [1, 0, 0, 0, 0]
        results = self.engine.find_similar_to_vector(v, top_k=5, min_similarity=0.9)
        for r in results:
            self.assertGreaterEqual(r.similarity_score, 0.9)

    def test_find_similar_modes(self):
        for mode in ("embedding", "style", "pattern", "hybrid"):
            results = self.engine.find_similar("region_0", top_k=3, mode=mode)
            for r in results:
                if mode == "hybrid":
                    self.assertEqual(r.match_type, "hybrid")
                else:
                    self.assertEqual(r.match_type, mode)


class TestSimilarityClusters(unittest.TestCase):
    def test_find_clusters_basic(self):
        engine = _make_engine(10)
        clusters = engine.find_clusters(k=3, min_size=1)
        self.assertIsInstance(clusters, dict)
        # All regions should be in some cluster
        total = sum(len(m) for m in clusters.values())
        self.assertEqual(total, 10)

    def test_find_clusters_min_size(self):
        engine = _make_engine(10)
        clusters = engine.find_clusters(k=3, min_size=5)
        # With min_size=5 only larger clusters are returned
        for members in clusters.values():
            self.assertGreaterEqual(len(members), 5)

    def test_find_clusters_no_index(self):
        engine = SimilarityEngine()
        self.assertEqual(engine.find_clusters(), {})


class TestSimilarityStatistics(unittest.TestCase):
    def setUp(self):
        self.engine = _make_engine(5)

    def test_style_statistics(self):
        stats = self.engine.get_style_statistics()
        self.assertIn("style_counts", stats)
        self.assertIn("style_type_distribution", stats)
        # We have 2 styles in the fixture
        self.assertGreaterEqual(len(stats["style_counts"]), 1)

    def test_type_statistics(self):
        stats = self.engine.get_type_statistics()
        self.assertIn("type_counts", stats)
        self.assertIn("type_style_distribution", stats)

    def test_statistics_empty_engine(self):
        engine = SimilarityEngine()
        self.assertEqual(engine.get_style_statistics(), {})
        self.assertEqual(engine.get_type_statistics(), {})


class TestSimilarityPersistence(unittest.TestCase):
    def test_save_and_load_index(self):
        engine = _make_engine(4)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name
        try:
            engine.save_index(temp_path)
            self.assertTrue(os.path.exists(temp_path))

            new_engine = SimilarityEngine()
            ok = new_engine.load_index(temp_path)
            self.assertTrue(ok)
            self.assertTrue(new_engine._built)
            self.assertEqual(len(new_engine.index.embeddings), 4)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_load_empty_engine(self):
        engine = SimilarityEngine()
        # Should be a no-op (no index to save)
        engine.save_index()  # type: ignore[arg-type]
        self.assertIsNone(engine.index)

    def test_load_missing_file(self):
        engine = SimilarityEngine(index_path="/tmp/does_not_exist.json")
        self.assertFalse(engine.load_index())

    def test_loaded_file_is_valid_json(self):
        engine = _make_engine(3)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name
        try:
            engine.save_index(temp_path)
            with open(temp_path, "r") as f:
                data = json.load(f)
            self.assertIn("version", data)
            self.assertIn("index", data)
            self.assertIn("embeddings", data["index"])
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestSimilarityNaturalLanguage(unittest.TestCase):
    def setUp(self):
        self.engine = _make_engine(10)

    def test_query_similar_to_style(self):
        results = self.engine.query("Find maps similar to issavi")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertEqual(r.metadata["style"], "issavi")

    def test_query_similar_to_other_style(self):
        results = self.engine.query("Find maps like roshamuul")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertEqual(r.metadata["style"], "roshamuul")

    def test_query_by_type_temple(self):
        # At least one region in fixture is a "temple" (region_0)
        results = self.engine.query("Show me temples")
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertEqual(r.metadata.get("region_type"), "temple")

    def test_query_unknown(self):
        results = self.engine.query("completely unrelated query text")
        self.assertEqual(results, [])

    def test_query_dungeon(self):
        # region_1 is a dungeon
        results = self.engine.query("dungeon stuff")
        self.assertGreater(len(results), 0)


class TestSimilarityRecommendations(unittest.TestCase):
    def test_get_recommendations(self):
        engine = _make_engine(5)
        recs = engine.get_recommendations("region_0", count=3)
        self.assertLessEqual(len(recs), 3)
        for rec in recs:
            self.assertIn("region_id", rec)
            self.assertIn("similarity", rec)
            self.assertIn("style", rec)
            self.assertIn("type", rec)
            self.assertIn("reason", rec)

    def test_get_recommendations_unknown(self):
        engine = _make_engine(5)
        recs = engine.get_recommendations("unknown_id")
        self.assertEqual(recs, [])


class TestSimilarityResultDataclass(unittest.TestCase):
    def test_to_dict(self):
        r = SimilarityResult(
            query_id="q1",
            matched_id="m1",
            similarity_score=0.85,
            match_type="embedding",
            matched_region={"name": "m1"},
            metadata={"style": "issavi"},
        )
        d = r.to_dict()
        self.assertEqual(d["query_id"], "q1")
        self.assertEqual(d["matched_id"], "m1")
        self.assertEqual(d["similarity_score"], 0.85)


if __name__ == "__main__":
    unittest.main()
