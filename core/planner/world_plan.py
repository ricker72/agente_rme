from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .city_plan import CityPlan
from .dungeon_plan import DungeonPlan
from .zone_plan import ZonePlan


@dataclass
class WorldPlan:
    cities: List[CityPlan] = field(default_factory=list)
    dungeons: List[DungeonPlan] = field(default_factory=list)
    roads: List[Dict[str, object]] = field(default_factory=list)
    teleports: List[Dict[str, object]] = field(default_factory=list)
    ports: List[Dict[str, object]] = field(default_factory=list)
    hunting_zones: List[ZonePlan] = field(default_factory=list)
    boss_zones: List[ZonePlan] = field(default_factory=list)
    quest_zones: List[ZonePlan] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "cities": [city.to_dict() for city in self.cities],
            "dungeons": [dungeon.to_dict() for dungeon in self.dungeons],
            "roads": self.roads,
            "teleports": self.teleports,
            "ports": self.ports,
            "hunting_zones": [zone.to_dict() for zone in self.hunting_zones],
            "boss_zones": [zone.to_dict() for zone in self.boss_zones],
            "quest_zones": [zone.to_dict() for zone in self.quest_zones],
        }
