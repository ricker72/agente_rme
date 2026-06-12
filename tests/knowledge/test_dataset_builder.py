"""Tests for the DatasetBuilder."""

from __future__ import annotations

import os
import tempfile
import unittest

from core.knowledge import DatasetBuilder
from core.knowledge.models import KnowledgeDataset


def _src_roshamuul() -> dict:
    return {
        "meta": {"name": "roshamuul", "theme": "roshamuul"},
        "regions": [
            {
                "name": "roshamuul_circular_hunt",
                "theme": "roshamuul",
                "min_level": 280,
                "max_level": 380,
                "tags": ["circular"],
            },
        ],
        "cities": [
            {"name": "Issavi", "theme": "issavi", "min_level": 250, "max_level": 450}
        ],
        "structures": [
            {
                "name": "roshamuul_boss_arena",
                "category": "boss_room",
                "tags": ["boss", "circular", "arena"],
                "width": 30,
                "height": 30,
            }
        ],
        "spawns": [
            {"monster": "Guzzlemaw", "zone": "roshamuul_circular_hunt", "level": 280}
        ],
        "waypoints": [{"name": "roshamuul_tp"}],
        "quests": [{"name": "Soul War", "difficulty": "hard"}],
    }


def _src_issavi() -> dict:
    return {
        "meta": {"name": "issavi", "theme": "issavi"},
        "regions": [
            {
                "name": "issavi_sewers_hunt",
                "theme": "issavi",
                "min_level": 250,
                "max_level": 400,
                "tags": ["sewer"],
            },
        ],
        "cities": [{"name": "issavi_city", "theme": "issavi"}],
        "spawns": [{"monster": "Scarab", "zone": "issavi_sewers_hunt", "level": 280}],
    }


class TestDatasetBuilder(unittest.TestCase):
    def test_build_from_dict_sources(self):
        b = DatasetBuilder()
        ds = b.build_from_sources([_src_roshamuul(), _src_issavi()])
        self.assertGreater(ds.total(), 0)
        names = [h.name for h in ds.hunts]
        self.assertIn("roshamuul_circular_hunt", names)
        self.assertIn("issavi_sewers_hunt", names)

    def test_stats(self):
        b = DatasetBuilder()
        b.build_from_sources([_src_roshamuul(), _src_issavi()])
        stats = b.last_stats
        self.assertEqual(stats.sources_processed, 2)
        self.assertEqual(stats.sources_failed, 0)
        self.assertGreater(stats.entries_added, 0)

    def test_attach_scores(self):
        b = DatasetBuilder()
        ds = b.build_from_sources([_src_roshamuul()])
        b.attach_scores(
            ds,
            critic_report={"Issavi": 88.0, "Soul War": 92.0},
        )
        issavi = ds.by_name("Issavi")
        soul = ds.by_name("Soul War")
        self.assertEqual(issavi.critic_score, 88.0)
        self.assertEqual(soul.critic_score, 92.0)

    def test_default_scores(self):
        b = DatasetBuilder(quality_default=70.0, reuse_default=40.0)
        ds = b.build_from_sources([_src_roshamuul()])
        for e in ds.all_entries():
            self.assertGreaterEqual(e.quality_score, 70.0)
            self.assertGreaterEqual(e.reuse_score, 40.0)

    def test_write_to_file(self):
        b = DatasetBuilder()
        ds = b.build_from_sources([_src_roshamuul()])
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "kds.json")
            ds.write(path)
            self.assertTrue(os.path.exists(path))
            ds2 = KnowledgeDataset.read(path)
            self.assertEqual(ds2.total(), ds.total())

    def test_handles_unknown_object(self):
        b = DatasetBuilder()

        # An object that is not a dict and has no to_dict
        class _Dummy:
            name = "dummy"

        ds = b.build_from_sources([_Dummy()])
        # No entries but no exception
        self.assertIsInstance(ds, KnowledgeDataset)

    def test_handles_none(self):
        b = DatasetBuilder()
        ds = b.build_from_sources([None])
        self.assertEqual(ds.total(), 0)

    def test_extends_existing_dataset(self):
        b = DatasetBuilder()
        ds = KnowledgeDataset()
        b.build_from_sources([_src_roshamuul()], dataset=ds)
        before = ds.total()
        b.build_from_sources([_src_issavi()], dataset=ds)
        self.assertGreater(ds.total(), before)

    def test_handles_string_source(self):
        import json

        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "src.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(_src_roshamuul(), f)
            b = DatasetBuilder()
            ds = b.build_from_sources([p])
            self.assertGreater(ds.total(), 0)


if __name__ == "__main__":
    unittest.main()
