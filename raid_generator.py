class RaidGenerator:
    def __init__(self, asset_registry, map_designer, world_model):
        self.asset_registry = asset_registry
        self.map_designer = map_designer
        self.world_model = world_model

    def generate_raid(self, level_range, party_size=5):
        min_level, max_level = level_range
        location = self.map_designer.select_raid_zone(min_level, max_level)
        boss = self.world_model.select_boss(min_level)
        rewards = self.asset_registry.get_raid_rewards(min_level)
        return QuestPackage(
            name=f"{location} Raid",
            level_min=min_level,
            level_max=max_level,
            description=f"A raid in {location} against {boss.name}.",
            objectives=[f"Defeat {boss.name} with a party of {party_size} players"],
            rewards={"items": rewards, "gold": self.asset_registry.calculate_raid_gold(min_level)}
        )

# Test file: test_raid_generator.py
import unittest
from raid_generator import RaidGenerator
from asset_registry import AssetRegistry
from map_designer import MapDesigner
from world_model import WorldModel

class TestRaidGenerator(unittest.TestCase):
    def setUp(self):
        self.asset_registry = AssetRegistry()
        self.map_designer = MapDesigner()
        self.world_model = WorldModel()
        self.generator = RaidGenerator(self.asset_registry, self.map_designer, self.world_model)

    def test_generate_raid(self):
        raid = self.generator.generate_raid((15, 20))
        self.assertEqual(raid.level_min, 15)
        self.assertEqual(raid.level_max, 20)
        self.assertIn("Raid", raid.name)
        for obj in raid.objectives:
            self.assertNotIn("TODO", obj)
        self.assertTrue(raid.rewards.get("items"))