"""Canonical UI-neutral tile projection used by planner materialization."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from core.editor.action_queue import ActionIdentifier, ActionQueue, BatchAction, TileChange
from core.editor.editable_map import EditableMap, EditableTile
from core.editor.item_type_flags import RMEItemTypeCatalog


TileKey = tuple[int, int, int]


@dataclass(frozen=True, order=True)
class TileCoord:
    x: int
    y: int
    z: int = 7

    def key(self) -> TileKey:
        return self.x, self.y, self.z


@dataclass
class WorkspaceTile:
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


@dataclass
class MappingTransaction:
    label: str
    before: dict[TileKey, WorkspaceTile | None]
    after: dict[TileKey, WorkspaceTile | None]
    batch_action: BatchAction | None = field(default=None, compare=False, repr=False)


class WorkspaceMappingEngine:
    """EditableMap + ActionQueue owner with no dependency on the desktop package."""

    def __init__(self, workspace_root: str | Path = ".") -> None:
        catalog = RMEItemTypeCatalog.load(workspace_root)
        self.editor_map = EditableMap(catalog)
        self.actions = ActionQueue(self.editor_map)
        self.tiles: dict[TileKey, WorkspaceTile] = {}

    def commit_tiles(
        self,
        label: str,
        before: dict[TileKey, WorkspaceTile | None],
        after: dict[TileKey, WorkspaceTile | None],
        identifier: ActionIdentifier = ActionIdentifier.DRAW,
    ) -> MappingTransaction:
        positions = sorted(set(before) | set(after))
        transaction = MappingTransaction(label, before, after)
        batch = BatchAction(
            label=label,
            changes=[
                TileChange(
                    position=position,
                    before=self._editable_tile(before.get(position)),
                    after=self._editable_tile(after.get(position)),
                )
                for position in positions
            ],
            identifier=identifier,
            metadata={"mapping_transaction": True, "dirty_positions": positions},
            redo_callback=lambda: self._apply_projection(after),
            undo_callback=lambda: self._apply_projection(before),
        )
        transaction.batch_action = batch
        self.actions.commit(batch)
        return transaction

    def _commit(
        self,
        label: str,
        before: dict[TileKey, WorkspaceTile | None],
        after: dict[TileKey, WorkspaceTile | None],
        identifier: ActionIdentifier = ActionIdentifier.DRAW,
    ) -> MappingTransaction:
        """Compatibility entry point; all mutations still use one BatchAction."""
        return self.commit_tiles(label, before, after, identifier)

    def undo(self) -> bool:
        action = self.actions.undo_action()
        if action is None:
            return False
        if not action.metadata.get("mapping_transaction"):
            self.sync_from_editable(action.positions)
        return True

    def redo(self) -> bool:
        action = self.actions.redo_action()
        if action is None:
            return False
        if not action.metadata.get("mapping_transaction"):
            self.sync_from_editable(action.positions)
        return True

    def sync_from_editable(self, positions: Iterable[TileKey]) -> None:
        for position in positions:
            tile = self.editor_map.get_tile(position)
            if tile is None:
                self.tiles.pop(position, None)
                continue
            items = list(tile.items) + [item.item_id for item in tile.item_payloads]
            self.tiles[position] = WorkspaceTile(
                coord=TileCoord(*position),
                role=tile.role,
                brush=tile.brush,
                ground_id=tile.ground,
                item_id=items[-1] if items else None,
                items=items,
                zones=set(tile.zones),
                house_id=tile.house_id,
                spawn_monsters=list(tile.spawn_monsters),
                spawn_npcs=list(tile.spawn_npcs),
                waypoint=tile.waypoint,
                region=tile.region,
                metadata=dict(tile.metadata),
            )

    def _apply_projection(self, state: dict[TileKey, WorkspaceTile | None]) -> None:
        for position, tile in state.items():
            if tile is None:
                self.tiles.pop(position, None)
            else:
                self.tiles[position] = tile.copy()

    @staticmethod
    def _editable_tile(tile: WorkspaceTile | None) -> EditableTile | None:
        if tile is None:
            return None
        return EditableTile(
            x=tile.coord.x,
            y=tile.coord.y,
            z=tile.coord.z,
            ground=tile.ground_id,
            items=list(tile.items),
            zones=set(tile.zones) | ({tile.zone} if tile.zone else set()),
            house_id=tile.house_id,
            spawn_monsters=list(tile.spawn_monsters),
            spawn_npcs=list(tile.spawn_npcs),
            waypoint=tile.waypoint,
            role=tile.role,
            brush=tile.brush,
            region=tile.region,
            metadata=dict(tile.metadata),
        )


__all__ = ["MappingTransaction", "TileCoord", "TileKey", "WorkspaceMappingEngine", "WorkspaceTile"]
