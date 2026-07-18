"""
QuestPackage — the universal output type for all content generators.

Every generator (quest, raid, boss, reward, mission) produces a QuestPackage
that contains everything needed to place playable content into a WorldModel.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class RoomType(enum.Enum):
    """Types of special rooms that can appear in content."""

    NONE = "none"
    LEVER = "lever"
    PUZZLE = "puzzle"
    BOSS_LAIR = "boss_lair"
    TREASURE = "treasure"
    ARENA = "arena"


@dataclass
class QuestPackage:
    """
    A self-contained package of playable content ready for world integration.

    Attributes:
        name: Display name of the content.
        level_min: Minimum player level.
        level_max: Maximum player level.
        description: Flavor text / narrative description.
        objectives: List of objective strings the player must complete.
        rewards: Dict with 'gold' (int) and 'items' (list of dicts).
        room_type: The type of room this content generates.
        location: World coordinates where content should be placed (x, y, z).
        enemy_count: Number of enemies to spawn.
        boss_name: Name of the boss monster (if any).
        theme: Visual/gameplay theme string.
        metadata: Arbitrary extra data for advanced integrations.
    """

    name: str
    level_min: int
    level_max: int
    description: str = ""
    objectives: List[str] = field(default_factory=list)
    rewards: Dict[str, Any] = field(default_factory=dict)
    room_type: RoomType = RoomType.NONE
    location: Optional[Tuple[int, int, int]] = None
    enemy_count: int = 0
    boss_name: Optional[str] = None
    theme: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Validate the package. Returns list of error strings (empty = valid)."""
        errors: List[str] = []
        if not self.name:
            errors.append("name is empty")
        if self.level_min < 1:
            errors.append(f"level_min={self.level_min} must be >= 1")
        if self.level_max < self.level_min:
            errors.append(f"level_max={self.level_max} < level_min={self.level_min}")
        if not self.objectives:
            errors.append("objectives list is empty")
        for i, obj in enumerate(self.objectives):
            if not obj or not obj.strip():
                errors.append(f"objective[{i}] is empty")
            elif "TODO" in obj:
                errors.append(f"objective[{i}] contains TODO placeholder")
        if not self.description:
            errors.append("description is empty")
        return errors

    def is_valid(self) -> bool:
        """Check if the package has no validation errors."""
        return len(self.validate()) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "level_min": self.level_min,
            "level_max": self.level_max,
            "description": self.description,
            "objectives": list(self.objectives),
            "rewards": dict(self.rewards),
            "room_type": self.room_type.value,
            "location": list(self.location) if self.location else None,
            "enemy_count": self.enemy_count,
            "boss_name": self.boss_name,
            "theme": self.theme,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> QuestPackage:
        """Deserialize from dictionary."""
        loc = data.get("location")
        if loc is not None:
            loc = tuple(loc)
        room_str = data.get("room_type", "none")
        return cls(
            name=data["name"],
            level_min=data["level_min"],
            level_max=data["level_max"],
            description=data.get("description", ""),
            objectives=data.get("objectives", []),
            rewards=data.get("rewards", {}),
            room_type=RoomType(room_str),
            location=loc,
            enemy_count=data.get("enemy_count", 0),
            boss_name=data.get("boss_name"),
            theme=data.get("theme"),
            metadata=data.get("metadata", {}),
        )
