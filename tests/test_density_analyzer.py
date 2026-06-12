"""
Tests for the DensityAnalyzer.
"""

from __future__ import annotations

import unittest

from core.critic.analyzers import DensityAnalyzer
from core.world.world_model import WorldModel
from core.world.tile import Tile


class DensityAnalyzerTests(unittest.TestCase):
    def test_empty_world(self):
        w = WorldModel()
        result = DensityAnalyzer().analyze(w)
        self.assertEqual(result["score"].value, 0.0)
        self.assertEqual(result["metrics"]["total_tiles"], 0)

    def test_dense_world_high_score(self):
        w = WorldModel()
        for x in range(10):
            for y in range(10):
                w.set_tile(
                    Tile(
                        x=x,
                        y=y,
                        z=7,
                        ground=100,
                        items=[
                            {"itemid": 200, "count": 1},
                            {"itemid": 201, "count": 1},
                        ],
                    )
                )
        result = DensityAnalyzer().analyze(w)
        self.assertGreaterEqual(result["score"].value, 50.0)
        self.assertEqual(result["metrics"]["total_tiles"], 100)

    def test_sparse_world_lower_score(self):
        w = WorldModel()
        for x in range(10):
            for y in range(10):
                # Only one tile in 50 has content
                items = [{"itemid": 200, "count": 1}] if (x == 0 and y == 0) else []
                w.set_tile(Tile(x=x, y=y, z=7, ground=100, items=items))
        result = DensityAnalyzer().analyze(w)
        # Sparse => lower score
        self.assertLess(result["score"].value, 80.0)

    def test_overdecorated_triggers_issue(self):
        w = WorldModel()
        for x in range(5):
            for y in range(5):
                w.set_tile(
                    Tile(
                        x=x,
                        y=y,
                        z=7,
                        ground=100,
                        items=[{"itemid": i, "count": 1} for i in range(20)],
                    )
                )
        result = DensityAnalyzer().analyze(w)
        issue_types = {i.issue_type.value for i in result["issues"]}
        self.assertIn("overdecorated_area", issue_types)


if __name__ == "__main__":
    unittest.main()
