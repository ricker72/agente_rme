"""Tests for the ranker (extracted for coverage tracking)."""

from __future__ import annotations

import unittest

from core.knowledge import EntryType
from core.knowledge.knowledge_ranker import KnowledgeRanker, RankerWeights
from core.knowledge.models import KnowledgeEntry


def _entry(name: str, **kw) -> KnowledgeEntry:
    return KnowledgeEntry.build(
        entry_type=EntryType.HUNT, name=name, source="x", **kw,
    )


class TestRankerWeights(unittest.TestCase):
    def test_total(self):
        w = RankerWeights()
        total = w.quality + w.critic + w.playtest + w.reuse + w.similarity + w.level_fit
        self.assertEqual(w.total(), total)


class TestKnowledgeRanker(unittest.TestCase):
    def test_normalize_under_zero(self):
        r = KnowledgeRanker()
        self.assertEqual(r._normalize(-5), 0.0)

    def test_normalize_above_100(self):
        r = KnowledgeRanker()
        self.assertEqual(r._normalize(150), 1.0)

    def test_normalize_0_1(self):
        r = KnowledgeRanker()
        self.assertEqual(r._normalize(0.7), 0.7)

    def test_normalize_0_100(self):
        r = KnowledgeRanker()
        self.assertAlmostEqual(r._normalize(80), 0.8)

    def test_normalize_invalid(self):
        r = KnowledgeRanker()
        self.assertEqual(r._normalize("foo"), 0.0)
        self.assertEqual(r._normalize(None), 0.0)

    def test_level_fit_no_target(self):
        r = KnowledgeRanker()
        e = _entry("a", min_level=100, max_level=200)
        self.assertEqual(r.level_fit(e), 1.0)

    def test_level_fit_only_min(self):
        r = KnowledgeRanker()
        e = _entry("a", min_level=100, max_level=200)
        s = r.level_fit(e, target_min=150)
        self.assertGreater(s, 0.0)

    def test_level_fit_only_max(self):
        r = KnowledgeRanker()
        e = _entry("a", min_level=100, max_level=200)
        s = r.level_fit(e, target_max=150)
        self.assertGreater(s, 0.0)

    def test_rank_with_all_signals(self):
        r = KnowledgeRanker()
        e = _entry("a", attributes={"quality_score": 50})
        e.critic_score = 80
        e.playtest_score = 70
        e.reuse_score = 60
        s = r.rank(e, similarity=0.5, target_min_level=1, target_max_level=9999)
        self.assertGreater(s, 0.0)
        self.assertLessEqual(s, 1.0)

    def test_rank_clamped(self):
        r = KnowledgeRanker()
        e = _entry("a")
        s = r.rank(e, similarity=2.0)  # out of range
        self.assertLessEqual(s, 1.0)


if __name__ == "__main__":
    unittest.main()
