from __future__ import annotations

from typing import Dict, List

BUILDING_TYPES = [
    "Temple",
    "Depot",
    "House",
    "Guildhall",
    "Market",
    "Castle",
    "Tower",
    "Library",
    "Arena",
    "Harbor",
    "Bridge",
    "QuestRoom",
    "BossRoom",
]


class BuildingClassifier:
    def classify(self, structure: Dict[str, object]) -> str:
        width = int(structure.get("width", 0))
        height = int(structure.get("height", 0))
        area = width * height
        decorations = structure.get("decorations", []) or []
        decor_count = len(decorations)
        connectivity = structure.get("connectivity", {}) or {}
        doors = int(connectivity.get("doors", 0) or 0)
        has_altar = any("altar" in str(item).lower() for item in decorations)
        has_market = any("stall" in str(item).lower() or "market" in str(item).lower() for item in decorations)
        has_storage = any("locker" in str(item).lower() or "crate" in str(item).lower() for item in decorations)
        has_boss = any("throne" in str(item).lower() or "boss" in str(item).lower() for item in decorations)

        if has_altar and area >= 200:
            return "Temple"
        if has_storage and area >= 120 and doors >= 2:
            return "Depot"
        if has_market and area >= 160:
            return "Market"
        if area >= 420 and width >= 18 and height >= 18:
            return "Castle"
        if area >= 250 and width == height and decor_count >= 3:
            return "Guildhall"
        if area >= 120 and width >= 10 and height >= 10 and doors >= 3:
            return "Library"
        if area >= 80 and has_boss:
            return "BossRoom"
        if area >= 100 and decor_count >= 4 and doors <= 2:
            return "House"
        if area <= 60 and doors <= 2:
            return "House"
        if area >= 300 and width >= 12 and height >= 12 and doors >= 2:
            return "Arena"
        if width >= 6 and height <= 4 and doors == 0:
            return "Bridge"
        if width >= 14 and height >= 6 and decor_count >= 2:
            return "Harbor"
        if decor_count >= 2 and width >= 8 and height >= 8:
            return "Tower"
        if area >= 180 and doors >= 2:
            return "QuestRoom"
        return "House"

    def supported_types(self) -> List[str]:
        return BUILDING_TYPES
