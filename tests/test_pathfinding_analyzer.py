"""
Tests for the PathfindingAnalyzer and its A*/BFS/Dijkstra algorithms.
"""

from __future__ import annotations

import math
import unittest

from core.critic.analyzers.pathfinding_analyzer import (
    bfs, dijkstra, astar, WalkableGraph, octile_heuristic,
    octile_cost, manhattan_heuristic, PathfindingAnalyzer,
)
from core.world.world_model import WorldModel
from core.world.tile import Tile


def _linear_world(length: int = 10) -> WorldModel:
    """A linear chain of ground tiles along the x axis."""
    w = WorldModel()
    for x in range(length):
        w.set_tile(Tile(x=x, y=0, z=7, ground=100))
    return w


class AlgorithmTests(unittest.TestCase):

    def test_bfs_finds_path(self):
        w = _linear_world(5)
        g = WalkableGraph(w).build()
        path = bfs((0, 0, 7), (4, 0, 7), g.neighbors_fn)
        self.assertIsNotNone(path)
        self.assertEqual(path[0], (0, 0, 7))
        self.assertEqual(path[-1], (4, 0, 7))
        self.assertEqual(len(path), 5)

    def test_bfs_no_path(self):
        w = WorldModel()
        w.set_tile(Tile(x=0, y=0, z=7, ground=100))
        g = WalkableGraph(w).build()
        path = bfs((0, 0, 7), (5, 0, 7), g.neighbors_fn)
        self.assertIsNone(path)

    def test_dijkstra_shortest(self):
        w = _linear_world(5)
        g = WalkableGraph(w).build()
        path = dijkstra((0, 0, 7), (4, 0, 7), g.neighbors_fn, octile_cost)
        self.assertIsNotNone(path)
        self.assertEqual(path[0], (0, 0, 7))
        self.assertEqual(path[-1], (4, 0, 7))

    def test_astar_shortest(self):
        w = _linear_world(5)
        g = WalkableGraph(w).build()
        path = astar((0, 0, 7), (4, 0, 7), g.neighbors_fn,
                     octile_heuristic, octile_cost)
        self.assertIsNotNone(path)
        self.assertEqual(path[-1], (4, 0, 7))

    def test_heuristics_admissible(self):
        a = (0, 0, 7)
        b = (5, 3, 7)
        h = octile_heuristic(a, b)
        # Actual cost (cardinal only): |5|+|3| = 8
        self.assertLessEqual(h, 8.0 + 1e-9)
        # Manhattan
        self.assertEqual(manhattan_heuristic(a, b), 8.0)
        # Octile cost
        self.assertEqual(octile_cost((0, 0, 7), (1, 0, 7)), 1.0)
        self.assertEqual(octile_cost((0, 0, 7), (1, 1, 7)), math.sqrt(2))
        self.assertEqual(octile_cost((0, 0, 7), (0, 0, 8)), 1.5)

    def test_bfs_same_start_goal(self):
        path = bfs((0, 0, 7), (0, 0, 7), lambda p: [])
        self.assertEqual(path, [(0, 0, 7)])

    def test_astar_no_path(self):
        w = WorldModel()
        w.set_tile(Tile(x=0, y=0, z=7, ground=100))
        g = WalkableGraph(w).build()
        path = astar((0, 0, 7), (5, 0, 7), g.neighbors_fn,
                     octile_heuristic, octile_cost)
        self.assertIsNone(path)

    def test_dijkstra_no_path(self):
        w = WorldModel()
        w.set_tile(Tile(x=0, y=0, z=7, ground=100))
        g = WalkableGraph(w).build()
        path = dijkstra((0, 0, 7), (5, 0, 7), g.neighbors_fn, octile_cost)
        self.assertIsNone(path)


class PathfindingAnalyzerTests(unittest.TestCase):

    def test_empty_world(self):
        w = WorldModel()
        result = PathfindingAnalyzer().analyze(w)
        self.assertEqual(result["score"].value, 0.0)
        severities = {i.severity.value for i in result["issues"]}
        self.assertIn("critical", severities)

    def test_simple_path(self):
        w = _linear_world(20)
        result = PathfindingAnalyzer().analyze(w)
        self.assertGreater(result["score"].value, 60.0)
        self.assertEqual(result["metrics"]["reachable_tiles"],
                         result["metrics"]["walkable_tiles"])

    def test_disconnected_zones(self):
        w = WorldModel()
        for x in range(5):
            w.set_tile(Tile(x=x, y=0, z=7, ground=100))
        for x in range(20, 25):
            w.set_tile(Tile(x=x, y=0, z=7, ground=100))
        result = PathfindingAnalyzer().analyze(w)
        # Some tiles unreachable => either isolated_region or bottleneck issue
        issue_types = {i.issue_type.value for i in result["issues"]}
        self.assertTrue(
            "isolated_region" in issue_types or "bottleneck" in issue_types,
            f"Expected isolated_region or bottleneck, got: {issue_types}",
        )

    def test_walkable_graph_find_entry(self):
        w = _linear_world(5)
        g = WalkableGraph(w).build()
        ep = g.find_entry_point()
        self.assertIsNotNone(ep)
        self.assertIn(ep, g.positions)

    def test_walkable_graph_neighbors(self):
        w = _linear_world(5)
        g = WalkableGraph(w).build()
        n = g.neighbors((2, 0, 7), allow_z_change=True)
        # Has 2 neighbors in y=0 plus 2 in y=1 (which don't exist)
        self.assertIn((1, 0, 7), n)
        self.assertIn((3, 0, 7), n)

    def test_walkable_graph_is_walkable(self):
        w = _linear_world(3)
        g = WalkableGraph(w).build()
        self.assertTrue(g.is_walkable((0, 0, 7)))
        self.assertFalse(g.is_walkable((100, 100, 7)))


if __name__ == "__main__":
    unittest.main()
