"""
Tests for the SpawnAnalyzer.
"""

from __future__ import annotations

import unittest

from core.critic.analyzers import SpawnAnalyzer
from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn


class SpawnAnalyzerTests(unittest.TestCase):
    def test_no_spawns(self):
        w = WorldModel()
        for x in range(5):
            for y in range(5):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        result = SpawnAnalyzer().analyze(w)
        self.assertEqual(result["metrics"]["total_spawns"], 0)
        # Critical issue expected
        severities = {i.severity.value for i in result["issues"]}
        self.assertIn("critical", severities)

    def test_good_density(self):
        w = WorldModel()
        for x in range(20):
            for y in range(20):
                t = Tile(x=x, y=y, z=7, ground=100)
                if (x + y) % 5 == 0:
                    t.spawn = Spawn(monster="Rat", respawn=60, radius=2)
                w.set_tile(t)
        result = SpawnAnalyzer().analyze(w)
        # 5% density is the target
        self.assertGreater(result["score"].value, 30.0)

    def test_clusters_detected(self):
        w = WorldModel()
        # Cluster of 5 spawns within 1 tile of each other
        for x, y in [(5, 5), (5, 6), (6, 5), (6, 6), (5, 7)]:
            w.set_tile(
                Tile(
                    x=x,
                    y=y,
                    z=7,
                    ground=100,
                    spawn=Spawn(monster="Rat", respawn=60, radius=2),
                )
            )
        # And some sparse ground
        for x in range(20):
            for y in range(20):
                if w.get_tile(x, y, 7) is None:
                    w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        result = SpawnAnalyzer().analyze(w)
        self.assertGreaterEqual(result["metrics"]["cluster_count"], 1)
        issue_types = {i.issue_type.value for i in result["issues"]}
        self.assertIn("spawn_cluster", issue_types)

    def test_empty_world(self):
        w = WorldModel()
        result = SpawnAnalyzer().analyze(w)
        self.assertEqual(result["score"].value, 0.0)


if __name__ == "__main__":
    unittest.main()
