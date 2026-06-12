from collections import Counter
from typing import Dict, List


class CityAnalyzer:
    def detect_districts(
        self, rooms: List[dict], tiles: Dict[str, int]
    ) -> Dict[str, object]:
        district_types = Counter()
        for room in rooms:
            name = room.get("name", "").lower()
            if "temple" in name:
                district_types["Temple"] += 1
            elif "depot" in name:
                district_types["Depot"] += 1
            elif "market" in name or "plaza" in name:
                district_types["Market"] += 1
            elif "harbor" in name or "dock" in name:
                district_types["Harbor"] += 1
            elif "house" in name or "residential" in name:
                district_types["Residential"] += 1
            elif "castle" in name:
                district_types["Castle"] += 1
        return {
            "district_distribution": dict(district_types),
            "road_width": self._estimate_road_width(tiles),
            "house_density": self._estimate_house_density(rooms),
        }

    def _estimate_road_width(self, tiles: Dict[str, int]) -> int:
        road_count = tiles.get("polished_stone", 0) + tiles.get("yalahar_floor", 0)
        if road_count > 5000:
            return 3
        if road_count > 2000:
            return 2
        return 1

    def _estimate_house_density(self, rooms: List[dict]) -> float:
        houses = sum(1 for room in rooms if "house" in room.get("name", "").lower())
        return houses / max(len(rooms), 1)
