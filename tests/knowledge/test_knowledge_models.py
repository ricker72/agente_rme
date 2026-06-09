"""Tests for the core data models (KnowledgeEntry, Dataset, QueryResult)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from core.knowledge.models import (
    EntryType,
    KnowledgeDataset,
    KnowledgeEntry,
    KnowledgeQueryResult,
    QueryMatch,
)


class TestKnowledgeEntry(unittest.TestCase):
    def test_compute_id_is_stable(self):
        a = KnowledgeEntry.compute_id(EntryType.HUNT, "Roshamuul", "map.otbm")
        b = KnowledgeEntry.compute_id(EntryType.HUNT, "roshamuul", "MAP.OTBM")
        self.assertEqual(a, b)

    def test_build_computes_id_and_signature(self):
        e = KnowledgeEntry.build(
            entry_type=EntryType.HUNT,
            name="Roshamuul Circular",
            source="roshamuul.otbm",
            biome="roshamuul",
            min_level=250,
            max_level=380,
            tags=["circular"],
            attributes={"monsters": ["Guzzlemaw"]},
        )
        self.assertEqual(e.entry_type, EntryType.HUNT)
        self.assertEqual(e.name, "Roshamuul Circular")
        self.assertGreater(len(e.signature), 0)
        self.assertIn("circular", e.signature)
        self.assertIn("roshamuul", e.signature)
        self.assertIn("monster_guzzlemaw", e.signature)

    def test_round_trip_dict(self):
        e = KnowledgeEntry.build(
            entry_type=EntryType.CITY,
            name="Issavi",
            source="issavi.otbm",
            min_level=200,
            max_level=500,
            attributes={"theme": "issavi", "size": 2000},
        )
        d = e.to_dict()
        e2 = KnowledgeEntry.from_dict(d)
        self.assertEqual(e.id, e2.id)
        self.assertEqual(e.entry_type, e2.entry_type)
        self.assertEqual(e.name, e2.name)
        self.assertEqual(e.source, e2.source)
        self.assertEqual(e.min_level, e2.min_level)
        self.assertEqual(e.max_level, e2.max_level)

    def test_unknown_entry_type_falls_back(self):
        e = KnowledgeEntry.from_dict({
            "id": "x", "entry_type": "alien", "name": "X", "source": "y"
        })
        self.assertEqual(e.entry_type, EntryType.HUNT)


class TestKnowledgeDataset(unittest.TestCase):
    def _entry(self, name: str, entry_type: EntryType = EntryType.HUNT) -> KnowledgeEntry:
        return KnowledgeEntry.build(
            entry_type=entry_type, name=name, source="src",
        )

    def test_add_dedup(self):
        ds = KnowledgeDataset()
        a = self._entry("a")
        b = self._entry("a")  # same id
        ds.add(a)
        ds.add(b)
        self.assertEqual(ds.total(), 1)

    def test_add_different_types(self):
        ds = KnowledgeDataset()
        ds.add(self._entry("h1", EntryType.HUNT))
        ds.add(self._entry("c1", EntryType.CITY))
        self.assertEqual(ds.total(), 2)

    def test_remove(self):
        ds = KnowledgeDataset()
        e = self._entry("foo")
        ds.add(e)
        self.assertTrue(ds.remove(e.id))
        self.assertEqual(ds.total(), 0)
        self.assertFalse(ds.remove(e.id))

    def test_by_name(self):
        ds = KnowledgeDataset()
        ds.add(self._entry("Roshamuul", EntryType.HUNT))
        self.assertIsNotNone(ds.by_name("roshamuul"))
        self.assertIsNone(ds.by_name("not present"))

    def test_by_type(self):
        ds = KnowledgeDataset()
        ds.add(self._entry("h1", EntryType.HUNT))
        ds.add(self._entry("h2", EntryType.HUNT))
        ds.add(self._entry("c1", EntryType.CITY))
        self.assertEqual(len(ds.by_type(EntryType.HUNT)), 2)
        self.assertEqual(len(ds.by_type(EntryType.CITY)), 1)

    def test_counts(self):
        ds = KnowledgeDataset()
        ds.add(self._entry("h1", EntryType.HUNT))
        ds.add(self._entry("c1", EntryType.CITY))
        c = ds.counts()
        self.assertEqual(c["hunts"], 1)
        self.assertEqual(c["cities"], 1)
        self.assertEqual(c["boss_rooms"], 0)

    def test_write_and_read(self):
        ds = KnowledgeDataset()
        ds.add(self._entry("h1", EntryType.HUNT))
        ds.add(self._entry("c1", EntryType.CITY))
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "kds.json")
            ds.write(path)
            self.assertTrue(os.path.exists(path))
            ds2 = KnowledgeDataset.read(path)
            self.assertEqual(ds2.total(), 2)
            self.assertEqual(len(ds2.hunts), 1)
            self.assertEqual(len(ds2.cities), 1)

    def test_to_dict_has_buckets(self):
        ds = KnowledgeDataset()
        ds.add(self._entry("h", EntryType.HUNT))
        ds.add(self._entry("b", EntryType.BOSS_ROOM))
        d = ds.to_dict()
        self.assertIn("hunts", d)
        self.assertIn("boss_rooms", d)
        self.assertIn("_meta", d)
        self.assertEqual(d["_meta"]["total_entries"], 2)


class TestQueryMatch(unittest.TestCase):
    def test_round_trip(self):
        e = KnowledgeEntry.build(
            entry_type=EntryType.HUNT, name="x", source="y",
        )
        m = QueryMatch(entry=e, score=0.75, match_type="text", explanation="x")
        d = m.to_dict()
        m2 = QueryMatch.from_dict(d)
        self.assertEqual(m2.entry.id, e.id)
        self.assertEqual(m2.score, 0.75)
        self.assertEqual(m2.match_type, "text")


class TestKnowledgeQueryResult(unittest.TestCase):
    def test_sort(self):
        e1 = KnowledgeEntry.build(EntryType.HUNT, "a", "x")
        e2 = KnowledgeEntry.build(EntryType.HUNT, "b", "x")
        r = KnowledgeQueryResult(query="q")
        r.add(QueryMatch(entry=e2, score=0.5))
        r.add(QueryMatch(entry=e1, score=0.9))
        r.sort()
        self.assertEqual(r.matches[0].entry.name, "a")
        self.assertEqual(r.top(1)[0].entry.name, "a")

    def test_names(self):
        e1 = KnowledgeEntry.build(EntryType.HUNT, "alpha", "x")
        e2 = KnowledgeEntry.build(EntryType.HUNT, "beta", "x")
        r = KnowledgeQueryResult(query="q")
        r.add(QueryMatch(entry=e1, score=0.5))
        r.add(QueryMatch(entry=e2, score=0.5))
        self.assertEqual(r.names(), ["alpha", "beta"])


if __name__ == "__main__":
    unittest.main()
