"""
BossGenerator — Generates boss encounter content as QuestPackage objects.

Each boss encounter includes the boss definition, lair location,
abilities, loot table, and encounter objectives.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from .quest_package import QuestPackage, RoomType
from .map_designer import MapDesigner

logger = logging.getLogger(__name__)


class BossGenerator:
    """
    Generates boss encounter content for a given level range.

    Usage:
        generator = BossGenerator(asset_registry, map_designer, world_model)
        boss = generator.generate(level_range=(300, 500), boss_type="dragon")
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
        boss_type: Optional[str] = None,
    ) -> QuestPackage:
        """
        Generate a boss encounter package.

        Args:
            level_range: (min_level, max_level) tuple.
            boss_type: Optional hint for boss selection (e.g. 'dragon',
                       'undead', 'demon'). Used as metadata; the actual
                       boss is selected by level from MapDesigner pools.

        Returns:
            A fully populated QuestPackage.
        """
        min_level, max_level = level_range

        # Resolve location and boss
        lair = self.map_designer.get_boss_lair(min_level, max_level)
        theme = self.map_designer.get_zone_theme(lair)
        boss = self.map_designer.select_boss(min_level, boss_type)

        # Coordinates from lair
        lair_hash = self.map_designer._deterministic_offset(f"boss:{lair}", 500)
        wx = 3000 + lair_hash
        wy = 3000 + lair_hash * 2
        wz = 7

        # Build loot
        loot_items = self.map_designer.select_rewards(min_level, count=3)
        gold = self.map_designer.calculate_gold(min_level) * 3

        # Objectives
        abilities = boss.get("abilities", [])
        objectives = [
            f"Navigate to the {lair} boss chamber",
            (
                f"Prepare for abilities: {', '.join(abilities)}"
                if abilities
                else "Prepare for the encounter"
            ),
            f"Defeat the {boss['name']}",
            "Claim the boss loot",
        ]

        # Enemy count for trash mobs before boss
        enemy_count = max(5, min_level // 15)

        name = f"{theme.title()} Boss: {boss['name']}"
        description = (
            f"A powerful {boss['name']} awaits in {lair}. "
            f"This boss wields {', '.join(abilities[:2])} "
            f"and commands {enemy_count} minions."
            if abilities
            else f"A powerful {boss['name']} awaits in {lair}."
        )

        package = QuestPackage(
            name=name,
            level_min=min_level,
            level_max=max_level,
            description=description,
            objectives=objectives,
            rewards={"gold": gold, "items": loot_items},
            room_type=RoomType.BOSS_LAIR,
            location=(wx, wy, wz),
            enemy_count=enemy_count,
            boss_name=boss["name"],
            theme=theme,
            metadata={
                "boss_type": boss_type or "standard",
                "abilities": abilities,
                "boss_hp": self._estimate_boss_hp(min_level),
                "boss_damage": self._estimate_boss_damage(min_level),
            },
        )

        logger.info(
            "Generated boss encounter '%s' for levels %d-%d",
            name,
            min_level,
            max_level,
        )
        return package

    @staticmethod
    def _estimate_boss_hp(min_level: int) -> int:
        """Estimate boss HP based on level."""
        return max(1000, min_level * 50)

    @staticmethod
    def _estimate_boss_damage(min_level: int) -> int:
        """Estimate boss damage based on level."""
        return max(100, min_level * 8)
