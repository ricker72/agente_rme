from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from dataclasses import dataclass, field
from typing import Any


Position = tuple[int, int, int]
LeafKey = tuple[int, int, int]
RME_LEAF_SIZE = 4
RME_FLOOR_COUNT = 16


@dataclass
class TileLocationState:
    position: Position
    spawn_monster_count: int = 0
    spawn_npc_count: int = 0
    waypoint_count: int = 0
    house_exits: set[int] = field(default_factory=set)

    def empty(self) -> bool:
        return not (
            self.spawn_monster_count
            or self.spawn_npc_count
            or self.waypoint_count
            or self.house_exits
        )


@dataclass
class RMEMapLeaf:
    leaf_x: int
    leaf_y: int
    z: int
    tiles: dict[int, Any] = field(default_factory=dict)
    locations: dict[int, TileLocationState] = field(default_factory=dict)
    visible_clients: set[int] = field(default_factory=set)
    requested: bool = False

    @property
    def origin(self) -> Position:
        return (self.leaf_x * RME_LEAF_SIZE, self.leaf_y * RME_LEAF_SIZE, self.z)

    def local_index(self, x: int, y: int) -> int:
        return (x & (RME_LEAF_SIZE - 1)) * RME_LEAF_SIZE + (y & (RME_LEAF_SIZE - 1))

    def empty(self) -> bool:
        return not self.tiles and not self.locations


class RMEMapSpatialIndex(MutableMapping[Position, Any]):
    """Python storage equivalent of RME BaseMap leaf/floor tile lookup."""

    def __init__(self) -> None:
        self._leaves: dict[LeafKey, RMEMapLeaf] = {}
        self._tile_count = 0

    def __getitem__(self, position: Position) -> Any:
        tile = self.get_tile(position)
        if tile is None:
            raise KeyError(tuple(position))
        return tile

    def __setitem__(self, position: Position, tile: Any) -> None:
        self.set_tile(position, tile)

    def __delitem__(self, position: Position) -> None:
        if self.remove_tile(position) is None:
            raise KeyError(tuple(position))

    def __iter__(self) -> Iterator[Position]:
        for key in sorted(self._leaves, key=lambda value: (value[2], value[1], value[0])):
            leaf = self._leaves[key]
            for local_index in sorted(leaf.tiles):
                yield self._position_for_index(leaf, local_index)

    def __len__(self) -> int:
        return self._tile_count

    def get_tile(self, position: Position) -> Any | None:
        x, y, z = self._validated_position(position)
        leaf = self._leaves.get(self.leaf_key((x, y, z)))
        return None if leaf is None else leaf.tiles.get(leaf.local_index(x, y))

    def set_tile(self, position: Position, tile: Any) -> Any | None:
        x, y, z = self._validated_position(position)
        key = self.leaf_key((x, y, z))
        leaf = self._leaves.setdefault(key, RMEMapLeaf(*key))
        index = leaf.local_index(x, y)
        old = leaf.tiles.get(index)
        leaf.tiles[index] = tile
        if old is None:
            self._tile_count += 1
        return old

    def remove_tile(self, position: Position) -> Any | None:
        x, y, z = self._validated_position(position)
        key = self.leaf_key((x, y, z))
        leaf = self._leaves.get(key)
        if leaf is None:
            return None
        old = leaf.tiles.pop(leaf.local_index(x, y), None)
        if old is not None:
            self._tile_count -= 1
        self._prune_leaf(key)
        return old

    def location(self, position: Position, create: bool = False) -> TileLocationState | None:
        x, y, z = self._validated_position(position)
        key = self.leaf_key((x, y, z))
        leaf = self._leaves.get(key)
        if leaf is None and create:
            leaf = self._leaves.setdefault(key, RMEMapLeaf(*key))
        if leaf is None:
            return None
        index = leaf.local_index(x, y)
        if create:
            return leaf.locations.setdefault(index, TileLocationState((x, y, z)))
        return leaf.locations.get(index)

    def release_location(self, position: Position) -> None:
        key = self.leaf_key(position)
        leaf = self._leaves.get(key)
        if leaf is None:
            return
        x, y, _z = position
        index = leaf.local_index(x, y)
        location = leaf.locations.get(index)
        if location is not None and location.empty():
            leaf.locations.pop(index, None)
        self._prune_leaf(key)

    def leaf_key(self, position: Position) -> LeafKey:
        x, y, z = self._validated_position(position)
        return (x // RME_LEAF_SIZE, y // RME_LEAF_SIZE, z)

    def leaves_in_rect(self, x1: int, y1: int, x2: int, y2: int, z: int) -> list[RMEMapLeaf]:
        self._validated_position((x1, y1, z))
        self._validated_position((x2, y2, z))
        min_x, max_x = sorted((x1 // RME_LEAF_SIZE, x2 // RME_LEAF_SIZE))
        min_y, max_y = sorted((y1 // RME_LEAF_SIZE, y2 // RME_LEAF_SIZE))
        return [
            leaf
            for leaf_y in range(min_y, max_y + 1)
            for leaf_x in range(min_x, max_x + 1)
            if (leaf := self._leaves.get((leaf_x, leaf_y, z))) is not None
        ]

    def iter_rect(self, x1: int, y1: int, x2: int, y2: int, z: int) -> Iterator[tuple[Position, Any]]:
        min_x, max_x = sorted((x1, x2))
        min_y, max_y = sorted((y1, y2))
        for leaf in self.leaves_in_rect(min_x, min_y, max_x, max_y, z):
            for index, tile in sorted(leaf.tiles.items()):
                position = self._position_for_index(leaf, index)
                if min_x <= position[0] <= max_x and min_y <= position[1] <= max_y:
                    yield position, tile

    def set_leaf_visibility(self, position: Position, client_id: int, visible: bool) -> None:
        key = self.leaf_key(position)
        leaf = self._leaves.setdefault(key, RMEMapLeaf(*key))
        if visible:
            leaf.visible_clients.add(int(client_id))
        else:
            leaf.visible_clients.discard(int(client_id))

    def set_leaf_requested(self, position: Position, requested: bool) -> None:
        key = self.leaf_key(position)
        leaf = self._leaves.setdefault(key, RMEMapLeaf(*key))
        leaf.requested = bool(requested)

    def audit(self) -> dict[str, object]:
        floor_counts: dict[int, int] = {}
        for _x, _y, z in self:
            floor_counts[z] = floor_counts.get(z, 0) + 1
        return {
            "rme_spatial_index_ready": True,
            "leaf_size": RME_LEAF_SIZE,
            "floor_count": RME_FLOOR_COUNT,
            "leaf_count": len(self._leaves),
            "tile_count": self._tile_count,
            "location_count": sum(len(leaf.locations) for leaf in self._leaves.values()),
            "requested_leaf_count": sum(1 for leaf in self._leaves.values() if leaf.requested),
            "visible_leaf_count": sum(1 for leaf in self._leaves.values() if leaf.visible_clients),
            "tiles_by_floor": dict(sorted(floor_counts.items())),
            "source_parity": [
                "BaseMap::getTileL/createTileL",
                "Floor::locs[16]",
                "TileLocation counters",
                "QTreeNode visibility/requested state",
            ],
        }

    def _validated_position(self, position: Position) -> Position:
        if len(position) != 3:
            raise ValueError("position must contain x, y and z")
        x, y, z = (int(value) for value in position)
        if not 0 <= z < RME_FLOOR_COUNT:
            raise ValueError(f"floor outside RME range 0..15: {z}")
        return (x, y, z)

    def _position_for_index(self, leaf: RMEMapLeaf, index: int) -> Position:
        local_x, local_y = divmod(index, RME_LEAF_SIZE)
        origin_x, origin_y, z = leaf.origin
        return (origin_x + local_x, origin_y + local_y, z)

    def _prune_leaf(self, key: LeafKey) -> None:
        leaf = self._leaves.get(key)
        if leaf and leaf.empty() and not leaf.visible_clients and not leaf.requested:
            self._leaves.pop(key, None)


class DirtyTileTracker(set[Position]):
    def __init__(self) -> None:
        super().__init__()
        self.revision = 0
        self.reasons: dict[Position, set[str]] = {}

    def mark(self, position: Position, reason: str = "edit") -> None:
        pos = tuple(int(value) for value in position)
        super().add(pos)
        self.revision += 1
        self.reasons.setdefault(pos, set()).add(str(reason))

    def add(self, element: Position) -> None:
        self.mark(element)

    def consume(self) -> list[Position]:
        positions = sorted(self)
        self.clear()
        self.reasons.clear()
        return positions

    def audit(self) -> dict[str, object]:
        return {
            "dirty_tile_tracking_ready": True,
            "revision": self.revision,
            "dirty_tile_count": len(self),
            "reason_counts": {
                reason: sum(reason in reasons for reasons in self.reasons.values())
                for reason in sorted({item for reasons in self.reasons.values() for item in reasons})
            },
        }
