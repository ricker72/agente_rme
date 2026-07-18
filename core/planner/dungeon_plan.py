from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class DungeonPlan:
    name: str
    theme: str
    floors: int
    difficulty: str
    bosses: List[Dict[str, object]] = field(default_factory=list)
    quests: List[Dict[str, object]] = field(default_factory=list)
    connections: List[Dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "theme": self.theme,
            "floors": self.floors,
            "difficulty": self.difficulty,
            "bosses": self.bosses,
            "quests": self.quests,
            "connections": self.connections,
        }
