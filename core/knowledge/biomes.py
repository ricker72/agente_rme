from dataclasses import dataclass
from typing import List


@dataclass
class Biome:
    name: str
    grounds: List[int]
    walls: List[int]
    decorations: List[int]
    monsters: List[str]


BIOMES = [
    Biome(
        name="Issavi",
        grounds=[393, 415, 416],
        walls=[1495, 1496, 1497],
        decorations=[2153, 2117, 1803],
        monsters=["Frazzlemaw", "Sphinx", "Cloak Of Terror"],
    ),
    Biome(
        name="Roshamuul",
        grounds=[1053, 1056, 1057],
        walls=[1500, 1501, 1502],
        decorations=[2150, 2151, 2152],
        monsters=["Demon", "Nightmare", "Vampire"],
    ),
    Biome(
        name="Yalahar",
        grounds=[396, 397, 398],
        walls=[1498, 1499, 1503],
        decorations=[2148, 2149, 2154],
        monsters=["Siren", "Gargoyle", "Hydra"],
    ),
    Biome(
        name="Jungle",
        grounds=[514, 513, 516],
        walls=[1504, 1505, 1506],
        decorations=[2155, 2156, 2157],
        monsters=["Jungle Troll", "Panther", "Lizard Snake"],
    ),
    Biome(
        name="Ice",
        grounds=[428, 429, 430],
        walls=[1507, 1508, 1509],
        decorations=[2158, 2159, 2160],
        monsters=["White Deer", "Ice Golem", "Frost Dragon"],
    ),
    Biome(
        name="Desert",
        grounds=[393, 394, 415],
        walls=[1495, 1496, 1497],
        decorations=[2153, 2151, 1803],
        monsters=["Sandcrawler", "Anubis", "Mummy"],
    ),
    Biome(
        name="Swamp",
        grounds=[541, 542, 543],
        walls=[1504, 1505, 1506],
        decorations=[2155, 2156, 2157],
        monsters=["Swamp Troll", "Behemoth", "Mudman"],
    ),
    Biome(
        name="Library",
        grounds=[415, 416, 417],
        walls=[1495, 1498, 1499],
        decorations=[2148, 2150, 2153],
        monsters=["Warlock", "Book Golem", "Mage"],
    ),
    Biome(
        name="Soul War",
        grounds=[1053, 1056, 1057],
        walls=[1500, 1501, 1502],
        decorations=[2150, 2152, 2154],
        monsters=["Demon", "Nightmare", "Vampire"],
    ),
    Biome(
        name="Cobra Bastion",
        grounds=[393, 415, 421],
        walls=[1495, 1500, 1501],
        decorations=[2153, 2156, 2157],
        monsters=["Serpent Spawn", "Cobra Assassin", "Scarab"],
    ),
    Biome(
        name="Falcon Bastion",
        grounds=[415, 416, 421],
        walls=[1495, 1496, 1497],
        decorations=[2155, 2159, 2160],
        monsters=["Falcon Knight", "Harpie", "Wind Spirit"],
    ),
]

BIOME_BY_NAME = {biome.name.lower(): biome for biome in BIOMES}


def get_biome(name: str) -> Biome | None:
    return BIOME_BY_NAME.get(name.lower())
