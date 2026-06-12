"""
Tests for the BossRoomAnalyzer.
"""

from __future__ import annotations

import unittest

from core.critic.analyzers import BossRoomAnalyzer
from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.structure import Structure
from core.world.region import Region


def _open_arena(size: int = 10) -> WorldModel:
    """Build a simple open arena (no walls) so it has many escape routes."""
    w = WorldModel()
    for x in range(size):
        for y in range(size):
            w.set_tile(Tile(x=x, y=y, z=7, ground=100))
    # Surround with more open ground so the arena has many boundary exits
    for x in range(-3, size + 3):
        for y in range(-3, size + 3):
            if 0 <= x < size and 0 <= y < size:
                continue
            w.set_tile(Tile(x=x, y=y, z=7, ground=100))
    return w


class BossRoomAnalyzerTests(unittest.TestCase):
    def test_no_bosses(self):
        w = WorldModel()
        for x in range(5):
            for y in range(5):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        result = BossRoomAnalyzer().analyze(w)
        self.assertEqual(result["metrics"]["bosses"], 0)
        titles = [r.title.lower() for r in result["recommendations"]]
        self.assertTrue(any("arena" in t or "boss" in t for t in titles))

    def test_small_arena_triggers_invalid(self):
        w = WorldModel()
        for x in range(3):
            for y in range(3):
                w.set_tile(Tile(x=x, y=y, z=7, ground=100))
        w.add_structure(
            Structure(
                name="boss_small",
                category="boss_room",
                x=0,
                y=0,
                z=7,
                width=3,
                height=3,
                tags=["boss"],
            )
        )
        result = BossRoomAnalyzer().analyze(w)
        issue_types = {i.issue_type.value for i in result["issues"]}
        self.assertIn("invalid_boss_room", issue_types)

    def test_open_arena_has_no_escape_issue(self):
        w = _open_arena(15)
        w.add_structure(
            Structure(
                name="boss_open",
                category="boss_room",
                x=0,
                y=0,
                z=7,
                width=15,
                height=15,
                tags=["boss"],
            )
        )
        result = BossRoomAnalyzer().analyze(w)
        self.assertEqual(result["metrics"]["bosses"], 1)
        issue_types = {i.issue_type.value for i in result["issues"]}
        self.assertNotIn("boss_no_escape", issue_types)

    def test_enclosed_arena_no_exit(self):
        w = WorldModel()
        # 5x5 enclosed arena with a wall around it (no exit)
        for x in range(5):
            for y in range(5):
                # Walls everywhere; boss is in the middle on ground
                t = Tile(x=x, y=y, z=7, ground=None)  # no ground (wall)
                # but the center has ground
                if 1 <= x <= 3 and 1 <= y <= 3:
                    t.ground = 100
                w.set_tile(t)
        w.add_structure(
            Structure(
                name="boss_cage",
                category="boss_room",
                x=1,
                y=1,
                z=7,
                width=3,
                height=3,
                tags=["boss"],
            )
        )
        result = BossRoomAnalyzer().analyze(w)
        # There must be at least 1 issue (either no escape or invalid)
        self.assertGreaterEqual(len(result["issues"]), 1)

    def test_empty_world_default_score(self):
        w = WorldModel()
        result = BossRoomAnalyzer().analyze(w)
        self.assertEqual(result["score"].value, 60.0)

    def test_region_named_boss_arena(self):
        w = WorldModel()
        w.add_region(Region(name="boss_dragon_lair", min_level=200, max_level=300))
        result = BossRoomAnalyzer().analyze(w)
        self.assertGreaterEqual(result["metrics"]["bosses"], 1)

    def test_score_in_valid_range(self):
        w = _open_arena(15)
        w.add_structure(
            Structure(
                name="boss_a",
                category="boss_room",
                x=0,
                y=0,
                z=7,
                width=15,
                height=15,
                tags=["boss"],
            )
        )
        result = BossRoomAnalyzer().analyze(w)
        self.assertGreaterEqual(result["score"].value, 0.0)
        self.assertLessEqual(result["score"].value, 100.0)


if __name__ == "__main__":
    unittest.main()
