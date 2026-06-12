from dataclasses import dataclass
from typing import List, Dict

from .district_generator import District


@dataclass
class Building:
    name: str
    type: str
    x: int
    y: int
    width: int
    height: int
    style: str


def generate_buildings(
    districts: List[District], theme: Dict[str, list]
) -> List[Building]:
    buildings: List[Building] = []
    for district in districts:
        if district.type == "Residential":
            buildings.extend(_generate_residential_dwellings(district, theme))
        elif district.type == "Training":
            buildings.append(
                Building(
                    name="Guildhall Training",
                    type="guildhall",
                    x=district.x + 1,
                    y=district.y + 1,
                    width=8,
                    height=6,
                    style="guildhall",
                )
            )
        elif district.type == "Industrial":
            buildings.append(
                Building(
                    name="Workshop",
                    type="shop",
                    x=district.x + 2,
                    y=district.y + 2,
                    width=8,
                    height=6,
                    style="shop",
                )
            )
        elif district.type == "HuntingGate":
            buildings.append(
                Building(
                    name="Hunting Gate",
                    type="gate",
                    x=district.x + 3,
                    y=district.y + 3,
                    width=6,
                    height=4,
                    style="gate",
                )
            )
    return buildings


def _generate_residential_dwellings(
    district: District, theme: Dict[str, list]
) -> List[Building]:
    houses: List[Building] = []
    left = district.x + 1
    top = district.y + 1
    houses.append(
        Building(
            name="Casa Pequeña",
            type="house_small",
            x=left,
            y=top,
            width=4,
            height=4,
            style="house_small",
        )
    )
    houses.append(
        Building(
            name="Casa Media",
            type="house_medium",
            x=left + 5,
            y=top,
            width=5,
            height=4,
            style="house_medium",
        )
    )
    houses.append(
        Building(
            name="Casa Grande",
            type="house_large",
            x=left,
            y=top + 5,
            width=6,
            height=5,
            style="house_large",
        )
    )
    return houses
