from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


ROLE_MAPCOLORS = {
    "WATER": 205,
    "GROUND": 126,
    "NATURE": 126,
    "ROAD": 114,
    "MOUNTAIN": 129,
    "WALL": 186,
    "DOOR": 186,
    "WINDOW": 186,
    "ROOF": 180,
    "INTERIOR": 210,
    "BORDER": 114,
    "DECORATION": 192,
    "CREATURE": 215,
    "NPC": 215,
    "SPAWN_OBJECT": 215,
}


@dataclass(frozen=True)
class RMEMapColor:
    index: int
    red: int
    green: int
    blue: int
    source: str

    @property
    def rgb(self) -> tuple[int, int, int]:
        return self.red, self.green, self.blue

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "rgb": list(self.rgb),
            "source": self.source,
        }


def rme_minimap_color_to_rgb(color: int) -> tuple[int, int, int]:
    color = max(0, min(255, int(color)))
    return (
        int(color / 36) % 6 * 51,
        int(color / 6) % 6 * 51,
        color % 6 * 51,
    )


def resolve_rme_mapcolor(model: Any, role: str = "") -> RMEMapColor:
    flags = dict(getattr(model, "flags", {}) or {})
    for key in ("mapcolor", "map_color", "minimap_color", "automap_color", "automap.color"):
        value = flags.get(key)
        if value is not None and str(value).isdigit():
            index = int(value)
            return RMEMapColor(index, *rme_minimap_color_to_rgb(index), source=f"appearance_flag:{key}")
    role_key = str(role or getattr(model, "semantic_role", "") or "GROUND").upper()
    name = str(getattr(model, "name", "")).lower()
    if "water" in name or "sea" in name:
        role_key = "WATER"
    elif "mountain" in name or "rock" in name:
        role_key = "MOUNTAIN"
    elif "road" in name or "street" in name:
        role_key = "ROAD"
    index = ROLE_MAPCOLORS.get(role_key, ROLE_MAPCOLORS["GROUND"])
    return RMEMapColor(index, *rme_minimap_color_to_rgb(index), source=f"role_fallback:{role_key}")


def dominant_stack_mapcolor(stack: Iterable[Any]) -> RMEMapColor:
    stack_list = list(stack)
    if not stack_list:
        return RMEMapColor(0, 0, 0, 0, source="empty")
    for tile in stack_list:
        role = str(getattr(tile, "role", "")).upper()
        if role in {"GROUND", "WATER", "ROAD", "MOUNTAIN", "INTERIOR"}:
            return resolve_rme_mapcolor(tile.model, role)
    first = stack_list[0]
    return resolve_rme_mapcolor(first.model, getattr(first, "role", "GROUND"))


def audit_rme_mapcolor_contract() -> dict[str, Any]:
    return {
        "rme_mapcolor_ready": True,
        "source_formula": "RME IOMinimap: r=(color/36)%6*51, g=(color/6)%6*51, b=color%6*51",
        "role_fallbacks": ROLE_MAPCOLORS,
        "exact_automap_color_extraction": "USED_WHEN_PRESENT",
    }
