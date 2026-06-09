"""Tests for the KnowledgeEngine public API."""

from __future__ import annotations

import os
import tempfile
import unittest

from core.knowledge import (
    DatasetBuilder,
    EntryType,
    KnowledgeEngine,
    parse_query,
)
from core.knowledge.models import KnowledgeDataset, KnowledgeEntry


def _src_roshamuul() -> dict:
    return {
        "meta": {"name": "roshamuul", "theme": "roshamuul"},
        "regions": [
            {"name": "roshamuul_circular_hunt", "theme": "roshamuul",
             "min_level": 280, "max_level": 380, "tags": ["circular"]},
        ],
        "cities": [{"name": "Issavi", "theme": "issavi",
                    "min_level": 250, "max_level": 450}],
        "structures": [{"name": "roshamuul_boss_arena",
                        "category": "boss_room",
                        "tags": ["boss", "circular", "arena"],
                        "width": 30, "height": 30}],
        "spawns": [{"monster": "Guzzlemaw",
                     "zone": "roshamuul_circular_hunt", "level": 280}],
        "quests": [{"name": "Soul War", "difficulty": "hard"}],
    }


def _src_issavi() -> dict:
    return {
        "meta": {"name": "issavi", "theme": "issavi"},
        "regions": [
            {"name": "issavi_sewers_hunt", "theme": "issavi",
             "min_level": 250, "max_level": 400, "tags": ["sewer"]},
        ],
        "cities": [{"name": "issavi_city", "theme": "issavi"}],
    }


def _src_soul_war() -> dict:
    return {
        "meta": {"name": "soul_war", "theme": "roshamuul"},
        "regions": [
            {"name": "soul_war_surface", "theme": "roshamuul",
             "min_level": 250, "max_level": 500, "tags": ["soul_war", "circular"]},
        ],
        "structures": [{"name": "soul_war_boss_arena", "category": "arena",
                        "tags": ["boss", "circular"], "width": 40, "height": 40}],
        "raids": [{"name": "Ferumbras Raid", "min_level": 300}],
    }


class TestKnowledgeEngine(unittest.TestCase):
    def _engine(self) -> KnowledgeEngine:
        return KnowledgeEngine.build_from_sources(
            [_src_roshamuul(), _src_issavi(), _src_soul_war()]
        )

    def test_build_from_sources(self):
        eng = self._engine()
        self.assertGreater(eng.dataset.total(), 0)

    def test_find_similar_hunts_exact(self):
        eng = self._engine()
        result = eng.find_similar_hunts("roshamuul_circular_hunt", k=5)
        self.assertGreaterEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "roshamuul_circular_hunt")
        self.assertEqual(result[0]["match_type"], "exact")

    def test_find_similar_hunts_returns_dicts(self):
        eng = self._engine()
        result = eng.find_similar_hunts("roshamuul_circular_hunt", k=3)
        for r in result:
            self.assertIn("name", r)
            self.assertIn("score", r)
            self.assertIn("biome", r)
            self.assertIn("entry_type", r)

    def test_find_similar_cities(self):
        eng = self._engine()
        result = eng.find_similar_cities("Issavi", k=3)
        self.assertGreater(len(result), 0)
        # First should be exact
        self.assertEqual(result[0]["match_type"], "exact")

    def test_find_similar_boss_rooms(self):
        eng = self._engine()
        result = eng.find_similar_boss_rooms("roshamuul_boss_arena", k=3)
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]["name"], "roshamuul_boss_arena")

    def test_find_similar_quests(self):
        eng = self._engine()
        result = eng.find_similar_quests("Soul War", k=3)
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]["name"], "Soul War")

    def test_find_similar_regions(self):
        eng = self._engine()
        result = eng.find_similar_regions("soul_war_surface", k=3)
        self.assertGreater(len(result), 0)

    def test_query_text(self):
        eng = self._engine()
        r = eng.query_text("boss rooms with circular arena", k=5)
        self.assertGreater(r.total, 0)
        for m in r.matches:
            self.assertGreaterEqual(m.score, 0.0)
            self.assertLessEqual(m.score, 1.0)

    def test_query_structured(self):
        eng = self._engine()
        r = eng.query_structured(EntryType.HUNT, k=5, min_level=250, max_level=400)
        self.assertGreater(r.total, 0)

    def test_save_and_load(self):
        eng = self._engine()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "kds.json")
            eng.save(path)
            eng2 = KnowledgeEngine.load(path)
            self.assertEqual(eng.dataset.total(), eng2.dataset.total())
            self.assertEqual(
                len(eng.dataset.hunts), len(eng2.dataset.hunts),
            )

    def test_lookup_for_prompt(self):
        eng = self._engine()
        result = eng.lookup_for_prompt("hunts with circular routes level 300-500", k=3)
        self.assertEqual(result["entry_type"], "hunt")
        self.assertEqual(result["min_level"], 300)
        self.assertEqual(result["max_level"], 500)
        # similar should be a list (may be empty if all filtered)
        self.assertIsInstance(result["similar"], list)

    def test_get_catalog(self):
        eng = self._engine()
        cat = eng.get_catalog()
        self.assertGreater(cat.total_entries, 0)
        self.assertGreater(len(cat.top_cities), 0)

    def test_empty_dataset(self):
        eng = KnowledgeEngine()
        self.assertEqual(eng.find_similar_hunts("x"), [])


class TestParseQuery(unittest.TestCase):
    def test_parse_hunt_query(self):
        p = parse_query("hunts level 300-500")
        self.assertEqual(p.entry_type, EntryType.HUNT)
        self.assertEqual(p.min_level, 300)
        self.assertEqual(p.max_level, 500)

    def test_parse_biome_query(self):
        p = parse_query("cities desert biome")
        self.assertEqual(p.entry_type, EntryType.CITY)
        self.assertEqual(p.biome, "desert")

    def test_parse_circular_query(self):
        p = parse_query("hunts with circular routes")
        self.assertEqual(p.entry_type, EntryType.HUNT)
        self.assertEqual(p.attrs.get("route"), "circular")

    def test_parse_boss_query(self):
        p = parse_query("boss rooms level 500")
        self.assertEqual(p.entry_type, EntryType.BOSS_ROOM)
        self.assertEqual(p.min_level, 500)
        self.assertEqual(p.max_level, 500)

    def test_parse_empty(self):
        p = parse_query("")
        self.assertEqual(p.entry_type, None)
        self.assertEqual(p.min_level, None)


if __name__ == "__main__":
    unittest.main()
