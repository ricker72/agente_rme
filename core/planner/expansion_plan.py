from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class ExpansionPlan:
    category: str
    reserved_area: Dict[str, int]
    reason: str
    timeline: str = "future"

    def to_dict(self) -> Dict[str, object]:
        return {
            "category": self.category,
            "reserved_area": self.reserved_area,
            "reason": self.reason,
            "timeline": self.timeline,
        }


class ExpansionPlanner:
    def reserve(
        self, category: str, width: int, height: int, reason: str
    ) -> ExpansionPlan:
        return ExpansionPlan(
            category=category,
            reserved_area={"width": width, "height": height},
            reason=reason,
            timeline="future",
        )
