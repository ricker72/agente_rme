from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from core.editor import RMEEditorCore
from core.editor.editable_map import Position
from core.world_generator.rme_materials_necro_v5 import build_venore_palette, classify_items, load_material_catalog


@dataclass
class VisualRepairReport:
    status: str = "PASS"
    invalid_ground_tiles: int = 0
    find_replace_repairs: int = 0
    copybuffer_repairs: int = 0
    bitmap_to_map_repairs: int = 0
    postprocess: dict[str, object] = field(default_factory=dict)
    diagnostics: list[str] = field(default_factory=list)
    repair_events: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": "RME Visual Repair Loop",
            "status": self.status,
            "invalid_ground_tiles": self.invalid_ground_tiles,
            "find_replace_repairs": self.find_replace_repairs,
            "copybuffer_repairs": self.copybuffer_repairs,
            "bitmap_to_map_repairs": self.bitmap_to_map_repairs,
            "postprocess": self.postprocess,
            "diagnostics": self.diagnostics,
            "repair_events": self.repair_events[:200],
            "tools_used": ["find/replace", "copybuffer", "bitmap-to-map", "brush_postprocess"],
        }


class RMEVisualRepairLoop:
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)
        self.catalog = load_material_catalog(self.root)
        self.classification = classify_items(self.catalog)
        self.palette = build_venore_palette(self.catalog, self.classification)
        self.invalid_ground_ids = set(int(item_id) for item_id in self.classification["categories"]["invalid_for_ground"])
        self.valid_ground_ids = set(int(item_id) for item_id in self.classification["categories"]["valid_base_ground"])
        base = self.palette.get("base_ground") or {}
        self.default_ground = int(
            base.get("grass_ground")
            or base.get("stone_road")
            or base.get("muddy_floor")
            or next(iter(sorted(self.valid_ground_ids)), 1)
        )

    def repair(self, editor_core: RMEEditorCore, bounds: tuple[int, int, int, int, int] | None = None) -> VisualRepairReport:
        report = VisualRepairReport()
        touched: set[Position] = set()
        bounds = bounds or _bounds_from_tiles(editor_core.map.tiles.keys())

        invalid_by_id: dict[int, list[Position]] = defaultdict(list)
        for position, tile in sorted(editor_core.map.tiles.items()):
            if tile.ground is None:
                continue
            if int(tile.ground) in self.invalid_ground_ids or not self._looks_like_safe_ground(int(tile.ground)):
                invalid_by_id[int(tile.ground)].append(position)

        report.invalid_ground_tiles = sum(len(positions) for positions in invalid_by_id.values())
        for source_id, positions in sorted(invalid_by_id.items()):
            replacement = self._replacement_ground(editor_core, positions)
            action = editor_core.advanced.find_replace.replace_item(
                source_id,
                replacement,
                label=f"Visual Repair replace invalid ground {source_id}",
                positions=positions,
            )
            editor_core.actions.commit(action)
            touched.update(change.position for change in action.changes)
            report.find_replace_repairs += len(action.changes)
            report.repair_events.append(
                {
                    "tool": "find/replace",
                    "source_id": source_id,
                    "target_id": replacement,
                    "changed_tiles": len(action.changes),
                }
            )

        copy_repairs = self._repair_neighbor_holes_with_copybuffer(editor_core, bounds)
        report.copybuffer_repairs = len(copy_repairs)
        touched.update(copy_repairs)
        if copy_repairs:
            report.repair_events.append({"tool": "copybuffer", "changed_tiles": len(copy_repairs)})

        bitmap_repairs = self._repair_remaining_holes_with_bitmap(editor_core, bounds)
        report.bitmap_to_map_repairs = len(bitmap_repairs)
        touched.update(bitmap_repairs)
        if bitmap_repairs:
            report.repair_events.append(
                {"tool": "bitmap-to-map", "ground_id": self.default_ground, "changed_tiles": len(bitmap_repairs)}
            )

        if touched:
            report.postprocess = editor_core.postprocessor.run(touched).to_dict()
        else:
            report.postprocess = editor_core.postprocessor.run(editor_core.map.tiles.keys()).to_dict()

        remaining_bad = [
            position
            for position, tile in sorted(editor_core.map.tiles.items())
            if tile.ground is not None and int(tile.ground) in self.invalid_ground_ids
        ]
        if remaining_bad:
            report.status = "REPAIRED_WITH_WARNINGS"
            report.diagnostics.append(f"remaining invalid ground tiles: {len(remaining_bad)}")
        fidelity = editor_core.fidelity_gate.validate(editor_core.map, touched or None).to_dict()
        report.repair_events.append({"tool": "rme_fidelity_gate", "status": fidelity["status"]})
        if fidelity["status"] == "BLOCKED":
            report.status = "BLOCKED"
            report.diagnostics.append("RME fidelity gate blocked visual output; inspect fidelity_gate in the report.")
        report.postprocess["fidelity_gate"] = fidelity
        return report

    def _looks_like_safe_ground(self, item_id: int) -> bool:
        return item_id not in self.invalid_ground_ids

    def _replacement_ground(self, editor_core: RMEEditorCore, positions: Iterable[Position]) -> int:
        neighbor_grounds: Counter[int] = Counter()
        for position in positions:
            for neighbor in editor_core.map.neighbors8(position).values():
                if neighbor and neighbor.ground and int(neighbor.ground) in self.valid_ground_ids:
                    neighbor_grounds[int(neighbor.ground)] += 1
        if neighbor_grounds:
            return neighbor_grounds.most_common(1)[0][0]
        return self.default_ground

    def _repair_neighbor_holes_with_copybuffer(
        self,
        editor_core: RMEEditorCore,
        bounds: tuple[int, int, int, int, int],
        limit: int = 64,
    ) -> set[Position]:
        min_x, min_y, max_x, max_y, z = bounds
        repaired: set[Position] = set()
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if len(repaired) >= limit:
                    return repaired
                position = (x, y, z)
                if editor_core.map.get_tile(position) is not None:
                    continue
                source = self._best_neighbor_source(editor_core, position)
                if source is None:
                    continue
                chunk = editor_core.advanced.copybuffer.copy([source], anchor=source)
                action = editor_core.advanced.copybuffer.paste(
                    chunk,
                    position,
                    mode="replace",
                    label="Visual Repair copybuffer hole fill",
                )
                editor_core.actions.commit(action)
                if action.changes:
                    repaired.add(position)
        return repaired

    def _repair_remaining_holes_with_bitmap(
        self,
        editor_core: RMEEditorCore,
        bounds: tuple[int, int, int, int, int],
        limit: int = 64,
    ) -> set[Position]:
        min_x, min_y, max_x, max_y, z = bounds
        holes: list[Position] = []
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if len(holes) >= limit:
                    break
                position = (x, y, z)
                if editor_core.map.get_tile(position) is None and _has_any_neighbor(editor_core, position):
                    holes.append(position)
        repaired: set[Position] = set()
        for position in holes:
            action = editor_core.advanced.bitmap_to_map.build_action(
                position,
                [["g"]],
                {"g": [self.default_ground]},
                label="Visual Repair bitmap hole fill",
            )
            editor_core.actions.commit(action)
            if action.changes:
                repaired.add(position)
        return repaired

    def _best_neighbor_source(self, editor_core: RMEEditorCore, position: Position) -> Position | None:
        for neighbor in editor_core.map.neighbors8(position).values():
            if neighbor and neighbor.ground and int(neighbor.ground) in self.valid_ground_ids:
                return neighbor.position
        return None


def repair_editor_core_visual_zones(
    editor_core: RMEEditorCore,
    root: str | Path = ".",
    bounds: tuple[int, int, int, int, int] | None = None,
) -> dict[str, object]:
    return RMEVisualRepairLoop(root).repair(editor_core, bounds=bounds).to_dict()


def _bounds_from_tiles(positions: Iterable[Position]) -> tuple[int, int, int, int, int]:
    points = list(positions)
    if not points:
        return (0, 0, 0, 0, 7)
    z_counts = Counter(position[2] for position in points)
    z = z_counts.most_common(1)[0][0]
    floor_points = [position for position in points if position[2] == z]
    return (
        min(position[0] for position in floor_points),
        min(position[1] for position in floor_points),
        max(position[0] for position in floor_points),
        max(position[1] for position in floor_points),
        z,
    )


def _has_any_neighbor(editor_core: RMEEditorCore, position: Position) -> bool:
    return any(neighbor is not None for neighbor in editor_core.map.neighbors8(position).values())
