from typing import Dict, List

from .district_generator import District


def generate_harbor_layout(district: District, theme: Dict[str, list]) -> List[Dict[str, object]]:
    water = 396
    pier = theme.get("roads", [415])[0]
    boat = theme.get("decorations", [2149])[0]

    layout = []
    for dx in range(district.width):
        for dy in range(district.height):
            current_x = district.x + dx
            current_y = district.y + dy
            if dy >= district.height - 4:
                layout.append({"x": current_x, "y": current_y, "ground": water})
            else:
                layout.append({"x": current_x, "y": current_y, "ground": pier})

    for i in range(2):
        layout.append({"x": district.x + 2 + i * 5, "y": district.y + district.height - 5, "item": boat})
    return layout
