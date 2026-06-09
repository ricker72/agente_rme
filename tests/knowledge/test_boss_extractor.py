"""Tests for the boss extractor."""

from __future__ import annotations

import unittest

from core.knowledge.extractors import BossExtractor
from core.knowledge.models import EntryType


def _world(**kw) -> dict:
    base = {
        "meta": {"name": "test", "theme": "roshamuul"},
        "cities": [], "regions": [], "structures": [], "spawns": [], "waypoints": [],
    }
    base.update(kw)
    return base


class TestBossExtractor(unittest.TestCase):
    def setUp(self):
        self.ext = BossExtractor()

    def test_extracts_boss_structure(self):
        w = _world(structures=[{
            "name": "soul_war_arena", "category": "boss_room",
            "theme": "roshamuul", "min_level": 250, "max_level": 500,
            "width": 40, "height": 40,
            "tags": ["boss", "arena", "circular"],
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        e = out[0]
        self.assertEqual(e.entry_type, EntryType.BOSS_ROOM)
        self.assertEqual(e.attributes["shape"], "circular")
        # arena takes priority in our _infer_arena_type
        self.assertIn(e.attributes["arena_type"], ("arena", "circular"))
        self.assertEqual(e.attributes["size"], 1600)

    def test_extracts_from_region(self):
        w = _world(regions=[{
            "name": "boss_arena", "theme": "roshamuul",
            "min_level": 300, "max_level": 500,
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].entry_type, EntryType.BOSS_ROOM)

    def test_dedupes_structure_and_region(self):
        w = _world(
            structures=[{"name": "boss_a", "category": "boss",
                         "width": 10, "height": 10}],
            regions=[{"name": "boss_a", "theme": "x"}],
        )
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)

    def test_skips_non_boss(self):
        w = _world(structures=[{
            "name": "house_a", "category": "house",
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 0)

    def test_infer_arena_type_from_tags(self):
        w = _world(structures=[{
            "name": "throne_room", "category": "boss_room",
            "tags": ["boss", "throne"],
            "width": 10, "height": 10,
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(out[0].attributes["arena_type"], "throne")

    def test_empty(self):
        self.assertEqual(self.ext.extract(_world()), [])


if __name__ == "__main__":
    unittest.main()
