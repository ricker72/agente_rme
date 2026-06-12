from dataclasses import dataclass
from typing import List


@dataclass
class HuntingRange:
    label: str
    min_level: int
    max_level: int
    recommended_monsters: List[str]


HUNTING_RANGES = [
    HuntingRange(
        label="Beginner",
        min_level=1,
        max_level=50,
        recommended_monsters=["Jungle Troll", "Swamp Troll", "Gargoyle"],
    ),
    HuntingRange(
        label="Intermediate",
        min_level=51,
        max_level=120,
        recommended_monsters=["Vampire", "Hydra", "Demon"],
    ),
    HuntingRange(
        label="Advanced",
        min_level=121,
        max_level=200,
        recommended_monsters=["Frazzlemaw", "Sphinx", "Cloak Of Terror"],
    ),
    HuntingRange(
        label="Endgame",
        min_level=201,
        max_level=999,
        recommended_monsters=["Nightmare", "Demon", "Vampire"],
    ),
]


def get_hunting_range(level: int):
    for range_info in HUNTING_RANGES:
        if range_info.min_level <= level <= range_info.max_level:
            return range_info
    return HUNTING_RANGES[-1]
