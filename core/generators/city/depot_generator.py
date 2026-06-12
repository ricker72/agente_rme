from typing import Dict, List

from .district_generator import District


def generate_depot_layout(
    district: District, theme: Dict[str, list]
) -> List[Dict[str, object]]:
    floor = theme.get("floors", [416])[0]
    decoration = theme.get("decorations", [2150])[0]

    layout = []
    for dx in range(district.width):
        for dy in range(district.height):
            layout.append({"x": district.x + dx, "y": district.y + dy, "ground": floor})

    for row in range(2):
        for col in range(2):
            layout.append(
                {
                    "x": district.x + 2 + col * 3,
                    "y": district.y + 2 + row * 3,
                    "item": decoration,
                }
            )

    layout.append({"x": district.x + 1, "y": district.y + 1, "item": decoration})
    return layout
