"""
RewardGenerator — Generates reward packages as QuestPackage objects.

Rewards are standalone reward events: clearing a room, solving a puzzle,
completing a challenge. Each includes items, gold, and optional bonuses.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .quest_package import QuestPackage, RoomType
from .map_designer import MapDesigner

logger = logging.getLogger(__name__)

# Reward type configurations
_REWARD_TYPES: Dict[str, Dict[str, Any]] = {
    "standard": {"item_count": 2, "gold_mult": 1.0, "rarity_boost": False},
    "rare": {"item_count": 3, "gold_mult": 1.5, "rarity_boost": True},
    "epic": {"item_count": 4, "gold_mult": 2.0, "rarity_boost": True},
    "legendary": {"item_count": 5, "gold_mult": 3.0, "rarity_boost": True},
    "artifacts": {"item_count": 2, "gold_mult": 1.0, "rarity_boost": True},
    "daily": {"item_count": 1, "gold_mult": 0.5, "rarity_boost": False},
    "achievement": {"item_count": 3, "gold_mult": 2.5, "rarity_boost": True},
}


class RewardGenerator:
    """
    Generates reward content for a given level range.

    Usage:
        generator = RewardGenerator(asset_registry, map_designer, world_model)
        reward = generator.generate(level_range=(300, 500), reward_type="epic")
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
        reward_type: str = "standard",
    ) -> QuestPackage:
        """
        Generate a reward package.

        Args:
            level_range: (min_level, max_level) tuple.
            reward_type: Type of reward (standard, rare, epic, legendary,
                         artifacts, daily, achievement).

        Returns:
            A fully populated QuestPackage.
        """
        min_level, max_level = level_range
        config = _REWARD_TYPES.get(
            reward_type, _REWARD_TYPES["standard"]
        )

        # Resolve location
        location = self.map_designer.find_valid_location(min_level, max_level)
        theme = self.map_designer.get_zone_theme(location)

        # Coordinates
        reward_hash = self.map_designer._deterministic_offset(
            f"reward:{location}:{reward_type}", 500
        )
        wx = 4000 + reward_hash
        wy = 4000 + reward_hash * 2
        wz = 7

        # Calculate rewards
        base_gold = self.map_designer.calculate_gold(min_level)
        gold = int(base_gold * config["gold_mult"])
        location_bonus = self.map_designer.get_reward_bonus(min_level)
        total_gold = gold + location_bonus

        items = self.map_designer.select_rewards(
            min_level, count=config["item_count"]
        )

        # Apply rarity boost: upgrade rarity tier for each item
        if config["rarity_boost"]:
            items = [self._boost_rarity(item) for item in items]

        # Objectives
        objectives = self._build_reward_objectives(
            reward_type, location, min_level
        )

        name = f"{reward_type.title()} Reward: {location}"
        description = (
            f"Claim your {reward_type} reward in {location}. "
            f"Complete the challenge to earn {total_gold} gold "
            f"and {len(items)} items."
        )

        package = QuestPackage(
            name=name,
            level_min=min_level,
            level_max=max_level,
            description=description,
            objectives=objectives,
            rewards={"gold": total_gold, "items": items},
            room_type=RoomType.TREASURE,
            location=(wx, wy, wz),
            theme=theme,
            metadata={
                "reward_type": reward_type,
                "location_bonus": location_bonus,
                "rarity_boosted": config["rarity_boost"],
            },
        )

        logger.info(
            "Generated reward '%s' for levels %d-%d",
            name, min_level, max_level,
        )
        return package

    def _build_reward_objectives(
        self,
        reward_type: str,
        location: str,
        min_level: int,
    ) -> List[str]:
        """Build reward-specific objectives."""
        if reward_type == "daily":
            return [
                f"Complete the daily challenge in {location}",
                "Collect the daily reward",
            ]

        if reward_type == "achievement":
            count = max(3, min_level // 20)
            return [
                f"Accomplish {count} feats in {location}",
                "Claim the achievement reward chest",
            ]

        if reward_type == "artifacts":
            return [
                f"Discover the artifact vault in {location}",
                "Solve the guardian riddle",
                "Claim the ancient artifacts",
            ]

        if reward_type == "legendary":
            return [
                f"Prove your worth in {location}",
                "Defeat the legendary guardian",
                "Unlock the legendary treasure vault",
            ]

        if reward_type == "epic":
            return [
                f"Complete the epic challenge in {location}",
                "Survive the trap corridor",
                "Claim the epic loot",
            ]

        if reward_type == "rare":
            return [
                f"Find the hidden cache in {location}",
                "Unlock the rare chest",
            ]

        # standard
        return [
            f"Defeat enemies in {location} to claim the reward",
            "Collect the reward",
        ]

    @staticmethod
    def _boost_rarity(item: Dict[str, Any]) -> Dict[str, Any]:
        """Boost an item's rarity by one tier."""
        rarity_upgrade = {
            "common": "uncommon",
            "uncommon": "rare",
            "rare": "epic",
            "epic": "legendary",
            "legendary": "legendary",  # cap at legendary
        }
        result = dict(item)
        current = result.get("rarity", "common")
        result["rarity"] = rarity_upgrade.get(current, current)
        return result