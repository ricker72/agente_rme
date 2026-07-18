from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from core.editor.editable_map import EditableMap, Position


@dataclass
class BrushPostprocessReport:
    normalized_tiles: int = 0
    dirty_neighbors: set[Position] = field(default_factory=set)
    hooks_run: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "normalized_tiles": self.normalized_tiles,
            "dirty_neighbor_count": len(self.dirty_neighbors),
            "dirty_neighbors": sorted(self.dirty_neighbors),
            "hooks_run": self.hooks_run,
        }


class BrushPostprocessor:
    def __init__(self, editable_map: EditableMap, brush_engine: Any | None = None) -> None:
        self.editable_map = editable_map
        self.brush_engine = brush_engine

    def run(self, positions: Iterable[Position]) -> BrushPostprocessReport:
        report = BrushPostprocessReport()
        touched = set(tuple(position) for position in positions)
        expanded = set(touched)
        for x, y, z in touched:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    expanded.add((x + dx, y + dy, z))
        for position in sorted(expanded):
            tile = self.editable_map.get_tile(position)
            if tile is None:
                continue
            before = tile.stack_ids()
            self.editable_map.normalize_tile(position)
            after = self.editable_map.ensure_tile(position).stack_ids()
            if before != after or position in touched:
                self.editable_map.modified.add(position)
                report.dirty_neighbors.add(position)
            report.normalized_tiles += 1
        if self.brush_engine is not None:
            self._run_ground_and_border_hooks(expanded, report)
        return report

    def _run_ground_and_border_hooks(
        self, positions: set[Position], report: BrushPostprocessReport
    ) -> None:
        border_ids = {
            item_id
            for border in self.brush_engine.borders.values()
            for item_id in border.edges.values()
        }
        for z in sorted({position[2] for position in positions}):
            floor_positions = [position for position in positions if position[2] == z]
            grid: dict[tuple[int, int], dict[str, object]] = {}
            terrain_to_brush: dict[str, str] = {}
            for x, y, _floor in floor_positions:
                tile = self.editable_map.get_tile((x, y, z))
                if tile is None or tile.brush not in self.brush_engine.ground_brushes:
                    continue
                terrain = tile.metadata.get("terrain", tile.brush)
                terrain_to_brush[terrain] = tile.brush
                grid[(x, y)] = {
                    "terrain": terrain,
                    "ground": tile.ground,
                    "items": [item_id for item_id in tile.items if item_id not in border_ids],
                }
            if not grid:
                continue
            self.brush_engine.apply_ground_variants(grid, terrain_to_brush)
            self.brush_engine.apply_auto_borders(grid, terrain_to_brush)
            self.brush_engine.apply_optional_borders(grid, terrain_to_brush)
            for (x, y), state in grid.items():
                tile = self.editable_map.ensure_tile((x, y, z))
                tile.ground = int(state["ground"]) if state["ground"] is not None else None
                tile.items = [int(item_id) for item_id in state["items"]]
                self.editable_map.mark_dirty((x, y, z), "rme_brush_postprocess")
                report.dirty_neighbors.add((x, y, z))
            report.hooks_run.extend(["ground_variants", "borderize", "optional_borderize"])

    def audit(self) -> dict[str, object]:
        return {
            "brush_postprocessor_ready": True,
            "real_brush_engine_connected": self.brush_engine is not None,
            "hooks": ["ground_variants", "borderize", "optional_borderize"],
        }
