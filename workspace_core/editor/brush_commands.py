"""Transactional RME material brush commands over the canonical workspace map."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from core.editor.brush_postprocessor import BrushPostprocessor
from core.editor.item_type_flags import RMEItemTypeCatalog
from core.editor.material_catalog import MaterialBrushRef, RMEMaterialCatalog
from core.world_generator.rme_brush_engine import RMEBrushEngine
from core.world_generator.rme_materials_necro_v5 import (
    classify_items,
    load_material_catalog,
)

from .actions import ActionIdentifier, BatchAction, TileChange
from .model import EditableMap, EditableTile, Position


@dataclass(frozen=True)
class BrushCommandResult:
    brush_name: str
    brush_type: str
    positions: tuple[Position, ...]
    action: BatchAction
    postprocess: dict[str, object]


class WorkspaceBrushCommands:
    """Resolve official materials and commit each stroke as one BatchAction."""

    def __init__(self, workspace: object, root: str | Path = ".") -> None:
        self.workspace = workspace
        self.root = Path(root)
        self.materials: RMEMaterialCatalog | None = None
        self.brush_engine: RMEBrushEngine | None = None
        self.postprocessor: BrushPostprocessor | None = None

    def load(self) -> "WorkspaceBrushCommands":
        if self.materials is not None:
            return self
        editable_map = self.workspace.editable_map
        editable_map.item_catalog = RMEItemTypeCatalog.load(self.root)
        self.materials = RMEMaterialCatalog.load(self.root)
        classification = classify_items(load_material_catalog(self.root))
        self.brush_engine = RMEBrushEngine.load(self.root, classification)
        self.postprocessor = BrushPostprocessor(editable_map, self.brush_engine)
        return self

    def apply(
        self,
        brush_name: str,
        positions: Iterable[Position],
        *,
        label: str | None = None,
        align: str = "auto",
        doors: Iterable[Position] = (),
        door_type: str = "normal",
        semantic_role: str | None = None,
        house_id: int | None = None,
        house_exit: Position | None = None,
    ) -> BrushCommandResult:
        self.load()
        assert self.materials is not None and self.postprocessor is not None
        key = brush_name.strip().lower()
        brush = self.materials.brushes.get(key)
        if brush is None:
            raise KeyError(f"Unknown official RME brush: {brush_name}")
        engine_backed_types = {
            "wall",
            "doodad",
            "table",
            "carpet",
            "wall decoration",
        }
        if brush.item_id is None and brush.brush_type not in engine_backed_types:
            raise ValueError(f"RME brush has no material look/item id: {brush.name}")
        coords = tuple(sorted({tuple(int(value) for value in pos) for pos in positions}))
        if not coords:
            raise ValueError("Brush command requires at least one position")
        floors = {position[2] for position in coords}
        if len(floors) != 1:
            raise ValueError("One brush command cannot mix floors")
        door_coords = tuple(
            sorted({tuple(int(value) for value in pos) for pos in doors})
        )
        if any(position[2] not in floors for position in door_coords):
            raise ValueError("Doors must be on the same floor as their wall")
        affected = self._expanded(coords, amount=4 if brush.brush_type == "doodad" else 1)
        if house_exit is not None:
            normalized_exit = tuple(int(value) for value in house_exit)
            if normalized_exit[2] not in floors:
                raise ValueError("House exit must be on the same floor as the house stroke")
            affected = tuple(sorted(set(affected) | {normalized_exit}))
        staged = EditableMap(self.workspace.editable_map.item_catalog)
        for position in affected:
            existing = self.workspace.editable_map.snapshot_tile(position)
            if existing is not None:
                staged.set_tile(existing, position)
        assert self.brush_engine is not None
        family_report = self._apply_family(
            staged,
            brush,
            coords,
            affected,
            align=align,
            doors=door_coords,
            door_type=door_type,
            semantic_role=semantic_role,
        )
        if house_id is not None:
            self._apply_house_metadata(staged, coords, house_id, house_exit)
        postprocess = BrushPostprocessor(staged, self.brush_engine).run(coords).to_dict()
        report = {**postprocess, "family": family_report}
        changes = []
        for position in affected:
            before = self.workspace.editable_map.snapshot_tile(position)
            after = staged.snapshot_tile(position)
            if before != after:
                changes.append(TileChange(position=position, before=before, after=after))
        action = BatchAction(
            label=label or f"{brush.brush_type.title()} Brush: {brush.name}",
            identifier=ActionIdentifier.DRAW,
            changes=changes,
            metadata={
                "workspace_core_brush": True,
                "brush_name": brush.name,
                "brush_type": brush.brush_type,
                "source_file": brush.source_file,
                "semantic_role": semantic_role or brush.brush_type,
                "door_count": len(door_coords),
                "house_id": house_id,
                "house_exit": house_exit,
            },
        )
        self.workspace.actions.commit(action)
        return BrushCommandResult(
            brush_name=brush.name,
            brush_type=brush.brush_type,
            positions=coords,
            action=action,
            postprocess=report,
        )

    def _apply_to_tile(self, after: EditableTile, brush: MaterialBrushRef) -> None:
        if brush.brush_type == "ground":
            after.ground = int(brush.item_id)
            after.role = "ground"
        else:
            if brush.item_id is None:
                raise ValueError(f"RME brush has no material item id: {brush.name}")
            after.items.append(int(brush.item_id))
            after.role = brush.brush_type
        after.brush = brush.name.lower()
        after.metadata["material_source"] = brush.source_file
        after.metadata["terrain"] = brush.name.lower()

    def _apply_family(
        self,
        staged: EditableMap,
        brush: MaterialBrushRef,
        positions: tuple[Position, ...],
        affected: tuple[Position, ...],
        *,
        align: str,
        doors: tuple[Position, ...],
        door_type: str,
        semantic_role: str | None,
    ) -> dict[str, object]:
        assert self.brush_engine is not None
        if brush.brush_type == "ground":
            for position in positions:
                self._apply_to_tile(staged.ensure_tile(position), brush)
            return {"system": "ground", "placed": len(positions)}

        z = positions[0][2]
        grid = self._grid(staged, affected, z, set(positions))
        xy_positions = [(x, y) for x, y, _floor in positions]
        if brush.brush_type == "wall":
            wall_brush = self.brush_engine.wall_brush(brush.name)
            wall_positions = set(xy_positions)
            if wall_brush is not None:
                wall_ids = set(wall_brush.variants.values()) | {
                    item_id
                    for door_types in wall_brush.doors.values()
                    for item_ids in door_types.values()
                    for item_id in item_ids
                }
                for (x, y), state in grid.items():
                    tile = staged.get_tile((x, y, z))
                    if tile is not None and tile.brush == brush.name.lower():
                        wall_positions.add((x, y))
                    state["items"] = [
                        item_id
                        for item_id in state["items"]
                        if item_id not in wall_ids
                    ]
            family = self.brush_engine.apply_walls(
                grid,
                [
                    {
                        "brush": brush.name,
                        "positions": sorted(wall_positions),
                        "doors": [(x, y) for x, y, _floor in doors],
                        "door_type": door_type,
                    }
                ],
            )
            system = "wall_door"
        elif brush.brush_type == "doodad":
            family = self.brush_engine.apply_doodads(
                grid,
                [
                    {
                        "brush": brush.name,
                        "terrains": ["__brush_target__"],
                        "modulo": 1,
                        "residue": 0,
                        "max_count": len(positions),
                    }
                ],
            )
            system = "roof" if semantic_role == "roof" else "doodad"
        elif brush.brush_type in {"table", "carpet", "wall decoration"}:
            kind = brush.brush_type.replace(" ", "_")
            family = self.brush_engine.apply_oriented_items(
                grid,
                [
                    {
                        "kind": kind,
                        "brush": brush.name,
                        "positions": xy_positions,
                        "align": align,
                    }
                ],
            )
            system = kind
        else:
            for position in positions:
                self._apply_to_tile(staged.ensure_tile(position), brush)
            return {"system": brush.brush_type, "placed": len(positions)}
        self._grid_to_map(
            staged,
            grid,
            z,
            semantic_role or system,
            brush,
            set(positions),
        )
        return {"system": system, **family}

    @staticmethod
    def _grid(
        staged: EditableMap,
        affected: tuple[Position, ...],
        z: int,
        targets: set[Position],
    ) -> dict[tuple[int, int], dict[str, object]]:
        grid: dict[tuple[int, int], dict[str, object]] = {}
        for x, y, floor in affected:
            if floor != z:
                continue
            tile = staged.get_tile((x, y, z))
            terrain = "__brush_target__" if (x, y, z) in targets else ""
            if tile is not None and terrain != "__brush_target__":
                terrain = tile.metadata.get("terrain", tile.brush)
            grid[(x, y)] = {
                "terrain": terrain,
                "ground": tile.ground if tile else None,
                "items": list(tile.items) if tile else [],
            }
        return grid

    @staticmethod
    def _grid_to_map(
        staged: EditableMap,
        grid: dict[tuple[int, int], dict[str, object]],
        z: int,
        role: str,
        brush: MaterialBrushRef,
        targets: set[Position],
    ) -> None:
        for (x, y), state in grid.items():
            position = (x, y, z)
            ground = state.get("ground")
            items = [int(item_id) for item_id in state.get("items", [])]
            existing = staged.get_tile(position)
            if existing is None and ground is None and not items:
                continue
            tile = staged.ensure_tile(position)
            previous_items = list(tile.items)
            tile.ground = int(ground) if ground is not None else None
            tile.items = items
            if position in targets or items != previous_items:
                tile.role = role
                tile.brush = brush.name.lower()
                tile.metadata["material_source"] = brush.source_file
                tile.metadata["terrain"] = brush.name.lower()

    @staticmethod
    def _apply_house_metadata(
        staged: EditableMap,
        positions: tuple[Position, ...],
        house_id: int,
        house_exit: Position | None,
    ) -> None:
        if house_id <= 0:
            raise ValueError("house_id must be positive")
        for position in positions:
            tile = staged.ensure_tile(position)
            tile.house_id = int(house_id)
            tile.zones.add("HOUSE")
        if house_exit is not None:
            exit_position = tuple(int(value) for value in house_exit)
            tile = staged.ensure_tile(exit_position)
            tile.house_id = int(house_id)
            tile.zones.add("HOUSE_EXIT")

    @staticmethod
    def _expanded(
        positions: tuple[Position, ...], amount: int = 1
    ) -> tuple[Position, ...]:
        expanded: set[Position] = set()
        for x, y, z in positions:
            for dx in range(-amount, amount + 1):
                for dy in range(-amount, amount + 1):
                    expanded.add((x + dx, y + dy, z))
        return tuple(sorted(expanded))

    def audit(self) -> dict[str, object]:
        return {
            "workspace_brush_commands_ready": self.materials is not None,
            "lazy_loaded": True,
            "single_action_per_stroke": True,
            "postprocess_connected": self.postprocessor is not None,
            "material_catalog": self.materials.audit() if self.materials else {},
            "brush_engine": self.brush_engine.audit() if self.brush_engine else {},
        }


__all__ = ["BrushCommandResult", "WorkspaceBrushCommands"]
