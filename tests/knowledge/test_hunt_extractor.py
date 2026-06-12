"""Tests for the hunt extractor."""

from __future__ import annotations

import unittest

from core.knowledge.extractors import HuntExtractor
from core.knowledge.models import EntryType


def _world(**kw) -> dict:
    base = {
        "meta": {"name": "test", "theme": "roshamuul"},
        "cities": [],
        "regions": [],
        "structures": [],
        "spawns": [],
        "waypoints": [],
    }
    base.update(kw)
    return base


class TestHuntExtractor(unittest.TestCase):
    def setUp(self):
        self.ext = HuntExtractor()

    def test_extracts_hunt_region(self):
        w = _world(
            regions=[
                {
                    "name": "roshamuul_circular_hunt",
                    "theme": "roshamuul",
                    "min_level": 280,
                    "max_level": 380,
                    "tags": ["circular"],
                }
            ]
        )
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        e = out[0]
        self.assertEqual(e.entry_type, EntryType.HUNT)
        self.assertIn("circular_route", e.tags)
        self.assertTrue((e.attributes or {}).get("circular"))

    def test_groups_spawns(self):
        w = _world(
            regions=[
                {
                    "name": "soul_war_hunt",
                    "theme": "roshamuul",
                    "min_level": 250,
                    "max_level": 500,
                }
            ],
            spawns=[
                {"monster": "Guzzlemaw", "zone": "soul_war_hunt", "level": 280},
                {"monster": "Hellflayer", "zone": "soul_war_hunt", "level": 320},
            ],
        )
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertIn("Guzzlemaw", out[0].attributes["monsters"])
        self.assertIn("Hellflayer", out[0].attributes["monsters"])
        self.assertEqual(out[0].attributes["spawns"], 2)

    def test_difficulty_inference(self):
        cases = [
            (50, 100, "easy"),
            (200, 250, "medium"),
            (300, 400, "hard"),
            (500, 700, "extreme"),
        ]
        for mn, mx, expected in cases:
            w = _world(
                regions=[
                    {
                        "name": f"hunt_{mn}_{mx}",
                        "theme": "x",
                        "min_level": mn,
                        "max_level": mx,
                    }
                ]
            )
            out = self.ext.extract(w, source="src")
            self.assertEqual(len(out), 1)
            self.assertEqual(
                out[0].attributes["difficulty"],
                expected,
                f"failed for {mn}-{mx}",
            )

    def test_skips_non_hunt(self):
        w = _world(
            regions=[
                {
                    "name": "issavi_city_center",
                    "theme": "issavi",
                }
            ]
        )
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 0)

    def test_empty(self):
        self.assertEqual(self.ext.extract(_world()), [])

    def test_route_inference(self):
        w = _world(
            regions=[
                {
                    "name": "roshamuul_circular_hunt",
                    "theme": "roshamuul",
                }
            ]
        )
        out = self.ext.extract(w, source="src")
        self.assertEqual(out[0].attributes["route"], "circular")


if __name__ == "__main__":
    unittest.main()
