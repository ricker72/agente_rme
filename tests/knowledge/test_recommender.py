"""Tests for the recommender and ranker."""

from __future__ import annotations

import unittest

from core.knowledge import EntryType, KnowledgeEngine, KnowledgeIndex
from core.knowledge.knowledge_ranker import (
    KnowledgeRanker, RankerWeights,
)
from core.knowledge.knowledge_recommender import KnowledgeRecommender
from core.knowledge.models import KnowledgeDataset, KnowledgeEntry


def _src_roshamuul() -> dict:
    return {
        "meta": {"name": "roshamuul", "theme": "roshamuul"},
        "regions": [
            {"name": "roshamuul_circular_hunt", "theme": "roshamuul",
             "min_level": 280, "max_level": 380, "tags": ["circular"]},
        ],
        "cities": [{"name": "Issavi", "theme": "issavi"}],
        "structures": [{"name": "roshamuul_boss_arena", "category": "boss_room",
                        "tags": ["boss", "circular"], "width": 30, "height": 30}],
        "spawns": [{"monster": "Guzzlemaw",
                     "zone": "roshamuul_circular_hunt", "level": 280}],
    }

def _src_soul_war() -> dict:
    return {
        "meta": {"name": "soul_war", "theme": "roshamuul"},
        "regions": [
            {"name": "soul_war_surface", "theme": "roshamuul",
             "min_level": 250, "max_level": 500, "tags": ["circular"]},
            {"name": "soul_war_hunt", "theme": "roshamuul",
             "min_level": 280, "max_level": 400, "tags": ["circular"]},
        ],
        "structures": [{"name": "soul_war_boss_arena", "category": "arena",
                        "tags": ["boss", "circular"], "width": 40, "height": 40}],
    }


def _entry(name: str, et: EntryType, **kw) -> KnowledgeEntry:
    return KnowledgeEntry.build(entry_type=et, name=name, source="src", **kw)


class TestKnowledgeRanker(unittest.TestCase):
    def setUp(self):
        self.r = KnowledgeRanker()

    def test_default_rank(self):
        e = _entry("a", EntryType.HUNT)
        s = self.r.rank(e, similarity=0.5)
        self.assertGreaterEqual(s, 0.0)
        self.assertLessEqual(s, 1.0)

    def test_score_normalization(self):
        # Set the entry-level quality_score (not via attributes)
        e1 = _entry("a", EntryType.HUNT); e1.quality_score = 20
        e2 = _entry("b", EntryType.HUNT); e2.quality_score = 50
        e3 = _entry("c", EntryType.HUNT); e3.quality_score = 80
        s1 = self.r.rank(e1)
        s2 = self.r.rank(e2)
        s3 = self.r.rank(e3)
        self.assertLess(s1, s2)
        self.assertLess(s2, s3)

    def test_level_fit_in_range(self):
        e = _entry("a", EntryType.HUNT, min_level=200, max_level=400)
        s = self.r.rank(e, target_min_level=250, target_max_level=350)
        self.assertGreater(s, 0.0)

    def test_level_fit_out_of_range(self):
        e = _entry("a", EntryType.HUNT, min_level=200, max_level=400)
        s = self.r.rank(e, target_min_level=500, target_max_level=600)
        self.assertEqual(s, 0.0)

    def test_rank_many_sorted(self):
        entries = []
        for i in range(1, 5):
            e = _entry(f"e{i}", EntryType.HUNT)
            e.quality_score = i * 10
            entries.append(e)
        # Pass the same similarity for all so the order is by quality.
        ranked = self.r.rank_many([(e, 0.5) for e in entries])
        # Best quality first (e4 has quality 40, e1 has quality 10).
        self.assertEqual(ranked[0][0].quality_score, 40)
        self.assertEqual(ranked[-1][0].quality_score, 10)

    def test_custom_weights(self):
        w = RankerWeights(quality=0.0, critic=0.0, playtest=0.0,
                          reuse=0.0, similarity=1.0, level_fit=0.0)
        r = KnowledgeRanker(weights=w)
        # quality_score=100 should not affect ranking — only similarity
        e1 = _entry("a", EntryType.HUNT, attributes={"quality_score": 100})
        e2 = _entry("b", EntryType.HUNT, attributes={"quality_score": 0})
        s1 = r.rank(e1, similarity=0.5)
        s2 = r.rank(e2, similarity=0.5)
        self.assertEqual(s1, s2)


class TestKnowledgeRecommender(unittest.TestCase):
    def setUp(self):
        self.eng = KnowledgeEngine.build_from_sources(
            [_src_roshamuul(), _src_soul_war()],
        )
        self.rec = KnowledgeRecommender(
            self.eng.index, self.eng.ranker,
        )

    def test_recommend_for_entry(self):
        target = self.eng.dataset.by_name("roshamuul_circular_hunt")
        result = self.rec.recommend_for_entry(target, k=3)
        self.assertGreater(result.total, 0)
        # Recommended entries should be hunts
        for m in result.matches:
            self.assertEqual(m.entry.entry_type, EntryType.HUNT)

    def test_recommend_by_text(self):
        result = self.rec.recommend_by_text("circular hunt", k=3,
                                            entry_type=EntryType.HUNT)
        self.assertGreater(result.total, 0)
        for m in result.matches:
            self.assertEqual(m.entry.entry_type, EntryType.HUNT)

    def test_recommend_by_text_no_type(self):
        result = self.rec.recommend_by_text("circular", k=3)
        self.assertGreater(result.total, 0)

    def test_recommend_with_level_target(self):
        target = self.eng.dataset.by_name("roshamuul_circular_hunt")
        result = self.rec.recommend_for_entry(
            target, k=3, target_min_level=250, target_max_level=500,
        )
        self.assertGreater(result.total, 0)


if __name__ == "__main__":
    unittest.main()
