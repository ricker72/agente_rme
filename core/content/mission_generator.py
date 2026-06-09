"""
MissionGenerator — Generates mission content as QuestPackage objects.

Missions are multi-stage objectives spanning areas of the world.
Each mission includes type-specific objectives, scaled rewards,
and area placement.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .quest_package import QuestPackage, RoomType
from .map_designer import MapDesigner

logger = logging.getLogger(__name__)

# Mission type metadata
_MISSION_TYPES: Dict[str, Dict[str, Any]] = {
    "exploration": {
        "reward_mult": 1.0,
        "enemy_count_base": 3,
        "description_template": (
            "Chart unknown territory in {area}. "
            "Discover hidden chambers and map all pathways."
        ),
    },
    "rescue": {
        "reward_mult": 1.2,
        "enemy_count_base": 8,
        "description_template": (
            "A captive is held in {area}. "
            "Defeat the guards and escort the prisoner to safety."
        ),
    },
    "combat": {
        "reward_mult": 1.5,
        "enemy_count_base": 15,
        "description_template": (
            "Heavy enemy presence detected in {area}. "
            "Eliminate hostiles and secure the zone."
        ),
    },
    "collection": {
        "reward_mult": 1.1,
        "enemy_count_base": 5,
        "description_template": (
            "Ancient relics are scattered across {area}. "
            "Gather them before the enemy does."
        ),
    },
    "escort": {
        "reward_mult": 1.3,
        "enemy_count_base": 10,
        "description_template": (
            "An NPC must travel through dangerous {area}. "
            "Protect them along the route."
        ),
    },
    "stealth": {
        "reward_mult": 1.4,
        "enemy_count_base": 6,
        "description_template": (
            "Infiltrate {area} without being detected. "
            "Retrieve the objective and escape."
        ),
    },
    "boss": {
        "reward_mult": 2.0,
        "enemy_count_base": 12,
        "description_template": (
            "A powerful boss controls {area}. "
            "Clear the path and defeat the boss."
        ),
    },
    "lever": {
        "reward_mult": 1.3,
        "enemy_count_base": 7,
        "description_template": (
            "Hidden mechanisms control access to {area}. "
            "Find and activate the levers to progress."
        ),
    },
    "puzzle": {
        "reward_mult": 1.3,
        "enemy_count_base": 4,
        "description_template": (
            "Ancient puzzles guard treasures in {area}. "
            "Solve each challenge to claim the rewards."
        ),
    },
}


class MissionGenerator:
    """
    Generates mission content for a given level range.

    Usage:
        generator = MissionGenerator(asset_registry, map_designer, world_model)
        mission = generator.generate(level_range=(300, 500), mission_type="combat")
    """

    def __init__(
        self,
        asset_registry: Any,
        map_designer: MapDesigner,
        world_model: Any,
    ):
        self.asset_registry = asset_registry
        self.map_designer = map_designer
        self.world_model = world_model

    def generate(
        self,
        level_range: tuple,
        mission_type: str = "exploration",
    ) -> QuestPackage:
        """
        Generate a mission package.

        Args:
            level_range: (min_level, max_level) tuple.
            mission_type: Type of mission (exploration, rescue, combat,
                          collection, escort, stealth, boss, lever, puzzle).

        Returns:
            A fully populated QuestPackage.
        """
        min_level, max_level = level_range
        config = _MISSION_TYPES.get(
            mission_type, _MISSION_TYPES["exploration"]
        )

        # Resolve area
        area = self.map_designer.select_mission_area(min_level, max_level)
        theme = self.map_designer.get_zone_theme(area)

        # Coordinates
        mission_hash = self.map_designer._deterministic_offset(
            f"mission:{area}:{mission_type}", 500
        )
        wx = 5000 + mission_hash
        wy = 5000 + mission_hash * 2
        wz = 7

        # Build objectives
        if mission_type == "boss":
            boss = self.map_designer.select_boss(min_level)
            objectives = [
                f"Clear the path to {boss['name']}'s lair in {area}",
                f"Defeat {max(5, min_level // 10)} enemies",
                f"Confront and defeat {boss['name']}",
                "Claim the mission rewards",
            ]
            boss_name = boss["name"]
        elif mission_type == "lever":
            lever = self.map_designer.get_lever_room(min_level, max_level)
            objectives = list(lever["objectives"])
            boss_name = None
        elif mission_type == "puzzle":
            puzzle = self.map_designer.get_puzzle_room(min_level, max_level)
            objectives = list(puzzle["objectives"])
            boss_name = None
        else:
            objectives = self.map_designer.get_mission_objectives(
                mission_type, min_level, area
            )
            boss_name = None

        # Rewards
        base_gold = self.map_designer.calculate_gold(min_level)
        gold = int(base_gold * config["reward_mult"])
        item_count = max(2, min_level // 80)
        items = self.map_designer.select_rewards(min_level, count=item_count)

        # Enemy count
        enemy_count = max(
            config["enemy_count_base"], min_level // 12
        )

        name = f"{mission_type.title()} Mission: {area}"
        description = config["description_template"].format(area=area)

        # Determine room type
        room_type_map = {
            "lever": RoomType.LEVER,
            "puzzle": RoomType.PUZZLE,
            "boss": RoomType.BOSS_LAIR,
        }

        package = QuestPackage(
            name=name,
            level_min=min_level,
            level_max=max_level,
            description=description,
            objectives=objectives,
            rewards={"gold": gold, "items": items},
            room_type=room_type_map.get(mission_type, RoomType.NONE),
            location=(wx, wy, wz),
            enemy_count=enemy_count,
            boss_name=boss_name,
            theme=theme,
            metadata={
                "mission_type": mission_type,
                "reward_mult": config["reward_mult"],
            },
        )

        logger.info(
            "Generated mission '%s' for levels %d-%d",
            name, min_level, max_level,
        )
        return package