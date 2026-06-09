"""Tests for the similarity primitives (cosine, jaccard, pattern, hybrid)."""

from __future__ import annotations

import unittest

from core.knowledge.models import (
    cosine_similarity,
    hybrid_similarity,
    jaccard_similarity,
    pattern_similarity,
    build_idf,
)


class TestCosineSimilarity(unittest.TestCase):
    def test_identical_strings_score_one(self):
        score = cosine_similarity("roshamuul circular", "roshamuul circular")
        self.assertAlmostEqual(score, 1.0, places=4)

    def test_disjoint_strings_score_zero(self):
        score = cosine_similarity("foo", "bar")
        self.assertEqual(score, 0.0)

    def test_empty_inputs(self):
        self.assertEqual(cosine_similarity("", "anything"), 0.0)
        self.assertEqual(cosine_similarity({}, "anything"), 0.0)

    def test_dict_input(self):
        a = {"roshamuul": 0.5, "circular": 0.5}
        b = {"roshamuul": 0.5, "circular": 0.5}
        self.assertAlmostEqual(cosine_similarity(a, b), 1.0, places=4)
        # Slightly different vector — close to 1 but not exactly.
        c = {"roshamuul": 0.6, "circular": 0.4}
        s = cosine_similarity(a, c)
        self.assertGreater(s, 0.9)
        self.assertLess(s, 1.0)

    def test_idf_weighting(self):
        idf = {"roshamuul": 5.0, "hunt": 1.0}
        s1 = cosine_similarity("roshamuul hunt", "roshamuul", idf=idf)
        s2 = cosine_similarity("roshamuul hunt", "hunt", idf=idf)
        self.assertGreater(s1, s2)


class TestJaccardSimilarity(unittest.TestCase):
    def test_identical_sets(self):
        self.assertEqual(jaccard_similarity({"a", "b"}, {"a", "b"}), 1.0)

    def test_disjoint_sets(self):
        self.assertEqual(jaccard_similarity({"a"}, {"b"}), 0.0)

    def test_partial_overlap(self):
        self.assertAlmostEqual(
            jaccard_similarity({"a", "b"}, {"a", "c"}), 1 / 3, places=4
        )

    def test_compound_tokens_expand(self):
        # "monster_rat" expands to {"monster", "rat"} so the
        # intersection with {"monster", "rat"} is the whole expanded set.
        a = jaccard_similarity({"monster_rat"}, {"monster_rat"})
        self.assertEqual(a, 1.0)
        # Cross-side: a "monster_rat" token shares both expanded tokens
        # with a "monster" + "rat" set, but the latter has no compound
        # so the union still has the "monster_rat" token. Result is 2/3.
        s = jaccard_similarity(["monster_rat"], ["monster", "rat"])
        self.assertAlmostEqual(s, 2 / 3, places=4)

    def test_empty_inputs(self):
        self.assertEqual(jaccard_similarity("", ""), 1.0)
        self.assertEqual(jaccard_similarity("", "x"), 0.0)


class TestPatternSimilarity(unittest.TestCase):
    def test_identical_attrs(self):
        a = {"shape": "circular", "theme": "roshamuul", "size": 100}
        b = {"shape": "circular", "theme": "roshamuul", "size": 100}
        self.assertAlmostEqual(pattern_similarity(a, b), 1.0, places=4)

    def test_different_categorical(self):
        a = {"shape": "circular", "theme": "roshamuul"}
        b = {"shape": "rectangular", "theme": "issavi"}
        self.assertLess(pattern_similarity(a, b), 0.5)

    def test_continuous_close(self):
        a = {"size": 100, "shape": "circular"}
        b = {"size": 110, "shape": "circular"}
        s = pattern_similarity(a, b)
        # categorical match on shape (1) + close continuous size (~0.91)
        # => 0.7 * 1 + 0.3 * 0.91 = ~0.97
        self.assertGreater(s, 0.9)

    def test_continuous_far(self):
        a = {"size": 10}
        b = {"size": 1000}
        s = pattern_similarity(a, b)
        self.assertLess(s, 0.1)

    def test_empty_inputs(self):
        self.assertEqual(pattern_similarity(None, None), 0.0)
        self.assertEqual(pattern_similarity({}, {}), 0.0)


class TestHybridSimilarity(unittest.TestCase):
    def test_combines_signals(self):
        a_text = "roshamuul circular hunt"
        b_text = "roshamuul circular hunt"
        attrs = {"shape": "circular", "theme": "roshamuul"}
        score = hybrid_similarity(a_text, b_text, attrs, attrs)
        self.assertGreater(score, 0.7)

    def test_zero_for_disjoint(self):
        score = hybrid_similarity("foo bar", "baz qux")
        self.assertEqual(score, 0.0)


class TestBuildIDF(unittest.TestCase):
    def test_empty_corpus(self):
        self.assertEqual(build_idf([]), {})

    def test_single_document(self):
        idf = build_idf(["roshamuul circular"])
        self.assertIn("roshamuul", idf)
        self.assertIn("circular", idf)
        self.assertGreater(idf["roshamuul"], 0.0)

    def test_idf_differentiates_rare_vs_common(self):
        # "roshamuul" appears in 1 doc, "hunt" in both
        idf = build_idf(["roshamuul hunt", "issavi hunt"])
        self.assertGreater(idf["roshamuul"], idf["hunt"])


if __name__ == "__main__":
    unittest.main()
