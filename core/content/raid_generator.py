"""
RaidGenerator — Generates raid content as QuestPackage objects.

Raids are large-scale group encounters requiring coordinated parties.
Each raid includes a boss, zone, objectives, and scaled rewards.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from .quest_package import QuestPackage, RoomType
from .map_designer import MapDesigner

logger = logging.getLogger(__name__)

# Raid difficulty multipliers
_RAID_MULTIPLIERS = {
    "normal": {"gold_mult": 1.0, "item_count": 3, "enemy_mult": 1.0},
    "hard": {"gold_mult": 1.5, "item_count": 4, "enemy_mult": 1.5},
    "epic": {"gold_mult": 2.0, "item_count": 5, "enemy_mult": 2.0},
}


class RaidGenerator:
    """
    Generates raid content for a given level range.

    Usage:
        generator = RaidGenerator(asset_registry, map_designer, world_model)
        raid = generator.generate(level_range=(300, 500))
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
        party_size: int = 5,
        difficulty: str = "normal",
    ) -> QuestPackage:
        """
        Generate a raid package for the given level range.

        Args:
            level_range: (min_level, max_level) tuple.
            party_size: Number of players expected.
            difficulty: Raid difficulty (normal, hard, epic).

        Returns:
            A fully populated QuestPackage.
        """
        min_level, max_level = level_range
        diff = _RAID_MULTIPLIERS.get(difficulty, _RAID_MULTIPLIERS["normal"])

        # Resolve zone and boss
        zone = self.map_designer.select_raid_zone(min_level, max_level)
        theme = self.map_designer.get_zone_theme(zone)
        boss = self.map_designer.select_boss(min_level)

        # Coordinates from zone
        zone_hash = self.map_designer._deterministic_offset(f"raid:{zone}", 500)
        wx = 2000 + zone_hash
        wy = 2000 + zone_hash * 2
        wz = 7

        # Scale rewards
        base_gold = self.map_designer.calculate_gold(min_level)
        gold = int(base_gold * diff["gold_mult"])
        items = self.map_designer.select_rewards(min_level, count=diff["item_count"])

        # Enemy count
        enemy_count = max(10, int(min_level / 10 * diff["enemy_mult"]))

        # Build objectives
        objectives = self._build_raid_objectives(
            boss, zone, party_size, enemy_count, difficulty
        )

        name = f"{theme.title()} Raid: {zone}"
        description = (
            f"A {difficulty} raid in {zone} against {boss['name']}. "
            f"Gather a party of {party_size} to face this challenge."
        )

        package = QuestPackage(
            name=name,
            level_min=min_level,
            level_max=max_level,
            description=description,
            objectives=objectives,
            rewards={"gold": gold, "items": items},
            room_type=RoomType.ARENA,
            location=(wx, wy, wz),
            enemy_count=enemy_count,
            boss_name=boss["name"],
            theme=theme,
            metadata={
                "raid": True,
                "difficulty": difficulty,
                "party_size": party_size,
                "boss_abilities": boss.get("abilities", []),
            },
        )

        logger.info(
            "Generated raid '%s' for levels %d-%d (%s)",
            name,
            min_level,
            max_level,
            difficulty,
        )
        return package

    def _build_raid_objectives(
        self,
        boss: Dict[str, Any],
        zone: str,
        party_size: int,
        enemy_count: int,
        difficulty: str,
    ) -> List[str]:
        """Build raid-specific objectives."""
        objectives = [
            f"Assemble a party of {party_size} players",
            f"Clear {enemy_count} enemies in {zone}",
        ]

        # Add ability-specific objectives
        abilities = boss.get("abilities", [])
        if abilities:
            objectives.append(f"Counter the boss abilities: {', '.join(abilities)}")

        objectives.extend(
            [
                f"Defeat {boss['name']}",
                "Claim the raid rewards",
            ]
        )

        if difficulty in ("hard", "epic"):
            objectives.insert(2, "Survive the elite guard waves")
            if difficulty == "epic":
                objectives.insert(3, "Endure the final enrage phase")

        return objectives
