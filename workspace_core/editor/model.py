"""Canonical editable workspace model exposed to UI, AI and exporters."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.editor.editable_map import EditableMap, EditableTile, Position


TileKey = tuple[int, int, int]


@dataclass(frozen=True, order=True)
class TileCoord:
    x: int
    y: int
    z: int = 7

    def key(self) -> TileKey:
        return (self.x, self.y, self.z)


@dataclass
class WorkspaceTile:
    """UI-neutral tile projection backed by the canonical EditableMap."""

    coord: TileCoord
    role: str = "ground"
    brush: str = "terrain"
    ground_id: int | None = 0
    item_id: int | None = None
    items: list[int] = field(default_factory=list)
    zone: str = ""
    zones: set[str] = field(default_factory=set)
    house_id: int | None = None
    spawn_monsters: list[str] = field(default_factory=list)
    spawn_npcs: list[str] = field(default_factory=list)
    waypoint: str | None = None
    region: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def copy(self) -> "WorkspaceTile":
        return WorkspaceTile(
            coord=self.coord,
            role=self.role,
            brush=self.brush,
            ground_id=self.ground_id,
            item_id=self.item_id,
            items=list(self.items),
            zone=self.zone,
            zones=set(self.zones),
            house_id=self.house_id,
            spawn_monsters=list(self.spawn_monsters),
            spawn_npcs=list(self.spawn_npcs),
            waypoint=self.waypoint,
            region=self.region,
            metadata=dict(self.metadata),
        )

    def to_viewport_dict(self) -> dict[str, object]:
        return {
            "x": self.coord.x,
            "y": self.coord.y,
            "floor": self.coord.z,
            "role": self.role,
            "brush": self.brush,
            "ground_id": self.ground_id,
            "item_id": self.item_id,
            "items": list(self.items),
            "zone": self.zone,
            "zones": sorted(self.zones),
            "house_id": self.house_id,
            "spawn_monsters": list(self.spawn_monsters),
            "spawn_npcs": list(self.spawn_npcs),
            "waypoint": self.waypoint,
            "region": self.region,
            "metadata": dict(self.metadata),
        }


__all__ = [
    "EditableMap",
    "EditableTile",
    "Position",
    "TileCoord",
    "TileKey",
    "WorkspaceTile",
]
