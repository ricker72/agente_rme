from dataclasses import dataclass
from typing import List

@dataclass
class City:
    name: str
    style: str
    roads: List[int]
    walls: List[int]
    floors: List[int]
    decorations: List[int]

CITIES = [
    City(
        name="Thais",
        style="medieval_city",
        roads=[393, 415],
        walls=[1495, 1498],
        floors=[416, 417],
        decorations=[2148, 2150],
    ),
    City(
        name="Venore",
        style="maritime_city",
        roads=[396, 397],
        walls=[1499, 1503],
        floors=[398, 399],
        decorations=[2149, 2154],
    ),
    City(
        name="Yalahar",
        style="ancient_ruins",
        roads=[415, 416],
        walls=[1498, 1499],
        floors=[396, 370],
        decorations=[2148, 2152],
    ),
    City(
        name="Issavi",
        style="ancient_desert",
        roads=[415, 416],
        walls=[1495, 1496, 1497],
        floors=[393, 415, 416],
        decorations=[2153, 2117, 1803],
    ),
]

CITY_BY_NAME = {city.name.lower(): city for city in CITIES}


def get_city(name: str):
    return CITY_BY_NAME.get(name.lower())
