"""
QuestGenerator — Generates quest content as QuestPackage objects.

Integrates with WorldModel, AssetRegistry, and MapDesigner to produce
playable quest content with objectives, rewards, and location data.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .quest_package import QuestPackage, RoomType
from .map_designer import MapDesigner

logger = logging.getLogger(__name__)


class QuestGenerator:
    """
    Generates quest content for a given level range.

    Usage:
        generator = QuestGenerator(asset_registry, map_designer, world_model)
        quest = generator.generate(level_range=(300, 500))
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
        quest_type: str = "exploration",
    ) -> QuestPackage:
        """
        Generate a quest package for the given level range.

        Args:
            level_range: (min_level, max_level) tuple.
            quest_type: Type of quest (exploration, combat, rescue, collection,
                        boss, lever, puzzle).

        Returns:
            A fully populated QuestPackage.
        """
        min_level, max_level = level_range

        # Resolve location
        location = self.map_designer.find_valid_location(min_level, max_level)
        theme = self.map_designer.get_zone_theme(location)

        # Get zone-level coordinates for WorldModel integration
        self.map_designer._pick_zone(min_level, max_level, hint="quest")
        zone_hash = self.map_designer._deterministic_offset(f"coord:{location}", 500)
        wx = 1000 + zone_hash
        wy = 1000 + zone_hash * 2
        wz = 7

        # Select boss if applicable
        boss = None
        if quest_type in ("boss", "lever", "puzzle"):
            boss = self.map_designer.select_boss(min_level)

        # Build objectives
        objectives = self._build_objectives(quest_type, location, min_level, boss)

        # Select rewards
        rewards_items = self.map_designer.select_rewards(min_level, count=2)
        gold = self.map_designer.calculate_gold(min_level)

        # Enemy count scales with level
        enemy_count = max(3, min_level // 20)

        # Determine room type
        room_type = self._room_type_for_quest(quest_type)

        name = f"{theme.title()} {quest_type.title()}: {location}"
        description = (
            f"Venture into {location} and complete a {quest_type} quest. "
            f"Enemies patrol the area — defeat {enemy_count} foes to proceed."
            if enemy_count > 0
            else f"Venture into {location} and complete a {quest_type} quest."
        )

        package = QuestPackage(
            name=name,
            level_min=min_level,
            level_max=max_level,
            description=description,
            objectives=objectives,
            rewards={"gold": gold, "items": rewards_items},
            room_type=room_type,
            location=(wx, wy, wz),
            enemy_count=enemy_count,
            boss_name=boss["name"] if boss else None,
            theme=theme,
            metadata={"quest_type": quest_type},
        )

        logger.info("Generated quest '%s' for levels %d-%d", name, min_level, max_level)
        return package

    def _build_objectives(
        self,
        quest_type: str,
        location: str,
        min_level: int,
        boss: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Build objective list based on quest type."""
        if quest_type == "lever":
            lever = self.map_designer.get_lever_room(min_level, min_level + 50)
            return list(lever["objectives"])

        if quest_type == "puzzle":
            puzzle = self.map_designer.get_puzzle_room(min_level, min_level + 50)
            return list(puzzle["objectives"])

        if quest_type == "boss" and boss:
            return [
                f"Locate the {boss['name']} in {location}",
                f"Defeat the {boss['name']}",
                "Collect the boss loot",
            ]

        if quest_type == "combat":
            count = max(5, min_level // 10)
            return [
                f"Defeat {count} enemies in {location}",
                "Survive all waves",
                "Return to the quest giver",
            ]

        if quest_type == "rescue":
            return [
                f"Find the captive in {location}",
                "Defeat the guards",
                "Escort the prisoner to safety",
            ]

        if quest_type == "collection":
            count = max(3, min_level // 15)
            return [
                f"Gather {count} artifacts from {location}",
                "Return all artifacts to the historian",
            ]

        # Default: exploration
        return [
            f"Explore {location} and map all pathways",
            "Discover the hidden chamber",
            "Report findings to the quest giver",
        ]

    @staticmethod
    def _room_type_for_quest(quest_type: str) -> RoomType:
        """Map quest type to room type."""
        mapping = {
            "lever": RoomType.LEVER,
            "puzzle": RoomType.PUZZLE,
            "boss": RoomType.BOSS_LAIR,
        }
        return mapping.get(quest_type, RoomType.NONE)
