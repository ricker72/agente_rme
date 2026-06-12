
# Test file: test_quest_generator.py
import unittest
from quest_generator import QuestGenerator
from asset_registry import AssetRegistry
from map_designer import MapDesigner
from world_model import WorldModel


class TestQuestGenerator(unittest.TestCase):
    def setUp(self):
        self.asset_registry = AssetRegistry()
        self.map_designer = MapDesigner()
        self.world_model = WorldModel()
        self.generator = QuestGenerator(
            self.asset_registry, self.map_designer, self.world_model
        )

    def test_generate_quest(self):
        quest = self.generator.generate_quest((5, 10))
        self.assertEqual(quest.level_min, 5)
        self.assertEqual(quest.level_max, 10)
        self.assertNotEqual(quest.name, "TODO")
        for obj in quest.objectives:
            self.assertNotIn("TODO", obj)
        for item in quest.rewards.get("items", []):
            self.assertIn("name", item)
