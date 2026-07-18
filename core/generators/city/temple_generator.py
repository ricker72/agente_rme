from typing import Dict, List

from .district_generator import District


def generate_temple_layout(
    district: District, theme: Dict[str, list]
) -> List[Dict[str, object]]:
    floor = theme.get("floors", [415])[0]
    wall = theme.get("walls", [1495])[0]
    decoration = theme.get("decorations", [2153])[0]

    layout = []
    for dx in range(district.width):
        for dy in range(district.height):
            layout.append({"x": district.x + dx, "y": district.y + dy, "ground": floor})

    layout.append({"x": district.x + 4, "y": district.y + 2, "item": decoration})
    layout.append({"x": district.x + 5, "y": district.y + 2, "item": decoration})
    layout.append({"x": district.x + 4, "y": district.y + 6, "item": decoration})
    layout.append({"x": district.x + 5, "y": district.y + 6, "item": decoration})
    layout.append({"x": district.x + 5, "y": district.y + 4, "item": wall})

    return layout
