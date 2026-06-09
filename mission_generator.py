class MissionGenerator:
    def __init__(self, asset_registry, map_designer, world_model):
        self.asset_registry = asset_registry
        self.map_designer = map_designer
        self.world_model = world_model

    def generate_mission(self, level_range, mission_type="exploration"):
        min_level, max_level = level_range
        area = self.map_designer.select_mission_area(min_level, max_level)
        objectives = self.world_model.generate_mission_objectives(mission_type, min_level)
        rewards = self.asset_registry.get_mission_rewards(min_level, mission_type)
        return QuestPackage(
            name=f"{mission_type.title()} Mission: {area}",
            level_min=min_level,
            level_max=max_level,
            description=f"Embark on a {mission_type} mission in {area}.",
            objectives=objectives,
            rewards=rewards
        )

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
        self.generator = MissionGenerator(self.asset_registry, self.map_designer, self.world_model)

    def test_generate_mission(self):
        mission = self.generator.generate_mission((20, 25), "rescue")
        self.assertEqual(mission.level_min, 20)
        self.assertEqual(mission.level_max, 25)
        self.assertIn("rescue", mission.name.lower())
        self.assertTrue(len(mission.objectives) > 0)
        for obj in mission.objectives:
            self.assertNotIn("TODO", obj)