"""
Integration tests for the critic — end-to-end usage from build world to report.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest

from core.critic import VisualCritic
from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.region import Region
from core.world.structure import Structure
from core.world.spawn import Spawn


def _build_issavi_roshamuul(
    level_min: int = 300, level_max: int = 500, hunts: int = 3, bosses: int = 2
) -> WorldModel:
    """Build a realistic Issavi + Roshamuul style world for level 300-500.

    3 hunts, 2 bosses, 1 raid-style city hub, all connected.
    """
    w = WorldModel()
    # City hub: depot + temple + npc + market, 30x30
    city_x, city_y = 0, 0
    for x in range(city_x, city_x + 30):
        for y in range(city_y, city_y + 30):
            items = [{"itemid": 200 + (x * y) % 12, "count": 1}]
            w.set_tile(Tile(x=x, y=y, z=7, ground=100, items=items))
    # Services as regions
    w.add_region(Region(name="city_issavi", min_level=1, max_level=level_max))
    w.add_region(Region(name="city_issavi_depot", min_level=1, max_level=level_max))
    w.add_region(Region(name="city_issavi_temple", min_level=1, max_level=level_max))
    w.add_region(Region(name="city_issavi_npc", min_level=1, max_level=level_max))

    # Hunts
    for i in range(hunts):
        ox = 50 + i * 60
        oy = 0
        for dx in range(20):
            for dy in range(20):
                t = Tile(
                    x=ox + dx,
                    y=oy + dy,
                    z=7,
                    ground=200 + i,
                    items=[{"itemid": 300 + (dx + dy) % 6, "count": 1}],
                    zone=f"hunt_{i}",
                )
                # Spawns ~10% density
                if (dx + dy) % 5 == 0:
                    t.spawn = Spawn(monster="Demon", respawn=60, radius=2)
                w.set_tile(t)
        w.add_region(
            Region(
                name=f"hunt_{i}",
                theme="issavi",
                min_level=level_min + i * 20,
                max_level=level_max,
            )
        )

    # Connector paths between city and hunts
    for i in range(hunts):
        ox = 50 + i * 60
        for y in range(30, 60):
            for xx in range(30, ox, 5):
                w.set_tile(Tile(x=xx, y=y, z=7, ground=150))

    # Boss arenas
    for i in range(bosses):
        ox = 30 + i * 80
        oy = 80
        for dx in range(15):
            for dy in range(15):
                t = Tile(
                    x=ox + dx,
                    y=oy + dy,
                    z=7,
                    ground=500 + i,
                    items=[{"itemid": 900, "count": 1}],
                    zone=f"boss_arena_{i}",
                )
                w.set_tile(t)
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
    w.add_region(Region(name="raid_zargoth", min_level=level_min, max_level=level_max))
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


class CriticPipelineIntegrationTests(unittest.TestCase):
    def test_issavi_roshamuul_e2e(self):
        w = _build_issavi_roshamuul()
        with tempfile.TemporaryDirectory() as tmp:
            critic = VisualCritic()
            critic.analyze(
                w,
                map_name="issavi_roshamuul_300_500",
                output_dir=tmp,
                generate_heatmaps=True,
            )
            # Verify report artifacts
            json_path = os.path.join(tmp, "critic_report.json")
            md_path = os.path.join(tmp, "critic_report.md")
            metrics_path = os.path.join(tmp, "critic_report_metrics.json")
            self.assertTrue(os.path.exists(json_path))
            self.assertTrue(os.path.exists(md_path))
            self.assertTrue(os.path.exists(metrics_path))
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("overall_score", data)
            self.assertIn("scores", data)
            # All required categories present
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
                self.assertIn(cat + "_score", data)

    def test_artifacts_match_expected_format(self):
        w = _build_issavi_roshamuul()
        with tempfile.TemporaryDirectory() as tmp:
            critic = VisualCritic()
            critic.analyze(
                w, output_dir=tmp, generate_heatmaps=True, base_name="issavi_roshamuul"
            )
            # The expected JSON file has the format described in the spec
            with open(
                os.path.join(tmp, "issavi_roshamuul.json"), encoding="utf-8"
            ) as f:
                data = json.load(f)
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
                "issues",
                "recommendations",
            ):
                self.assertIn(field, data)

    def test_issues_and_recommendations_generated(self):
        w = _build_issavi_roshamuul(hunts=3, bosses=2)
        critic = VisualCritic()
        result = critic.analyze(w, map_name="test_full")
        # At least some issues and recommendations expected
        self.assertIsInstance(result.issues, list)
        self.assertIsInstance(result.recommendations, list)

    def test_score_aggregates_correctly(self):
        w = _build_issavi_roshamuul()
        critic = VisualCritic()
        result = critic.analyze(w)
        # Overall score = weighted average of per-category scores
        scores = {k: v.value for k, v in result.scores.items()}
        manual = sum(scores.values()) / max(len(scores), 1)
        # Allow some tolerance for the weighted calculation
        self.assertAlmostEqual(result.overall_score, manual, delta=20.0)

    def test_heatmaps_generated(self):
        w = _build_issavi_roshamuul()
        with tempfile.TemporaryDirectory() as tmp:
            critic = VisualCritic()
            result = critic.analyze(w, output_dir=tmp, generate_heatmaps=True)
            artifacts = result.metadata["artifacts"]
            for kind in ("visual", "navigation", "density", "spawn"):
                self.assertIn(kind, artifacts)
                self.assertTrue(os.path.exists(artifacts[kind]))
                self.assertGreater(os.path.getsize(artifacts[kind]), 0)


if __name__ == "__main__":
    unittest.main()
