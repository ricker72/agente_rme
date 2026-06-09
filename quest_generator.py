class QuestGenerator:
    def __init__(self, asset_registry, map_designer, world_model):
        self.asset_registry = asset_registry
        self.map_designer = map_designer
        self.world_model = world_model

    def generate_quest(self, level_range):
        min_level, max_level = level_range
        location = self.map_designer.find_valid_location(min_level, max_level)
        items = self.asset_registry.get_reward_items(min_level)
        return QuestPackage(
            name=f"{location} Adventure",
            level_min=min_level,
            level_max=max_level,
            description=f"Complete the adventure in {location}.",
            objectives=["Defeat {self.world_model.get_enemy_count(min_level)} enemies", "Retrieve {items[0]['name']} from the boss"],
            rewards={
                "gold": self.asset_registry.calculate_gold(min_level),
                "items": items
            }
        )

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
        self.generator = QuestGenerator(self.asset_registry, self.map_designer, self.world_model)

    def test_generate_quest(self):
        quest = self.generator.generate_quest((5, 10))
        self.assertEqual(quest.level_min, 5)
        self.assertEqual(quest.level_max, 10)
        self.assertNotEqual(quest.name, "TODO")
        for obj in quest.objectives:
            self.assertNotIn("TODO", obj)
        for item in quest.rewards.get("items", []):
            self.assertIn("name", item)