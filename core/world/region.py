from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Region:
    """
    A named zone in the world that groups tiles with a common purpose.

    Architecture:
      - name: Unique region name (e.g. "issavi_city_center").
      - theme: Visual theme (e.g. "issavi", "roshamuul", "jungle").
      - min_level: Recommended minimum player level for this region.
      - max_level: Recommended maximum player level for this region.
      - tags: Categorization tags for search and filtering.
    """

    name: str
    theme: str = "generic"
    min_level: int = 1
    max_level: int = 9999
    tags: List[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "theme": self.theme,
            "min_level": self.min_level,
            "max_level": self.max_level,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Region:
        return cls(
            name=data.get("name", "unnamed"),
            theme=data.get("theme", "generic"),
            min_level=data.get("min_level", 1),
            max_level=data.get("max_level", 9999),
            tags=data.get("tags", []),
        )

    def __repr__(self) -> str:
        return f"Region(name='{self.name}', theme='{self.theme}', levels={self.min_level}-{self.max_level})"
