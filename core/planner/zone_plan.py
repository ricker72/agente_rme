from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ZonePlan:
    zone_type: str
    name: str
    x: int
    y: int
    width: int
    height: int
    difficulty: str = "normal"
    purpose: str = "generic"
    features: List[str] = None

    def __post_init__(self):
        if self.features is None:
            self.features = []

    def to_dict(self) -> Dict[str, object]:
        return {
            "zone_type": self.zone_type,
            "name": self.name,
            "bounds": {
                "x": self.x,
                "y": self.y,
                "width": self.width,
                "height": self.height,
            },
            "difficulty": self.difficulty,
            "purpose": self.purpose,
            "features": self.features,
        }
