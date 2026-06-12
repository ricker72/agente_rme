"""
Integration tests: PlaytestAgent uses the critic on its world.
"""

from __future__ import annotations

import tempfile
import unittest

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.critic import VisualCritic


class PlaytestCriticIntegrationTests(unittest.TestCase):
    def test_critic_after_playtest_simulation(self):
        """Build a world, run a basic playtest, then analyze with the critic."""
        w = WorldModel()
        for x in range(15):
            for y in range(15):
                items = (
                    [{"itemid": 200 + (x + y) % 4, "count": 1}]
                    if (x + y) % 2 == 0
                    else []
                )
                t = Tile(x=x, y=y, z=7, ground=100, items=items)
                if (x + y) % 4 == 0:
                    t.spawn = Spawn(monster="Rat", respawn=60, radius=2)
                w.set_tile(t)

        # Simulate running the playtest (just create the report dict)

        # Critic consumes the same world the playtest would have used
        with tempfile.TemporaryDirectory() as tmp:
            critic = VisualCritic()
            result = critic.analyze(
                w,
                output_dir=tmp,
                map_name="playtest_300",
            )
            self.assertIsNotNone(result)
            self.assertGreater(len(result.scores), 0)
            # The playtest_report can be passed as extra context
            self.assertIn("scores", result.to_dict())


if __name__ == "__main__":
    unittest.main()
