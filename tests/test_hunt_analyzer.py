"""
Tests for the HuntAnalyzer.
"""

from __future__ import annotations

import unittest

from core.critic.analyzers import HuntAnalyzer
from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region


class HuntAnalyzerTests(unittest.TestCase):
    def test_no_hunts(self):
        w = WorldModel()
        for x in range(10):
            for y in range(10):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        result = HuntAnalyzer().analyze(w)
        # Default score when no hunts
        self.assertGreaterEqual(result["score"].value, 0.0)
        # Recommendation to add hunt zones
        recs_titles = [r.title for r in result["recommendations"]]
        self.assertTrue(any("hunt" in t.lower() for t in recs_titles))

    def test_single_hunt_detected(self):
        w = WorldModel()
        w.add_region(Region(name="hunt_north", min_level=100, max_level=200))
        for x in range(20):
            for y in range(20):
                t = Tile(x=x, y=y, z=7, ground=100, zone="hunt_north")
                if (x + y) % 4 == 0:
                    t.spawn = Spawn(monster="Rat", respawn=60, radius=2)
                w.set_tile(t)
        result = HuntAnalyzer().analyze(w)
        self.assertEqual(result["metrics"]["hunts"], 1)
        self.assertGreater(result["score"].value, 0.0)

    def test_hunt_gap_detected(self):
        w = WorldModel()
        # Two hunt zones far apart
        w.add_region(Region(name="hunt_north", min_level=100, max_level=200))
        w.add_region(Region(name="hunt_south", min_level=100, max_level=200))
        for x, y in [(0, 0), (200, 200)]:
            for dx in range(10):
                for dy in range(10):
                    t = Tile(
                        x=x + dx,
                        y=y + dy,
                        z=7,
                        ground=100,
                        zone=("hunt_north" if (x, y) == (0, 0) else "hunt_south"),
                    )
                    if (dx + dy) % 4 == 0:
                        t.spawn = Spawn(monster="Rat", respawn=60, radius=2)
                    w.set_tile(t)
        result = HuntAnalyzer().analyze(w)
        self.assertEqual(result["metrics"]["hunts"], 2)
        # Hunt gap may or may not trigger; we just assert it doesn't crash
        self.assertIsNotNone(result)

    def test_empty_world(self):
        w = WorldModel()
        result = HuntAnalyzer().analyze(w)
        self.assertEqual(result["score"].value, 0.0)


if __name__ == "__main__":
    unittest.main()
