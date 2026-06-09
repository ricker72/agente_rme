from dataclasses import dataclass
from typing import List

@dataclass
class Theme:
    name: str
    architecture: str
    floor_types: List[int]
    wall_types: List[int]
    decoration_types: List[int]

THEMES = [
    Theme(
        name="issavi",
        architecture="ancient_desert",
        floor_types=[393, 415, 416],
        wall_types=[1495, 1496, 1497],
        decoration_types=[2153, 2117, 1803],
    ),
    Theme(
        name="roshamuul",
        architecture="corrupted_catacomb",
        floor_types=[1053, 1056, 1057],
        wall_types=[1500, 1501, 1502],
        decoration_types=[2150, 2151, 2152],
    ),
    Theme(
        name="yalahar",
        architecture="undersea_ruins",
        floor_types=[396, 397, 398],
        wall_types=[1498, 1499, 1503],
        decoration_types=[2148, 2149, 2154],
    ),
    Theme(
        name="jungle",
        architecture="tropical_temple",
        floor_types=[514, 513, 516],
        wall_types=[1504, 1505, 1506],
        decoration_types=[2155, 2156, 2157],
    ),
    Theme(
        name="ice",
        architecture="frozen_palace",
        floor_types=[428, 429, 430],
        wall_types=[1507, 1508, 1509],
        decoration_types=[2158, 2159, 2160],
    ),
]

THEME_BY_NAME = {theme.name.lower(): theme for theme in THEMES}


def get_theme(name: str):
    return THEME_BY_NAME.get(name.lower())
