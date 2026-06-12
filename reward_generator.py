
# Test file: test_reward_generator.py
import unittest
from reward_generator import RewardGenerator
from asset_registry import AssetRegistry
from map_designer import MapDesigner
from world_model import WorldModel


class TestRewardGenerator(unittest.TestCase):
    def setUp(self):
        self.asset_registry = AssetRegistry()
        self.map_designer = MapDesigner()
        self.world_model = WorldModel()
        self.generator = RewardGenerator(
            self.asset_registry, self.map_designer, self.world_model
        )

    def test_generate_reward(self):
        reward = self.generator.generate_reward((8, 12), "artifacts")
        self.assertEqual(reward.level_min, 8)
        self.assertIn("artifacts", reward.name)
        self.assertNotIn("TODO", reward.name)
        self.assertIsInstance(reward.rewards.get("items")[0], dict)
