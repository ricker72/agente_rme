class BossGenerator:
    def __init__(self, asset_registry, map_designer, world_model):
        self.asset_registry = asset_registry
        self.map_designer = map_designer
        self.world_model = world_model

    def generate_boss(self, level_range, boss_type="standard"):
        min_level, max_level = level_range
        location = self.map_designer.get_boss_lair(min_level, max_level)
        abilities = self.world_model.get_boss_abilities(boss_type, min_level)
        loot = self.asset_registry.generate_boss_loot(min_level)
        return QuestPackage(
            name=f"{location} Boss Encounter",
            level_min=min_level,
            level_max=max_level,
            description=f"A powerful boss awaits in {location}.",
            objectives=[f"Defeat the boss with abilities: {', '.join(abilities)}"],
            rewards={"items": loot, "gold": self.asset_registry.calculate_boss_gold(min_level)}
        )

# Test file: test_boss_generator.py
import unittest
from boss_generator import BossGenerator
from asset_registry import AssetRegistry
from map_designer import MapDesigner
from world_model import WorldModel

class TestBossGenerator(unittest.TestCase):
    def setUp(self):
        self.asset_registry = AssetRegistry()
        self.map_designer = MapDesigner()
        self.world_model = WorldModel()
        self.generator = BossGenerator(self.asset_registry, self.map_designer, self.world_model)

    def test_generate_boss(self):
        boss = self.generator.generate_boss((10, 15), "dragon")
        self.assertEqual(boss.level_min, 10)
        self.assertEqual(boss.level_max, 15)
        self.assertIn("Boss", boss.name)
        for ability in boss.objectives[0].split(": ")[1].split(", "):
            self.assertNotIn("TODO", ability)