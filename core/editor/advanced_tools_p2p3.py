from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping, Sequence

from core.editor.action_queue import EditorAction, TileChange
from core.editor.editable_map import EditableMap, EditableTile, Position
from core.editor.gameplay_p1 import GameplayP1System, WaypointDefinition


@dataclass(frozen=True)
class CopyBufferTile:
    offset: Position
    stack: tuple[int, ...]
    flags: int = 0
    house_id: int | None = None
    zones: tuple[str, ...] = ()
    spawn_monsters: tuple[str, ...] = ()
    spawn_npcs: tuple[str, ...] = ()
    waypoint: str | None = None


@dataclass
class CopyBufferChunk:
    anchor: Position
    tiles: list[CopyBufferTile] = field(default_factory=list)

    def audit(self) -> dict[str, object]:
        return {
            "anchor": self.anchor,
            "tile_count": len(self.tiles),
            "item_count": sum(len(tile.stack) for tile in self.tiles),
        }


class CopyBufferTool:
    def __init__(self, editable_map: EditableMap) -> None:
        self.map = editable_map

    def copy(self, positions: Iterable[Position], anchor: Position | None = None) -> CopyBufferChunk:
        ordered = sorted({tuple(position) for position in positions})
        if not ordered:
            raise ValueError("copy buffer requires at least one position")
        anchor = tuple(anchor or ordered[0])
        ax, ay, az = anchor
        chunk = CopyBufferChunk(anchor=anchor)
        for position in ordered:
            tile = self.map.get_tile(position)
            if tile is None or tile.empty():
                continue
            chunk.tiles.append(
                CopyBufferTile(
                    offset=(position[0] - ax, position[1] - ay, position[2] - az),
                    stack=tuple(tile.stack_ids()),
                    flags=tile.flags,
                    house_id=tile.house_id,
                    zones=tuple(sorted(tile.zones)),
                    spawn_monsters=tuple(tile.spawn_monsters),
                    spawn_npcs=tuple(tile.spawn_npcs),
                    waypoint=tile.waypoint,
                )
            )
        return chunk

    def paste(
        self,
        chunk: CopyBufferChunk,
        destination: Position,
        mode: str = "replace",
        label: str = "Paste CopyBuffer",
    ) -> EditorAction:
        if mode not in {"replace", "merge", "skip_existing"}:
            raise ValueError(f"unsupported merge mode: {mode}")
        dx, dy, dz = destination
        changes: list[TileChange] = []
        for buffered in chunk.tiles:
            ox, oy, oz = buffered.offset
            position = (dx + ox, dy + oy, dz + oz)
            before = self.map.snapshot_tile(position)
            if mode == "skip_existing" and before and not before.empty():
                continue
            after = before.copy() if before and mode == "merge" else EditableTile(*position)
            if mode == "merge" and after.stack_ids():
                merged_stack = after.stack_ids() + list(buffered.stack)
            else:
                merged_stack = list(buffered.stack)
            temp = EditableMap(self.map.item_catalog)
            temp.set_stack(position, merged_stack)
            normalized = temp.snapshot_tile(position) or EditableTile(*position)
            after.ground = normalized.ground
            after.items = normalized.items
            after.flags = buffered.flags or after.flags
            after.house_id = buffered.house_id if buffered.house_id is not None else after.house_id
            after.zones.update(buffered.zones)
            after.spawn_monsters.extend(buffered.spawn_monsters)
            after.spawn_npcs.extend(buffered.spawn_npcs)
            after.waypoint = buffered.waypoint or after.waypoint
            changes.append(TileChange(position=position, before=before, after=after))
        return EditorAction(label=label, changes=changes)


@dataclass(frozen=True)
class ItemMatch:
    position: Position
    layer: str
    item_id: int
    name: str = ""


class FindReplaceTool:
    def __init__(self, editable_map: EditableMap) -> None:
        self.map = editable_map

    def find(
        self,
        item_id: int | None = None,
        name_contains: str | None = None,
        role: str | None = None,
    ) -> list[ItemMatch]:
        needle = (name_contains or "").lower()
        matches: list[ItemMatch] = []
        for position, tile in sorted(self.map.tiles.items()):
            for layer, current_id in _iter_tile_stack(tile):
                item = self.map.item_catalog.get(current_id)
                if item_id is not None and current_id != int(item_id):
                    continue
                if needle and needle not in item.name.lower():
                    continue
                if role and not bool(getattr(item, f"is_{role}", False)):
                    continue
                matches.append(ItemMatch(position=position, layer=layer, item_id=current_id, name=item.name))
        return matches

    def replace_item(
        self,
        source_id: int,
        target_id: int,
        label: str = "Replace Item",
        positions: Iterable[Position] | None = None,
    ) -> EditorAction:
        allowed_positions = {tuple(position) for position in positions} if positions is not None else None
        changes: list[TileChange] = []
        for position, tile in sorted(self.map.tiles.items()):
            if allowed_positions is not None and position not in allowed_positions:
                continue
            stack = tile.stack_ids()
            if int(source_id) not in stack:
                continue
            before = self.map.snapshot_tile(position)
            replaced = [int(target_id) if item_id == int(source_id) else item_id for item_id in stack]
            temp = EditableMap(self.map.item_catalog)
            temp.set_stack(position, replaced)
            after = temp.snapshot_tile(position)
            if after and before:
                after.flags = before.flags
                after.house_id = before.house_id
                after.zones = set(before.zones)
                after.spawn_monsters = list(before.spawn_monsters)
                after.spawn_npcs = list(before.spawn_npcs)
                after.waypoint = before.waypoint
            changes.append(TileChange(position=position, before=before, after=after))
        return EditorAction(label=label, changes=changes)

    def set_tile_properties(
        self,
        positions: Iterable[Position],
        *,
        flags: int | None = None,
        house_id: int | None = None,
        zones: Iterable[str] | None = None,
        waypoint: str | None = None,
        label: str = "Set Tile Properties",
    ) -> EditorAction:
        changes: list[TileChange] = []
        zone_set = set(zones or [])
        for position in sorted({tuple(position) for position in positions}):
            before = self.map.snapshot_tile(position)
            after = before.copy() if before else EditableTile(*position)
            if flags is not None:
                after.flags = int(flags)
            if house_id is not None:
                after.house_id = int(house_id)
            if zones is not None:
                after.zones = set(zone_set)
            if waypoint is not None:
                after.waypoint = waypoint
            changes.append(TileChange(position=position, before=before, after=after))
        return EditorAction(label=label, changes=changes)


class BitmapToMapTool:
    def __init__(self, editable_map: EditableMap) -> None:
        self.map = editable_map

    def build_action(
        self,
        origin: Position,
        bitmap: Sequence[Sequence[str]],
        palette: Mapping[str, Sequence[int]],
        label: str = "Bitmap To Map",
    ) -> EditorAction:
        ox, oy, oz = origin
        changes: list[TileChange] = []
        for y, row in enumerate(bitmap):
            for x, token in enumerate(row):
                if token not in palette:
                    continue
                position = (ox + x, oy + y, oz)
                before = self.map.snapshot_tile(position)
                temp = EditableMap(self.map.item_catalog)
                temp.set_stack(position, palette[token])
                after = temp.snapshot_tile(position)
                changes.append(TileChange(position=position, before=before, after=after))
        return EditorAction(label=label, changes=changes)


class LuaLikeEditorAPI:
    def __init__(self, tools: "AdvancedToolsP2P3") -> None:
        self.tools = tools

    def get_tile(self, position: Position) -> dict[str, object] | None:
        tile = self.tools.map.get_tile(position)
        if tile is None:
            return None
        return _tile_to_dict(tile)

    def set_stack(self, position: Position, item_ids: Iterable[int]) -> dict[str, object]:
        action = self.tools.actions.make_stack_action("LuaAPI set_stack", position, item_ids)
        self.tools.actions.commit(action)
        return self.get_tile(position) or {}

    def add_item(self, position: Position, item_id: int) -> dict[str, object]:
        tile = self.tools.map.ensure_tile(position)
        stack = tile.stack_ids() + [int(item_id)]
        return self.set_stack(position, stack)

    def replace_item(self, source_id: int, target_id: int) -> dict[str, object]:
        action = self.tools.find_replace.replace_item(source_id, target_id, "LuaAPI replace_item")
        self.tools.actions.commit(action)
        return {"changed_tiles": len(action.changes)}

    def add_waypoint(self, name: str, position: Position) -> dict[str, object]:
        waypoint = WaypointDefinition(name=name, position=position)
        self.tools.gameplay.add_waypoint(waypoint)
        return {"name": waypoint.name, "position": waypoint.position}


@dataclass(frozen=True)
class LiveEditEvent:
    sequence: int
    kind: str
    payload: dict[str, object]


class LiveEditSession:
    def __init__(self, tools: "AdvancedToolsP2P3") -> None:
        self.tools = tools
        self._next_sequence = 1
        self.pending: list[LiveEditEvent] = []
        self.applied: list[LiveEditEvent] = []

    def enqueue(self, kind: str, payload: Mapping[str, object]) -> LiveEditEvent:
        event = LiveEditEvent(sequence=self._next_sequence, kind=kind, payload=dict(payload))
        self._next_sequence += 1
        self.pending.append(event)
        return event

    def apply_pending(self) -> dict[str, object]:
        applied = 0
        while self.pending:
            event = self.pending.pop(0)
            if event.kind == "paint_stack":
                position = _position_from_payload(event.payload["position"])
                item_ids = [int(item_id) for item_id in event.payload["item_ids"]]  # type: ignore[index]
                action = self.tools.actions.make_stack_action("Live paint_stack", position, item_ids)
                self.tools.actions.commit(action)
            elif event.kind == "replace_item":
                action = self.tools.find_replace.replace_item(
                    int(event.payload["source_id"]),
                    int(event.payload["target_id"]),
                    "Live replace_item",
                )
                self.tools.actions.commit(action)
            elif event.kind == "cursor":
                pass
            else:
                raise ValueError(f"unsupported live edit event: {event.kind}")
            self.applied.append(event)
            applied += 1
        return {"applied_events": applied, "last_sequence": self.applied[-1].sequence if self.applied else 0}

    def audit(self) -> dict[str, object]:
        return {
            "live_edit_ready": True,
            "pending_events": len(self.pending),
            "applied_events": len(self.applied),
            "protocol_events": ["cursor", "paint_stack", "replace_item"],
        }


class AdvancedToolsP2P3:
    def __init__(self, editable_map: EditableMap, actions, gameplay: GameplayP1System) -> None:
        self.map = editable_map
        self.actions = actions
        self.gameplay = gameplay
        self.copybuffer = CopyBufferTool(editable_map)
        self.find_replace = FindReplaceTool(editable_map)
        self.bitmap_to_map = BitmapToMapTool(editable_map)
        self.lua = LuaLikeEditorAPI(self)
        self.live = LiveEditSession(self)

    def import_chunk(
        self,
        chunk: CopyBufferChunk,
        destination: Position,
        mode: str = "merge",
        label: str = "Import/Merge Chunk",
    ) -> dict[str, object]:
        action = self.copybuffer.paste(chunk, destination, mode=mode, label=label)
        self.actions.commit(action)
        return {"mode": mode, "changed_tiles": len(action.changes), "destination": destination}

    def audit(self) -> dict[str, object]:
        return {
            "advanced_tools_ready": True,
            "copybuffer": "copybuffer.cpp/h style relative chunk copy/paste",
            "import_merge": ["replace", "merge", "skip_existing"],
            "bitmap_to_map": True,
            "find_replace_properties": True,
            "lua_like_api": ["map", "tile", "item", "brush"],
            "live_editing": self.live.audit(),
            "source_coverage": [
                "copybuffer.cpp/h",
                "import/merge",
                "bitmap-to-map",
                "find_item_window.cpp",
                "replace_items_window.cpp",
                "properties windows",
                "lua/lua_api_map.cpp",
                "lua/lua_api_tile.cpp",
                "lua/lua_api_item.cpp",
                "lua/lua_api_brush.cpp",
                "live_*",
                "net_connection.*",
            ],
        }


def _iter_tile_stack(tile: EditableTile) -> Iterable[tuple[str, int]]:
    if tile.ground is not None:
        yield "ground", tile.ground
    for index, item_id in enumerate(tile.items):
        yield f"item:{index}", item_id


def _tile_to_dict(tile: EditableTile) -> dict[str, object]:
    return {
        "position": tile.position,
        "ground": tile.ground,
        "items": list(tile.items),
        "flags": tile.flags,
        "house_id": tile.house_id,
        "zones": sorted(tile.zones),
        "spawn_monsters": list(tile.spawn_monsters),
        "spawn_npcs": list(tile.spawn_npcs),
        "waypoint": tile.waypoint,
    }


def _position_from_payload(value: object) -> Position:
    raw = list(value)  # type: ignore[arg-type]
    if len(raw) != 3:
        raise ValueError("position payload must contain x, y and z")
    return (int(raw[0]), int(raw[1]), int(raw[2]))
