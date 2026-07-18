from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from core.editor.item_type_flags import RMEItemTypeCatalog
from core.editor.complex_items import EditableItem
from core.editor.rme_map_model import DirtyTileTracker, RMEMapSpatialIndex


Position = tuple[int, int, int]


@dataclass
class EditableTile:
    x: int
    y: int
    z: int
    ground: int | None = None
    items: list[int] = field(default_factory=list)
    item_payloads: list[EditableItem] = field(default_factory=list)
    flags: int = 0
    house_id: int | None = None
    zones: set[str] = field(default_factory=set)
    spawn_monsters: list[str] = field(default_factory=list)
    spawn_npcs: list[str] = field(default_factory=list)
    waypoint: str | None = None
    role: str = "ground"
    brush: str = "terrain"
    region: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def position(self) -> Position:
        return (self.x, self.y, self.z)

    def copy(self) -> "EditableTile":
        return EditableTile(
            x=self.x,
            y=self.y,
            z=self.z,
            ground=self.ground,
            items=list(self.items),
            item_payloads=[item.copy() for item in self.item_payloads],
            flags=self.flags,
            house_id=self.house_id,
            zones=set(self.zones),
            spawn_monsters=list(self.spawn_monsters),
            spawn_npcs=list(self.spawn_npcs),
            waypoint=self.waypoint,
            role=self.role,
            brush=self.brush,
            region=self.region,
            metadata=dict(self.metadata),
        )

    def stack_ids(self) -> list[int]:
        return ([self.ground] if self.ground else []) + list(self.items)

    def complex_stack_ids(self) -> list[int]:
        return self.stack_ids() + [item.item_id for item in self.item_payloads]

    def empty(self) -> bool:
        return self.ground is None and not self.items and not self.spawn_monsters and not self.spawn_npcs and self.waypoint is None


class EditableMap:
    def __init__(self, item_catalog: RMEItemTypeCatalog | None = None) -> None:
        self.item_catalog = item_catalog or RMEItemTypeCatalog()
        self.tiles: RMEMapSpatialIndex = RMEMapSpatialIndex()
        self.modified = DirtyTileTracker()

    def get_tile(self, position: Position) -> EditableTile | None:
        return self.tiles.get(tuple(position))

    def ensure_tile(self, position: Position) -> EditableTile:
        pos = tuple(position)
        tile = self.tiles.get(pos)
        if tile is None:
            tile = EditableTile(*pos)
            self.tiles[pos] = tile
        return tile

    def set_tile(self, tile: EditableTile | None, position: Position | None = None) -> None:
        pos = tuple(position or (tile.position if tile else ()))
        if tile is None:
            self.tiles.pop(pos, None)
            self.mark_dirty(pos, "remove_tile")
            return
        self.tiles[tile.position] = tile.copy()
        self.normalize_tile(tile.position)
        self.mark_dirty(tile.position, "set_tile")

    def add_item(self, position: Position, item_id: int) -> None:
        tile = self.ensure_tile(position)
        item = self.item_catalog.get(item_id)
        if item.is_ground:
            tile.ground = item.item_id
        elif item.ground_equivalent:
            tile.ground = item.ground_equivalent
            tile.items.append(item.item_id)
        else:
            tile.items.append(item.item_id)
        self.normalize_tile(position)
        self.mark_dirty(position, "add_item")

    def set_stack(self, position: Position, item_ids: Iterable[int]) -> None:
        tile = self.ensure_tile(position)
        ground, items = self.item_catalog.classify_stack(item_ids)
        tile.ground = ground
        tile.items = items
        self.mark_dirty(position, "set_stack")

    def set_stack_exact(self, position: Position, ground: int | None, items: Iterable[int]) -> None:
        tile = self.ensure_tile(position)
        tile.ground = int(ground) if ground is not None else None
        tile.items = [int(item_id) for item_id in items]
        self.mark_dirty(position, "set_stack_exact")

    def normalize_tile(self, position: Position) -> None:
        tile = self.ensure_tile(position)
        stack = tile.stack_ids()
        ground, items = self.item_catalog.classify_stack(stack)
        tile.ground = ground
        tile.items = items

    def neighbors8(self, position: Position) -> dict[str, EditableTile | None]:
        x, y, z = position
        offsets = {
            "n": (0, -1),
            "e": (1, 0),
            "s": (0, 1),
            "w": (-1, 0),
            "nw": (-1, -1),
            "ne": (1, -1),
            "sw": (-1, 1),
            "se": (1, 1),
        }
        return {key: self.get_tile((x + dx, y + dy, z)) for key, (dx, dy) in offsets.items()}

    def dirty_positions(self) -> list[Position]:
        return sorted(self.modified)

    def mark_dirty(self, position: Position, reason: str = "edit") -> None:
        self.modified.mark(tuple(position), reason)

    def consume_dirty_positions(self) -> list[Position]:
        return self.modified.consume()

    def iter_rect(
        self, x1: int, y1: int, x2: int, y2: int, z: int
    ) -> Iterable[tuple[Position, EditableTile]]:
        return self.tiles.iter_rect(x1, y1, x2, y2, z)

    def snapshot_tile(self, position: Position) -> EditableTile | None:
        tile = self.get_tile(position)
        return tile.copy() if tile else None

    def audit(self) -> dict[str, object]:
        item_count = sum(len(tile.items) + (1 if tile.ground else 0) for tile in self.tiles.values())
        return {
            "editable_map_ready": True,
            "tile_count": len(self.tiles),
            "item_count": item_count,
            "dirty_tile_count": len(self.modified),
            "spatial_index": self.tiles.audit(),
            "dirty_tracker": self.modified.audit(),
        }
