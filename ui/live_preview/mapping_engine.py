"""
MAP-01 in-memory OpenTibia mapping engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

from workspace_core.editor import (
    ActionIdentifier,
    BatchAction,
    EditorWorkspaceCore,
    EditableTile,
    TileChange,
    TileCoord,
    TileKey,
    WorkspaceTile,
)

from .map_brushes import DEFAULT_ITEM_ID, DEFAULT_TERRAIN_ID, is_valid_item
from .map_selection import SelectionSessionMode


MapTile = WorkspaceTile


@dataclass
class MappingTransaction:
    """Undoable mapping operation."""

    name: str
    before: Dict[TileKey, Optional[MapTile]]
    after: Dict[TileKey, Optional[MapTile]]
    batch_action: BatchAction | None = field(default=None, compare=False, repr=False)


class OpenTibiaMappingEngine:
    """Small deterministic editor core for MAP-01 Safe Mode workflows."""

    def __init__(self, workspace_root: str | Path = ".") -> None:
        self.tiles: Dict[TileKey, MapTile] = {}
        self.workspace_core = EditorWorkspaceCore(root=workspace_root)
        self.editor_map = self.workspace_core.editable_map
        self.actions = self.workspace_core.actions
        self.selection_manager = self.workspace_core.selection
        self.selection_history = self.selection_manager.history
        self.copybuffer = self.workspace_core.copybuffer
        self.undo_stack: List[MappingTransaction] = []
        self.redo_stack: List[MappingTransaction] = []
        self.bookmarks: Dict[str, TileCoord] = {}
        self.recent_locations: List[TileCoord] = []
        self.cursor = TileCoord(0, 0, 7)

    @property
    def selection(self) -> Set[TileKey]:
        return self.selection_manager.positions

    @selection.setter
    def selection(self, positions: Iterable[TileKey]) -> None:
        self.selection_manager.set_positions(
            positions,
            mode=SelectionSessionMode.INTERNAL,
            label="Load selection state",
        )

    @property
    def clipboard(self) -> Dict[TileKey, MapTile]:
        return self.copybuffer.tiles

    @clipboard.setter
    def clipboard(self, tiles: Dict[TileKey, MapTile]) -> None:
        self.copybuffer.replace(tiles, record=False)

    @property
    def clipboard_history(self) -> List[Dict[TileKey, MapTile]]:
        return self.copybuffer.history

    def select_single(self, coord: TileCoord) -> Set[TileKey]:
        return self._set_selection({coord.key()})

    def clear_selection(self) -> Set[TileKey]:
        return self._set_selection(set())

    def select_rectangle(
        self,
        start: TileCoord,
        end: TileCoord,
        mode: SelectionSessionMode = SelectionSessionMode.EXTERNAL,
    ) -> Set[TileKey]:
        min_x, max_x = sorted((start.x, end.x))
        min_y, max_y = sorted((start.y, end.y))
        keys = {
            (x, y, start.z)
            for x in range(min_x, max_x + 1)
            for y in range(min_y, max_y + 1)
        }
        if mode & SelectionSessionMode.INTERNAL:
            self.selection_manager.set_positions(keys, mode=mode)
            return set(self.selection)
        return self._set_selection(keys)

    def expand_selection(self, radius: int = 1) -> Set[TileKey]:
        expanded = set(self.selection)
        for x, y, z in list(self.selection):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    expanded.add((x + dx, y + dy, z))
        return self._set_selection(expanded)

    def shrink_selection(self) -> Set[TileKey]:
        if len(self.selection) <= 1:
            return self._set_selection(set())
        xs = [key[0] for key in self.selection]
        ys = [key[1] for key in self.selection]
        z = next(iter(self.selection))[2]
        keys = {
            key
            for key in self.selection
            if min(xs) < key[0] < max(xs) and min(ys) < key[1] < max(ys) and key[2] == z
        }
        return self._set_selection(keys)

    def invert_selection(self, bounds: Tuple[int, int, int, int], z: int = 7) -> Set[TileKey]:
        min_x, min_y, max_x, max_y = bounds
        all_keys = {
            (x, y, z)
            for x in range(min_x, max_x + 1)
            for y in range(min_y, max_y + 1)
        }
        return self._set_selection(all_keys - self.selection)

    def select_polygon(self, points: List[TileCoord]) -> Set[TileKey]:
        if not points:
            return self._set_selection(set())
        z = points[0].z
        min_x = min(point.x for point in points)
        max_x = max(point.x for point in points)
        min_y = min(point.y for point in points)
        max_y = max(point.y for point in points)

        def contains(x: int, y: int) -> bool:
            inside = False
            j = len(points) - 1
            for i, point in enumerate(points):
                previous = points[j]
                if ((point.y > y) != (previous.y > y)) and (
                    x < (previous.x - point.x) * (y - point.y) / max(1, previous.y - point.y) + point.x
                ):
                    inside = not inside
                j = i
            return inside

        return self._set_selection(
            (x, y, z)
            for x in range(min_x, max_x + 1)
            for y in range(min_y, max_y + 1)
            if contains(x, y)
        )

    def select_region(self, region: str) -> Set[TileKey]:
        return self._set_selection(key for key, tile in self.tiles.items() if tile.region == region)

    def select_layer(self, z: int) -> Set[TileKey]:
        return self._set_selection(key for key in self.tiles if key[2] == z)

    def magic_select_same_brush(self, coord: TileCoord) -> Set[TileKey]:
        tile = self.tiles.get(coord.key())
        if tile is None:
            return self.select_single(coord)
        return self._set_selection(
            key for key, candidate in self.tiles.items() if candidate.brush == tile.brush
        )

    def paint(self, coords: Iterable[TileCoord], brush: str, role: str) -> MappingTransaction:
        after: Dict[TileKey, Optional[MapTile]] = {}
        before: Dict[TileKey, Optional[MapTile]] = {}
        for coord in coords:
            key = coord.key()
            before[key] = self.tiles.get(key).copy() if key in self.tiles else None
            tile = self.tiles.get(key, MapTile(coord=coord))
            tile = tile.copy()
            tile.coord = coord
            tile.brush = brush
            tile.role = role
            if role == "ground" and tile.ground_id is None:
                tile.ground_id = DEFAULT_TERRAIN_ID
            after[key] = tile
        return self._commit("Paint brush", before, after)

    def place_item(self, coord: TileCoord, item_id: int = DEFAULT_ITEM_ID) -> MappingTransaction:
        return self.place_items([coord], item_id)

    def place_items(
        self, coords: Iterable[TileCoord], item_id: int = DEFAULT_ITEM_ID
    ) -> MappingTransaction:
        if not is_valid_item(item_id):
            raise ValueError(f"Item id {item_id} is not in the MAP-01 OpenTibia allowlist")
        before: Dict[TileKey, Optional[MapTile]] = {}
        after: Dict[TileKey, Optional[MapTile]] = {}
        for coord in coords:
            key = coord.key()
            before[key] = self.tiles.get(key).copy() if key in self.tiles else None
            tile = self.tiles.get(key, MapTile(coord=coord)).copy()
            tile.coord = coord
            tile.item_id = item_id
            if item_id not in tile.items:
                tile.items.append(item_id)
            after[key] = tile
        return self._commit("Place item", before, after, ActionIdentifier.DRAW)

    def erase_item(self, coord: TileCoord, item_id: Optional[int] = None) -> MappingTransaction:
        key = coord.key()
        before = {key: self.tiles.get(key).copy() if key in self.tiles else None}
        tile = self.tiles.get(key, MapTile(coord=coord)).copy()
        if item_id is None:
            tile.items.clear()
            tile.item_id = None
        else:
            tile.items = [existing for existing in tile.items if existing != item_id]
            tile.item_id = tile.items[-1] if tile.items else None
        after = {key: tile}
        return self._commit("Erase item", before, after, ActionIdentifier.ERASE)

    def paint_radius(self, center: TileCoord, radius: int, brush: str, role: str) -> MappingTransaction:
        coords = [
            TileCoord(center.x + dx, center.y + dy, center.z)
            for dx in range(-radius, radius + 1)
            for dy in range(-radius, radius + 1)
            if dx * dx + dy * dy <= radius * radius
        ]
        return self.paint(coords, brush, role)

    def set_ground_tiles(self, mutations: Iterable[object]) -> MappingTransaction:
        before: Dict[TileKey, Optional[MapTile]] = {}
        after: Dict[TileKey, Optional[MapTile]] = {}
        for mutation in mutations:
            coord = TileCoord(
                int(getattr(mutation, "x")),
                int(getattr(mutation, "y")),
                int(getattr(mutation, "z")),
            )
            key = coord.key()
            before[key] = self.tiles.get(key).copy() if key in self.tiles else None
            tile = self.tiles.get(key, MapTile(coord=coord)).copy()
            tile.coord = coord
            tile.role = "ground"
            tile.brush = str(getattr(mutation, "brush_id"))
            tile.ground_id = int(getattr(mutation, "ground_id"))
            tile.metadata["material_id"] = str(getattr(mutation, "material_id"))
            after[key] = tile
        return self._commit("Ground brush", before, after, ActionIdentifier.DRAW)

    def apply_official_brush(
        self,
        brush_name: str,
        positions: Iterable[TileKey],
        *,
        root: str | Path = ".",
        **options: object,
    ) -> object:
        commands = self.workspace_core.brush_commands
        if commands.materials is None:
            commands.root = Path(root)
        result = commands.apply(brush_name, positions, **options)
        self._sync_visual_from_editor_positions(result.action.positions)
        return result

    def search_planner_knowledge(
        self, query: str, limit: int = 50
    ) -> List[Dict[str, object]]:
        return self.workspace_core.planner.search_materials(query, limit)

    def create_mapper_proposal(
        self, objective: str
    ) -> tuple[object, Dict[str, object]]:
        return self.workspace_core.planner.create_plan(objective)

    def erase(
        self,
        coords: Iterable[TileCoord],
        name: str = "Erase tiles",
        identifier: ActionIdentifier = ActionIdentifier.ERASE,
    ) -> MappingTransaction:
        before: Dict[TileKey, Optional[MapTile]] = {}
        after: Dict[TileKey, Optional[MapTile]] = {}
        for coord in coords:
            key = coord.key()
            before[key] = self.tiles.get(key).copy() if key in self.tiles else None
            after[key] = None
        return self._commit(name, before, after, identifier)

    def update_property(self, coord: TileCoord, name: str, value: str) -> MappingTransaction:
        key = coord.key()
        before = {key: self.tiles.get(key).copy() if key in self.tiles else None}
        tile = self.tiles.get(key, MapTile(coord=coord)).copy()
        tile.metadata[name] = value
        after = {key: tile}
        return self._commit(
            "Update property", before, after, ActionIdentifier.CHANGE_PROPERTIES
        )

    def copy_selection(self) -> int:
        return self.copybuffer.replace({
            key: tile.copy()
            for key, tile in self.tiles.items()
            if key in self.selection
        })

    def cut_selection(self) -> MappingTransaction:
        self.copy_selection()
        return self.erase(
            (TileCoord(*key) for key in self.selection),
            name="Cut tiles",
            identifier=ActionIdentifier.CUT_TILES,
        )

    def paste(self, target: TileCoord) -> MappingTransaction:
        if not self.clipboard:
            return self._commit(
                "Paste clipboard", {}, {}, ActionIdentifier.PASTE_TILES
            )
        min_x = min(key[0] for key in self.clipboard)
        min_y = min(key[1] for key in self.clipboard)
        before: Dict[TileKey, Optional[MapTile]] = {}
        after: Dict[TileKey, Optional[MapTile]] = {}
        for key, tile in self.clipboard.items():
            coord = TileCoord(target.x + key[0] - min_x, target.y + key[1] - min_y, target.z)
            new_key = coord.key()
            before[new_key] = self.tiles.get(new_key).copy() if new_key in self.tiles else None
            pasted = tile.copy()
            pasted.coord = coord
            after[new_key] = pasted
        return self._commit(
            "Paste clipboard", before, after, ActionIdentifier.PASTE_TILES
        )

    def duplicate(self, offset_x: int = 1, offset_y: int = 1) -> MappingTransaction:
        self.copy_selection()
        if not self.selection:
            return self._commit("Duplicate selection", {}, {})
        min_x = min(key[0] for key in self.selection)
        min_y = min(key[1] for key in self.selection)
        z = next(iter(self.selection))[2]
        return self.paste(TileCoord(min_x + offset_x, min_y + offset_y, z))

    def rotate_clipboard_clockwise(self) -> int:
        return self.copybuffer.rotate_clockwise()

    def mirror_clipboard_horizontal(self) -> int:
        return self.copybuffer.mirror_horizontal()

    def undo(self) -> Optional[MappingTransaction]:
        action = self.actions.undo_action()
        if action is None:
            return None
        transaction = action.metadata.get("mapping_transaction")
        if isinstance(transaction, MappingTransaction):
            if transaction in self.undo_stack:
                self.undo_stack.remove(transaction)
            self.redo_stack.append(transaction)
            return transaction
        if action.metadata.get("workspace_core_brush"):
            self._sync_visual_from_editor_positions(action.positions)
        return MappingTransaction(action.label, {}, {}, action if isinstance(action, BatchAction) else None)

    def redo(self) -> Optional[MappingTransaction]:
        action = self.actions.redo_action()
        if action is None:
            return None
        transaction = action.metadata.get("mapping_transaction")
        if isinstance(transaction, MappingTransaction):
            if transaction in self.redo_stack:
                self.redo_stack.remove(transaction)
            self.undo_stack.append(transaction)
            return transaction
        if action.metadata.get("workspace_core_brush"):
            self._sync_visual_from_editor_positions(action.positions)
        return MappingTransaction(action.label, {}, {}, action if isinstance(action, BatchAction) else None)

    def jump_to(self, x: int, y: int, z: int = 7) -> TileCoord:
        self.cursor = TileCoord(x, y, z)
        self.recent_locations.append(self.cursor)
        self.recent_locations = self.recent_locations[-25:]
        self.select_single(self.cursor)
        return self.cursor

    def add_bookmark(self, name: str, coord: TileCoord) -> None:
        self.bookmarks[name] = coord

    def tiles_for_viewport(self) -> List[Dict[str, object]]:
        return [tile.to_viewport_dict() for tile in self.tiles.values()]

    def tiles_for_positions(self, positions: Iterable[TileKey]) -> List[Dict[str, object]]:
        return [
            self.tiles[key].to_viewport_dict()
            for key in sorted(set(positions))
            if key in self.tiles
        ]

    def selection_coords(self) -> List[TileCoord]:
        return [TileCoord(*key) for key in sorted(self.selection)]

    def selected_or_cursor(self) -> List[TileCoord]:
        if self.selection:
            return self.selection_coords()
        return [self.cursor]

    def repair_visual_zones_with_rme_core(self, root: str = ".") -> Dict[str, object]:
        from .rme_editor_tools_bridge import RMEEditorToolsBridge

        return RMEEditorToolsBridge(self, root=root).repair_visual_zones()

    def _set_selection(self, keys: Iterable[TileKey]) -> Set[TileKey]:
        action = self.selection_manager.set_positions(keys, label="Select tiles")
        if action is not None:
            self.redo_stack.clear()
        return set(self.selection)

    def _commit(
        self,
        name: str,
        before: Dict[TileKey, Optional[MapTile]],
        after: Dict[TileKey, Optional[MapTile]],
        identifier: ActionIdentifier = ActionIdentifier.DRAW,
    ) -> MappingTransaction:
        transaction = MappingTransaction(name=name, before=before, after=after)
        selection_before = set(self.selection)
        deleted = {key for key, tile in after.items() if tile is None}
        selection_after = selection_before - deleted
        changes = [
            TileChange(
                position=key,
                before=self._editable_tile(before.get(key)),
                after=self._editable_tile(after.get(key)),
            )
            for key in sorted(set(before) | set(after))
        ]

        def apply_visual_after() -> None:
            self._apply_state(after)
            self.selection_manager.set_positions(
                selection_after,
                mode=SelectionSessionMode.INTERNAL,
                label="Internal visual action selection sync",
            )

        def apply_visual_before() -> None:
            self._apply_state(before)
            self.selection_manager.set_positions(
                selection_before,
                mode=SelectionSessionMode.INTERNAL,
                label="Internal undo selection sync",
            )

        batch = BatchAction(
            label=name,
            changes=changes,
            identifier=identifier,
            metadata={
                "mapping_transaction": transaction,
                "visual_operation": True,
                "dirty_positions": sorted(set(before) | set(after)),
            },
            redo_callback=apply_visual_after,
            undo_callback=apply_visual_before,
        )
        transaction.batch_action = batch
        self.actions.commit(batch)
        self.undo_stack.append(transaction)
        self.redo_stack.clear()
        return transaction

    def _apply_state(self, state: Dict[TileKey, Optional[MapTile]]) -> None:
        for key, tile in state.items():
            if tile is None:
                self.tiles.pop(key, None)
            else:
                self.tiles[key] = tile.copy()

    def synchronize_editor_map(self) -> None:
        self.editor_map.tiles.clear()
        for key, tile in self.tiles.items():
            editable = self._editable_tile(tile)
            if editable is not None:
                self.editor_map.set_tile(editable, key)
        self.editor_map.consume_dirty_positions()

    def consume_dirty_positions(self) -> list[TileKey]:
        return self.editor_map.consume_dirty_positions()

    def action_audit(self) -> Dict[str, object]:
        return {
            **self.actions.audit(),
            "selection": self.selection_manager.audit(),
            "copybuffer": self.copybuffer.audit(),
            "workspace_core": self.workspace_core.audit(),
            "visual_operations_use_batch_action": True,
            "dirty_positions_pending": len(self.editor_map.modified),
        }

    def _editable_tile(self, tile: Optional[MapTile]) -> Optional[EditableTile]:
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

    def _sync_visual_from_editor_positions(
        self, positions: Iterable[TileKey]
    ) -> None:
        for key in positions:
            editable = self.editor_map.get_tile(key)
            if editable is None:
                self.tiles.pop(key, None)
                continue
            items = list(editable.items) + [item.item_id for item in editable.item_payloads]
            self.tiles[key] = MapTile(
                coord=TileCoord(*key),
                role=editable.role,
                brush=editable.brush,
                ground_id=editable.ground,
                item_id=items[-1] if items else None,
                items=items,
                zone=next(iter(sorted(editable.zones)), ""),
                zones=set(editable.zones),
                house_id=editable.house_id,
                spawn_monsters=list(editable.spawn_monsters),
                spawn_npcs=list(editable.spawn_npcs),
                waypoint=editable.waypoint,
                region=editable.region,
                metadata=dict(editable.metadata),
            )
