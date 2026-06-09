from __future__ import annotations

from typing import Dict, List


class CityBuilder:
    def build(self, city_plan: Dict[str, object]) -> Dict[str, object]:
        return {
            "name": city_plan.get("name"),
            "theme": city_plan.get("theme"),
            "population": city_plan.get("population"),
            "districts": city_plan.get("districts", []),
            "zones": city_plan.get("zones", []),
        }

    def describe_features(self, city_plan: Dict[str, object]) -> List[str]:
        return [district.get("type") for district in city_plan.get("districts", [])]
