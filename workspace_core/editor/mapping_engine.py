"""UI-neutral transactional mapping engine used by AI and desktop adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from core.editor.item_type_flags import RMEItemTypeCatalog

from .actions import ActionIdentifier, BatchAction, TileChange
from .model import EditableTile, TileCoord, TileKey, WorkspaceTile
from .workspace import EditorWorkspaceCore


@dataclass
class WorkspaceMappingTransaction:
    label: str
    before: dict[TileKey, WorkspaceTile | None]
    after: dict[TileKey, WorkspaceTile | None]
    batch_action: BatchAction | None = field(default=None, compare=False, repr=False)


class WorkspaceMappingEngine:
    """Canonical tile projection over EditableMap and ActionQueue, without UI imports."""

    def __init__(
        self,
        workspace_root: str | Path = ".",
        workspace: EditorWorkspaceCore | None = None,
    ) -> None:
        if workspace is None:
            from .model import EditableMap

            catalog = RMEItemTypeCatalog.load(workspace_root)
            workspace = EditorWorkspaceCore(
                editable_map=EditableMap(catalog),
                root=workspace_root,
            )
        self.workspace_core = workspace
        self.editor_map = self.workspace_core.editable_map
        self.actions = self.workspace_core.actions
        self.tiles: dict[TileKey, WorkspaceTile] = {}

    def commit_tiles(
        self,
        label: str,
        before: dict[TileKey, WorkspaceTile | None],
        after: dict[TileKey, WorkspaceTile | None],
        identifier: ActionIdentifier = ActionIdentifier.DRAW,
    ) -> WorkspaceMappingTransaction:
        positions = sorted(set(before) | set(after))
        transaction = WorkspaceMappingTransaction(label, before, after)
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
            metadata={"workspace_mapping_transaction": True, "dirty_positions": positions},
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
    ) -> WorkspaceMappingTransaction:
        return self.commit_tiles(label, before, after, identifier)

    def undo(self) -> bool:
        action = self.actions.undo_action()
        if action is None:
            return False
        if not action.metadata.get("workspace_mapping_transaction"):
            self.sync_from_editable(action.positions)
        return True

    def redo(self) -> bool:
        action = self.actions.redo_action()
        if action is None:
            return False
        if not action.metadata.get("workspace_mapping_transaction"):
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
                zone=next(iter(sorted(tile.zones)), ""),
                zones=set(tile.zones),
                house_id=tile.house_id,
                spawn_monsters=list(tile.spawn_monsters),
                spawn_npcs=list(tile.spawn_npcs),
                waypoint=tile.waypoint,
                region=tile.region,
                metadata=dict(tile.metadata),
            )

    def audit(self) -> dict[str, object]:
        return {
            "workspace_mapping_engine_ready": True,
            "ui_neutral": True,
            "tile_count": len(self.tiles),
            "actions": self.actions.audit(),
        }

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


__all__ = ["WorkspaceMappingEngine", "WorkspaceMappingTransaction"]
