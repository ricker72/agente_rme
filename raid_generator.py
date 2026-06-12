
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
        self.generator = RaidGenerator(
            self.asset_registry, self.map_designer, self.world_model
        )

    def test_generate_raid(self):
        raid = self.generator.generate_raid((15, 20))
        self.assertEqual(raid.level_min, 15)
        self.assertEqual(raid.level_max, 20)
        self.assertIn("Raid", raid.name)
        for obj in raid.objectives:
            self.assertNotIn("TODO", obj)
        self.assertTrue(raid.rewards.get("items"))
