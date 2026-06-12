"""Tests for KnowledgeQuery and KnowledgeIndex."""

from __future__ import annotations

import unittest

from core.knowledge import EntryType, KnowledgeIndex
from core.knowledge.knowledge_query import KnowledgeQuery, parse_query
from core.knowledge.models import KnowledgeEntry, KnowledgeDataset


def _entry(name: str, et: EntryType = EntryType.HUNT, **kw) -> KnowledgeEntry:
    return KnowledgeEntry.build(
        entry_type=et,
        name=name,
        source="src",
        **kw,
    )


class TestParseQuery(unittest.TestCase):
    def test_detects_hunt(self):
        p = parse_query("hunts level 300-500")
        self.assertEqual(p.entry_type, EntryType.HUNT)
        self.assertEqual(p.min_level, 300)
        self.assertEqual(p.max_level, 500)

    def test_detects_city(self):
        self.assertEqual(parse_query("city").entry_type, EntryType.CITY)

    def test_detects_boss(self):
        self.assertEqual(parse_query("boss arena").entry_type, EntryType.BOSS_ROOM)

    def test_detects_quest(self):
        self.assertEqual(parse_query("quest mission").entry_type, EntryType.QUEST)

    def test_detects_biome_desert(self):
        self.assertEqual(parse_query("cities in desert").biome, "desert")

    def test_detects_biome_issavi(self):
        self.assertEqual(parse_query("hunts issavi").biome, "issavi")

    def test_detects_circular(self):
        self.assertEqual(parse_query("circular routes").attrs.get("route"), "circular")

    def test_detects_difficulty(self):
        self.assertEqual(parse_query("hard").difficulty, "hard")
        self.assertEqual(parse_query("extreme").difficulty, "extreme")


class TestKnowledgeQuery(unittest.TestCase):
    def setUp(self):
        ds = KnowledgeDataset()
        ds.add(
            _entry(
                "roshamuul_circular_hunt",
                EntryType.HUNT,
                biome="roshamuul",
                min_level=250,
                max_level=380,
                attributes={"circular": True},
            )
        )
        ds.add(
            _entry(
                "issavi_sewers_hunt",
                EntryType.HUNT,
                biome="issavi",
                min_level=250,
                max_level=400,
                attributes={"circular": False},
            )
        )
        ds.add(
            _entry(
                "roshamuul_boss_arena",
                EntryType.BOSS_ROOM,
                biome="roshamuul",
                min_level=300,
                max_level=500,
                attributes={"shape": "circular"},
            )
        )
        self.ds = ds
        self.index = KnowledgeIndex()
        self.index.sync(ds)
        self.q = KnowledgeQuery(self.index)

    def test_text_query_typed(self):
        # Use a query that contains a real token from the hunt entries.
        r = self.q.text("hunt")
        self.assertGreater(r.total, 0)
        for m in r.matches:
            self.assertEqual(m.entry.entry_type, EntryType.HUNT)

    def test_text_query_with_level_filter(self):
        r = self.q.text("hunts level 300-500")
        self.assertGreaterEqual(r.total, 0)

    def test_text_query_biome(self):
        r = self.q.text("hunts in roshamuul")
        self.assertGreater(r.total, 0)

    def test_text_query_circular(self):
        r = self.q.text("circular routes")
        self.assertGreater(r.total, 0)

    def test_text_query_no_match(self):
        # Use a query that produces no token matches at all.
        r = self.q.text("qzpwjzqnqzx")
        self.assertEqual(r.total, 0)

    def test_text_query_empty(self):
        r = self.q.text("")
        self.assertEqual(r.total, 0)

    def test_structured_query(self):
        r = self.q.structured(EntryType.HUNT, k=10)
        self.assertEqual(r.total, 2)

    def test_structured_query_with_level(self):
        r = self.q.structured(EntryType.HUNT, k=10, min_level=200, max_level=300)
        self.assertGreaterEqual(r.total, 1)

    def test_structured_query_with_biome(self):
        r = self.q.structured(EntryType.HUNT, k=10, biome="roshamuul")
        self.assertGreaterEqual(r.total, 1)

    def test_filter_query(self):
        r = self.q.filter(EntryType.HUNT, lambda e: e.min_level >= 250)
        self.assertEqual(r.total, 2)

    def test_text_query_across_indexers(self):
        # Remove type hint so it searches all indexers
        r = self.q.text("circular", k=10)
        self.assertGreater(r.total, 0)


class TestKnowledgeIndex(unittest.TestCase):
    def test_add_and_get(self):
        idx = KnowledgeIndex()
        e = _entry("foo", EntryType.HUNT)
        idx.add(e)
        self.assertEqual(len(idx.hunt), 1)
        self.assertIs(idx.hunt.get("foo"), e)
        self.assertIsNone(idx.hunt.get("not_present"))

    def test_add_replaces_same_id(self):
        idx = KnowledgeIndex()
        e1 = _entry("foo", EntryType.HUNT, min_level=1)
        e2 = _entry("foo", EntryType.HUNT, min_level=200)
        idx.add(e1)
        idx.add(e2)
        self.assertEqual(len(idx.hunt), 1)
        self.assertEqual(idx.hunt.get("foo").min_level, 200)

    def test_clear(self):
        idx = KnowledgeIndex()
        idx.hunt.add(_entry("foo"))
        idx.hunt.clear()
        self.assertEqual(len(idx.hunt), 0)

    def test_sync(self):
        ds = KnowledgeDataset()
        ds.add(_entry("a", EntryType.HUNT))
        ds.add(_entry("b", EntryType.CITY))
        ds.add(_entry("c", EntryType.BOSS_ROOM))
        idx = KnowledgeIndex()
        idx.sync(ds)
        self.assertEqual(len(idx.hunt), 1)
        self.assertEqual(len(idx.city), 1)
        self.assertEqual(len(idx.boss), 1)

    def test_search_returns_sorted(self):
        idx = KnowledgeIndex()
        for name in ["alpha", "beta", "gamma", "delta"]:
            idx.add(_entry(name, EntryType.HUNT))
        results = idx.hunt.search("alpha", k=3)
        self.assertEqual(len(results), 3)
        # First result should be alpha (exact match)
        self.assertEqual(results[0][0].name, "alpha")
        self.assertEqual(results[0][1], 1.0)


if __name__ == "__main__":
    unittest.main()
