from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from core.editor import RMEEditorCore
from core.editor.action_queue import ActionIdentifier
from core.world_generator.rme_visual_repair_loop import repair_editor_core_visual_zones

from .mapping_engine import MapTile, MappingTransaction, OpenTibiaMappingEngine, TileCoord, TileKey


class RMEEditorToolsBridge:
    def __init__(self, mapping_engine: OpenTibiaMappingEngine, root: str | Path = ".") -> None:
        self.mapping_engine = mapping_engine
        self.root = Path(root)

    def to_editor_core(self) -> RMEEditorCore:
        core = RMEEditorCore(self.root)
        for key, tile in sorted(self.mapping_engine.tiles.items()):
            stack: list[int] = []
            if tile.ground_id is not None:
                stack.append(int(tile.ground_id))
            stack.extend(int(item_id) for item_id in tile.items)
            if stack:
                core.map.set_stack(key, stack)
        return core

    def repair_visual_zones(self) -> dict[str, object]:
        before = {key: tile.copy() for key, tile in self.mapping_engine.tiles.items()}
        core = self.to_editor_core()
        bounds = _bounds_from_mapping_engine(self.mapping_engine)
        report = repair_editor_core_visual_zones(core, root=self.root, bounds=bounds)
        after = _mapping_tiles_from_editor_core(core)
        transaction = MappingTransaction(
            name="RME Visual Repair Loop",
            before={key: before.get(key) for key in set(before) | set(after)},
            after={key: after.get(key) for key in set(before) | set(after)},
        )
        self.mapping_engine._commit(
            transaction.name,
            transaction.before,
            transaction.after,
            ActionIdentifier.AI_REPAIR,
        )
        report["ui_bridge"] = {
            "before_tiles": len(before),
            "after_tiles": len(self.mapping_engine.tiles),
            "transaction": transaction.name,
        }
        return report


def _mapping_tiles_from_editor_core(core: RMEEditorCore) -> Dict[TileKey, Optional[MapTile]]:
    tiles: Dict[TileKey, Optional[MapTile]] = {}
    for position, editable_tile in sorted(core.map.tiles.items()):
        coord = TileCoord(*position)
        stack = editable_tile.stack_ids()
        tile = MapTile(coord=coord)
        tile.ground_id = editable_tile.ground
        tile.items = list(editable_tile.items)
        tile.item_id = tile.items[-1] if tile.items else None
        tile.role = "ground" if editable_tile.ground is not None else "item"
        tile.brush = "rme_editor_core"
        if editable_tile.zones:
            tile.zone = ",".join(sorted(editable_tile.zones))
        if editable_tile.waypoint:
            tile.metadata["waypoint"] = editable_tile.waypoint
        if stack:
            tile.metadata["rme_stack"] = ",".join(str(item_id) for item_id in stack)
        tiles[position] = tile
    return tiles


def _bounds_from_mapping_engine(engine: OpenTibiaMappingEngine) -> tuple[int, int, int, int, int] | None:
    if not engine.tiles:
        return None
    points = list(engine.tiles)
    z = engine.cursor.z
    floor_points = [point for point in points if point[2] == z] or points
    return (
        min(point[0] for point in floor_points),
        min(point[1] for point in floor_points),
        max(point[0] for point in floor_points),
        max(point[1] for point in floor_points),
        floor_points[0][2],
    )
