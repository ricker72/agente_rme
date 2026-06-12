from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .zone_plan import ZonePlan


@dataclass
class CityPlan:
    name: str
    theme: str
    population: int
    districts: List[Dict[str, object]] = field(default_factory=list)
    zones: List[ZonePlan] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "theme": self.theme,
            "population": self.population,
            "districts": self.districts,
            "zones": [zone.to_dict() for zone in self.zones],
        }
