
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
        self.generator = BossGenerator(
            self.asset_registry, self.map_designer, self.world_model
        )

    def test_generate_boss(self):
        boss = self.generator.generate_boss((10, 15), "dragon")
        self.assertEqual(boss.level_min, 10)
        self.assertEqual(boss.level_max, 15)
        self.assertIn("Boss", boss.name)
        for ability in boss.objectives[0].split(": ")[1].split(", "):
            self.assertNotIn("TODO", ability)
