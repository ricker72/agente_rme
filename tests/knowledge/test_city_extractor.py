"""Tests for the city extractor."""

from __future__ import annotations

import unittest

from core.knowledge.extractors import CityExtractor
from core.knowledge.models import EntryType


def _world(**kw) -> dict:
    return {
        "meta": {"name": "test", "theme": "issavi"},
        "cities": [],
        "regions": [],
        "structures": [],
        "spawns": [],
        "waypoints": [],
        **kw,
    }


class TestCityExtractor(unittest.TestCase):
    def setUp(self):
        self.ext = CityExtractor()

    def test_extracts_from_cities_list(self):
        w = _world(cities=[{
            "name": "Issavi", "theme": "issavi", "min_level": 200, "max_level": 500,
            "tags": ["desert"],
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].name, "Issavi")
        self.assertEqual(out[0].entry_type, EntryType.CITY)
        self.assertEqual(out[0].biome, "issavi")
        self.assertEqual(out[0].min_level, 200)
        self.assertIn("desert", out[0].tags)

    def test_extracts_from_regions(self):
        w = _world(regions=[{
            "name": "issavi_city_center", "theme": "issavi",
            "min_level": 200, "max_level": 400,
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].name, "issavi_city_center")

    def test_extracts_from_structures(self):
        w = _world(structures=[{
            "name": "venore_temple", "category": "temple",
            "theme": "venore", "min_level": 100, "max_level": 200,
            "width": 30, "height": 30,
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].name, "venore_temple")

    def test_dedupes_across_sources(self):
        w = _world(
            cities=[{"name": "Issavi", "theme": "issavi"}],
            regions=[{"name": "issavi", "theme": "issavi"}],
        )
        out = self.ext.extract(w, source="src")
        # only one — first match wins
        self.assertEqual(len(out), 1)

    def test_skips_sub_zones(self):
        # depot/temple sub-zones are not "cities" themselves
        w = _world(regions=[{
            "name": "issavi_depot", "theme": "issavi",
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 0)

    def test_empty_world(self):
        out = self.ext.extract(_world(), source="src")
        self.assertEqual(out, [])

    def test_load_path(self):
        import os
        import tempfile
        import json
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "world.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(_world(cities=[{"name": "Thais", "theme": "thais"}]), f)
            out = self.ext(p)
            self.assertEqual(len(out), 1)
            self.assertEqual(out[0].name, "Thais")


if __name__ == "__main__":
    unittest.main()
