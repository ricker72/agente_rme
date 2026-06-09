"""
Tests for the NavigationAnalyzer.
"""

from __future__ import annotations

import unittest

from core.critic.analyzers import NavigationAnalyzer
from core.world.world_model import WorldModel
from core.world.tile import Tile


def _ground_square(size: int = 10, z: int = 7, ground: int = 100) -> WorldModel:
    w = WorldModel()
    for x in range(size):
        for y in range(size):
            w.set_tile(Tile(x=x, y=y, z=z, ground=ground))
    return w


class NavigationAnalyzerTests(unittest.TestCase):

    def test_score_in_range(self):
        w = _ground_square(10)
        result = NavigationAnalyzer().analyze(w)
        self.assertGreaterEqual(result["score"].value, 0.0)
        self.assertLessEqual(result["score"].value, 100.0)

    def test_empty_world(self):
        w = WorldModel()
        result = NavigationAnalyzer().analyze(w)
        self.assertEqual(result["score"].value, 0.0)
        self.assertEqual(result["metrics"]["regions"], 0)

    def test_single_region_no_isolation(self):
        w = _ground_square(15)
        result = NavigationAnalyzer().analyze(w)
        self.assertEqual(result["metrics"]["regions"], 1)
        # No isolation issues
        for issue in result["issues"]:
            self.assertNotEqual(issue.issue_type.value, "isolated_region")

    def test_multiple_regions_trigger_isolation_issue(self):
        w = WorldModel()
        # Two separate 5x5 patches
        for x in range(5):
            for y in range(5):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        for x in range(20, 25):
            for y in range(20, 25):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        result = NavigationAnalyzer().analyze(w)
        self.assertGreaterEqual(result["metrics"]["regions"], 2)
        # Should report isolated regions
        issue_types = {i.issue_type.value for i in result["issues"]}
        self.assertIn("isolated_region", issue_types)

    def test_dead_ends_detected(self):
        w = WorldModel()
        # 5x5 plus a 1x1 dead-end tail
        for x in range(5):
            for y in range(5):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        w.set_tile(Tile(x=6, y=2, z=7, ground=100))
        result = NavigationAnalyzer().analyze(w)
        # (6,2) has only 1 neighbor — a dead end
        self.assertGreaterEqual(result["metrics"]["dead_ends"], 1)


if __name__ == "__main__":
    unittest.main()
