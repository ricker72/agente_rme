from typing import Dict, List

from .district_generator import District


def generate_market_layout(district: District, theme: Dict[str, list]) -> List[Dict[str, object]]:
    road = theme.get("roads", [415])[0]
    stall = theme.get("decorations", [2151])[0]

    layout = []
    for dx in range(district.width):
        for dy in range(district.height):
            if dx in (0, district.width - 1) or dy in (0, district.height - 1):
                layout.append({"x": district.x + dx, "y": district.y + dy, "ground": road})
            else:
                layout.append({"x": district.x + dx, "y": district.y + dy, "ground": road})

    for i in range(3):
        layout.append({
            "x": district.x + 2 + i * 3,
            "y": district.y + 2,
            "item": stall,
        })
        layout.append({
            "x": district.x + 2 + i * 3,
            "y": district.y + district.height - 3,
            "item": stall,
        })
    return layout
