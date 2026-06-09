class RewardGenerator:
    def __init__(self, asset_registry, map_designer, world_model):
        self.asset_registry = asset_registry
        self.map_designer = map_designer
        self.world_model = world_model

    def generate_reward(self, level_range, reward_type="standard"):
        min_level, max_level = level_range
        reward_item = self.asset_registry.get_reward_item(reward_type, min_level)
        gold_amount = self.asset_registry.calculate_gold(min_level)
        location_bonus = self.map_designer.get_reward_bonus(min_level)
        return QuestPackage(
            name=f"{reward_type} Reward",
            level_min=min_level,
            level_max=max_level,
            description=f"Claim your {reward_type} reward in the area.",
            objectives=["Defeat enemies to claim reward"],
            rewards={
                "items": [{"name": reward_item, "rarity": "epic"}],
                "gold": gold_amount + location_bonus
            }
        )

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
        self.generator = RewardGenerator(self.asset_registry, self.map_designer, self.world_model)

    def test_generate_reward(self):
        reward = self.generator.generate_reward((8, 12), "artifacts")
        self.assertEqual(reward.level_min, 8)
        self.assertIn("artifacts", reward.name)
        self.assertNotIn("TODO", reward.name)
        self.assertIsInstance(reward.rewards.get("items")[0], dict)