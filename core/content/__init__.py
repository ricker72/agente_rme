"""
Content Generator Package — Automatic playable content generation.

Generates Quests, Raids, Bosses, Rewards, Missions, Lever Rooms,
and Puzzle Rooms as QuestPackage objects.

Usage:
    from core.content import QuestGenerator, RaidGenerator, BossGenerator

    generator = QuestGenerator(asset_registry, map_designer, world_model)
    quest = generator.generate(level_range=(300, 500))
    # quest is a QuestPackage
"""

from .quest_package import QuestPackage, RoomType
from .map_designer import MapDesigner
from .quest_generator import QuestGenerator
from .raid_generator import RaidGenerator
from .boss_generator import BossGenerator
from .reward_generator import RewardGenerator
from .mission_generator import MissionGenerator

__all__ = [
    "QuestPackage",
    "RoomType",
    "MapDesigner",
    "QuestGenerator",
    "RaidGenerator",
    "BossGenerator",
    "RewardGenerator",
    "MissionGenerator",
]