"""
Integration tests: the critic integrates with the export pipeline.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from core.critic import VisualCritic
from core.world.world_model import WorldModel
from core.world.tile import Tile


class CriticExportIntegrationTests(unittest.TestCase):

    def test_export_full_set(self):
        """All required export files are produced: critic_report.json / md / metrics."""
        w = WorldModel()
        for x in range(20):
            for y in range(20):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        with tempfile.TemporaryDirectory() as tmp:
            critic = VisualCritic()
            critic.analyze(w, output_dir=tmp, base_name="report")
            # Required: critic_report.json, critic_report.md, critic_report_metrics.json
            for name in ("report.json", "report.md", "report_metrics.json"):
                self.assertTrue(os.path.exists(os.path.join(tmp, name)),
                                f"Missing {name}")
            with open(os.path.join(tmp, "report.json"), encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("overall_score", data)
            self.assertIn("issues", data)
            self.assertIn("recommendations", data)

    def test_export_custom_base_name(self):
        w = WorldModel()
        w.set_tile(Tile(x=0, y=0, z=7, ground=100))
        with tempfile.TemporaryDirectory() as tmp:
            critic = VisualCritic()
            critic.analyze(w, output_dir=tmp, base_name="issavi_300")
            self.assertTrue(os.path.exists(os.path.join(tmp, "issavi_300.json")))

    def test_export_heatmaps(self):
        w = WorldModel()
        for x in range(10):
            for y in range(10):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        with tempfile.TemporaryDirectory() as tmp:
            critic = VisualCritic()
            result = critic.analyze(w, output_dir=tmp, generate_heatmaps=True,
                                    base_name="h")
            self.assertIn("visual", result.metadata["artifacts"])
            self.assertIn("navigation", result.metadata["artifacts"])
            self.assertIn("density", result.metadata["artifacts"])
            self.assertIn("spawn", result.metadata["artifacts"])

    def test_md_contains_table(self):
        w = WorldModel()
        for x in range(5):
            for y in range(5):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        with tempfile.TemporaryDirectory() as tmp:
            critic = VisualCritic()
            critic.analyze(w, output_dir=tmp, base_name="mdtest")
            with open(os.path.join(tmp, "mdtest.md"), encoding="utf-8") as f:
                content = f.read()
            self.assertIn("# Critic Report", content)
            self.assertIn("Per-category scores", content)
            self.assertIn("Overall Score", content)


if __name__ == "__main__":
    unittest.main()
