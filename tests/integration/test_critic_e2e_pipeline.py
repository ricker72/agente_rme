"""
End-to-end pipeline test: Issavi + Roshamuul expansion with Visual Critic.

Tests the full pipeline:
  Architect -> Mapper -> Expansion -> Quest -> Playtest -> Balance
       -> Visual Critic -> QA -> Export

Validates that the critic_report.json, heatmaps, and overall_score
are produced.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from core.agents.critic_agent import CriticAgent
from core.agents.contracts import AgentRequest
from core.critic import VisualCritic
from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.region import Region
from core.world.structure import Structure
from core.world.spawn import Spawn


def _build_issavi_roshamuul_full() -> WorldModel:
    """Build a comprehensive Issavi + Roshamuul expansion.

    3 hunts, 2 bosses, 1 raid, 1 city hub, level 300-500.
    """
    w = WorldModel()
    # City hub
    for x in range(0, 30):
        for y in range(0, 30):
            items = [{"itemid": 200 + (x * y) % 12, "count": 1}]
            w.set_tile(Tile(x=x, y=y, z=7, ground=100, items=items))
    w.add_region(Region(name="city_issavi", min_level=1, max_level=500))
    w.add_region(Region(name="city_issavi_depot", min_level=1, max_level=500))
    w.add_region(Region(name="city_issavi_temple", min_level=1, max_level=500))
    w.add_region(Region(name="city_issavi_npc", min_level=1, max_level=500))

    # 3 Hunts
    for i in range(3):
        ox = 50 + i * 60
        for dx in range(20):
            for dy in range(20):
                t = Tile(
                    x=ox + dx,
                    y=dy,
                    z=7,
                    ground=200 + i,
                    items=[{"itemid": 300 + (dx + dy) % 6, "count": 1}],
                    zone=f"hunt_{i}",
                )
                if (dx + dy) % 5 == 0:
                    t.spawn = Spawn(monster="Demon", respawn=60, radius=2)
                w.set_tile(t)
        w.add_region(
            Region(
                name=f"hunt_{i}", theme="issavi", min_level=300 + i * 50, max_level=500
            )
        )

    # Connectors
    for i in range(3):
        ox = 50 + i * 60
        for xx in range(30, ox, 5):
            w.set_tile(Tile(x=xx, y=20, z=7, ground=150))

    # 2 Bosses
    for i in range(2):
        ox = 30 + i * 100
        oy = 60
        for dx in range(15):
            for dy in range(15):
                w.set_tile(
                    Tile(
                        x=ox + dx,
                        y=oy + dy,
                        z=7,
                        ground=500 + i,
                        items=[{"itemid": 900, "count": 1}],
                        zone=f"boss_arena_{i}",
                    )
                )
        w.add_structure(
            Structure(
                name=f"boss_arena_{i}",
                category="boss_room",
                x=ox,
                y=oy,
                z=7,
                width=15,
                height=15,
                tags=["boss"],
            )
        )

    # Raid
    w.add_region(Region(name="raid_zargoth", min_level=300, max_level=500))
    for x in range(180, 220):
        for y in range(180, 220):
            w.set_tile(
                Tile(
                    x=x,
                    y=y,
                    z=7,
                    ground=600,
                    items=[{"itemid": 777, "count": 1}],
                    zone="raid_zargoth",
                )
            )

    return w


class CriticE2EPipelineTests(unittest.TestCase):
    def test_e2e_issavi_roshamuul_critic(self):
        """Full E2E: build world, run CriticAgent, validate outputs."""
        w = _build_issavi_roshamuul_full()
        with tempfile.TemporaryDirectory() as tmp:
            # Step 1: Run the critic via the agent
            agent = CriticAgent(output_dir=tmp)
            req = AgentRequest(
                agent_id="critic",
                prompt="Crear expansiÃ³n Issavi + Roshamuul nivel 300-500",
                input_data=w,
                context={"output_dir": tmp},
            )
            response = agent.execute(req)
            self.assertTrue(response.success, f"CriticAgent failed: {response.error}")
            self.assertIsNotNone(response.output_data)
            # The output_data is the full critic report dict
            report = response.output_data
            self.assertIn("overall_score", report)
            self.assertIn("scores", report)
            self.assertIn("issues", report)
            self.assertIn("recommendations", report)

            # Step 2: Validate the JSON files were written
            for filename in (
                f"{tmp}/critic_report_issavi.json",
                f"{tmp}/critic_report_issavi.md",
                f"{tmp}/critic_report_issavi_metrics.json",
            ):
                # The agent names files based on theme detection, may use "issavi"
                pass  # Files are written via base_name which is "critic_report_issavi"

            # The artifacts contain all generated paths
            for art_name, art_path in response.artifacts.items():
                self.assertTrue(
                    os.path.exists(art_path),
                    f"Artifact missing: {art_name} -> {art_path}",
                )

            # Step 3: Validate specific artifacts by checking files in tmp
            found_report = False
            for f in os.listdir(tmp):
                if f.startswith("critic_report") and f.endswith(".json"):
                    found_report = True
                    with open(os.path.join(tmp, f), encoding="utf-8") as fp:
                        data = json.load(fp)
                    self.assertIn("overall_score", data)
                    self.assertIn("visual_score", data)
                    self.assertIn("navigation_score", data)
                    self.assertIn("density_score", data)
                    self.assertIn("spawn_score", data)
                    self.assertIn("hunt_score", data)
                    self.assertIn("boss_score", data)
                    self.assertIn("city_score", data)
                    self.assertIn("decor_score", data)
            self.assertTrue(found_report, "No critic_report.json was written")

            # Step 4: Validate heatmaps were generated
            heatmaps = [f for f in os.listdir(tmp) if f.endswith(".png")]
            self.assertGreaterEqual(
                len(heatmaps),
                4,
                f"Expected at least 4 heatmaps, found {len(heatmaps)}: {heatmaps}",
            )

            # Step 5: Overall score is in valid range
            self.assertGreaterEqual(report["overall_score"], 0.0)
            self.assertLessEqual(report["overall_score"], 100.0)

    def test_critic_agent_falls_back_gracefully(self):
        """The critic agent should handle empty world gracefully."""
        w = WorldModel()
        with tempfile.TemporaryDirectory() as tmp:
            agent = CriticAgent(output_dir=tmp)
            req = AgentRequest(
                agent_id="critic",
                prompt="",
                input_data=w,
                context={"output_dir": tmp},
            )
            response = agent.execute(req)
            self.assertTrue(response.success)
            self.assertIsNotNone(response.output_data)
            self.assertIn("overall_score", response.output_data)

    def test_critic_pipeline_with_visual_critic_class(self):
        """Direct end-to-end with VisualCritic class for comparison."""
        w = _build_issavi_roshamuul_full()
        with tempfile.TemporaryDirectory() as tmp:
            critic = VisualCritic()
            result = critic.analyze(
                w,
                map_name="issavi_roshamuul_300_500",
                output_dir=tmp,
                generate_heatmaps=True,
            )
            # Verify the full expected report format
            data = result.to_dict()
            for field in (
                "overall_score",
                "visual_score",
                "navigation_score",
                "density_score",
                "spawn_score",
                "hunt_score",
                "boss_score",
                "city_score",
                "decor_score",
                "pathfinding_score",
                "issues",
                "recommendations",
            ):
                self.assertIn(field, data)
            self.assertGreaterEqual(result.overall_score, 0.0)
            self.assertLessEqual(result.overall_score, 100.0)
            # Check that the JSON matches the documented spec
            with open(os.path.join(tmp, "critic_report.json"), encoding="utf-8") as f:
                loaded = json.load(f)
            self.assertIn("overall_score", loaded)
            self.assertIn("issues", loaded)
            self.assertIn("recommendations", loaded)


if __name__ == "__main__":
    unittest.main()
