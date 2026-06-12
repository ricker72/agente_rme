"""
Tests for the Visual Map Critic AI — top-level orchestrator.
"""

from __future__ import annotations

import os
import tempfile
import unittest

from core.critic import VisualCritic, CriticResult
from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.region import Region
from core.world.structure import Structure
from core.world.spawn import Spawn


def _build_simple_world(size: int = 15) -> WorldModel:
    w = WorldModel()
    for x in range(size):
        for y in range(size):
            items = (
                [{"itemid": 100 + (x + y) % 4, "count": 1}] if (x + y) % 2 == 0 else []
            )
            t = Tile(x=x, y=y, z=7, ground=200, items=items)
            w.set_tile(t)
    for x, y in [(3, 3), (4, 3), (5, 3)]:
        t = w.get_tile(x, y, 7)
        if t:
            t.spawn = Spawn(monster="Rat", respawn=60, radius=2)
            t.zone = "hunt_north"
    w.add_region(Region(name="hunt_north", theme="issavi", min_level=50, max_level=150))
    w.add_region(Region(name="city_issavi", theme="issavi", min_level=1, max_level=50))
    w.add_region(Region(name="city_issavi_depot", theme="issavi"))
    w.add_region(Region(name="city_issavi_temple", theme="issavi"))
    w.add_structure(
        Structure(
            name="boss_arena",
            category="boss_room",
            x=10,
            y=10,
            z=7,
            width=8,
            height=8,
            tags=["boss"],
        )
    )
    return w


class VisualCriticTests(unittest.TestCase):
    def test_analyze_simple_world(self):
        w = _build_simple_world()
        critic = VisualCritic()
        result = critic.analyze(w, map_name="simple_test")
        self.assertIsInstance(result, CriticResult)
        self.assertEqual(result.map_name, "simple_test")
        self.assertGreaterEqual(result.overall_score, 0.0)
        self.assertLessEqual(result.overall_score, 100.0)
        for cat in (
            "visual",
            "navigation",
            "density",
            "spawn",
            "hunt",
            "boss",
            "city",
            "decor",
            "pathfinding",
        ):
            self.assertIsNotNone(result.get_score(cat), f"Missing category: {cat}")
            self.assertGreaterEqual(result.get_score(cat).value, 0.0)

    def test_analyze_empty_world(self):
        w = WorldModel()
        critic = VisualCritic()
        result = critic.analyze(w, map_name="empty")
        # Empty world => overall score is at the low end (not necessarily 0 due to defaults)
        self.assertLessEqual(result.overall_score, 30.0)
        # Issues are produced (low_spawn_density, empty region, etc.)
        self.assertGreater(len(result.issues), 0)

    def test_analyze_with_dict_input(self):
        data = {
            "tiles": [
                {
                    "x": 0,
                    "y": 0,
                    "z": 7,
                    "ground": 100,
                    "items": [{"itemid": 200, "count": 1}],
                },
                {"x": 1, "y": 0, "z": 7, "ground": 100, "items": []},
            ],
            "structures": [],
            "regions": [
                {"name": "hunt_a", "min_level": 1, "max_level": 100, "theme": "issavi"}
            ],
        }
        critic = VisualCritic()
        result = critic.analyze(data, map_name="dict_test")
        self.assertIsInstance(result, CriticResult)
        self.assertEqual(result.map_name, "dict_test")

    def test_analyze_saves_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = _build_simple_world()
            critic = VisualCritic()
            result = critic.analyze(
                w,
                map_name="artifacts_test",
                output_dir=tmp,
                generate_heatmaps=True,
            )
            artifacts = result.metadata.get("artifacts", {})
            self.assertIn("json", artifacts)
            self.assertIn("md", artifacts)
            self.assertIn("metrics", artifacts)
            self.assertIn("visual", artifacts)
            self.assertIn("navigation", artifacts)
            self.assertIn("density", artifacts)
            self.assertIn("spawn", artifacts)
            for path in artifacts.values():
                self.assertTrue(os.path.exists(path), f"Missing artifact: {path}")
                self.assertGreater(os.path.getsize(path), 0)

    def test_analyze_handles_invalid_input(self):
        critic = VisualCritic()
        with self.assertRaises(TypeError):
            critic.analyze("not a world")

    def test_artifacts_include_overall_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = _build_simple_world()
            critic = VisualCritic()
            result = critic.analyze(w, output_dir=tmp, base_name="myreport")
            json_path = result.metadata["artifacts"]["json"]
            import json

            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("overall_score", data)
            self.assertIn("scores", data)
            self.assertIn("issues", data)
            self.assertIn("recommendations", data)

    def test_no_heatmaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            w = _build_simple_world()
            critic = VisualCritic()
            result = critic.analyze(w, output_dir=tmp, generate_heatmaps=False)
            artifacts = result.metadata.get("artifacts", {})
            self.assertNotIn("visual", artifacts)
            self.assertNotIn("navigation", artifacts)
            # But JSON/MD are still written
            self.assertIn("json", artifacts)
            self.assertIn("md", artifacts)


if __name__ == "__main__":
    unittest.main()
