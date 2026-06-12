
# Test file: test_mission_generator.py
import unittest
from mission_generator import MissionGenerator
from asset_registry import AssetRegistry
from map_designer import MapDesigner
from world_model import WorldModel


class TestMissionGenerator(unittest.TestCase):
    def setUp(self):
        self.asset_registry = AssetRegistry()
        self.map_designer = MapDesigner()
        self.world_model = WorldModel()
        self.generator = MissionGenerator(
            self.asset_registry, self.map_designer, self.world_model
        )

    def test_generate_mission(self):
        mission = self.generator.generate_mission((20, 25), "rescue")
        self.assertEqual(mission.level_min, 20)
        self.assertEqual(mission.level_max, 25)
        self.assertIn("rescue", mission.name.lower())
        self.assertTrue(len(mission.objectives) > 0)
        for obj in mission.objectives:
            self.assertNotIn("TODO", obj)
