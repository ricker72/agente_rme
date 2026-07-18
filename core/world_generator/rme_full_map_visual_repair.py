from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.editor import RMEEditorCore
from core.editor.editable_map import Position
from core.editor.item_type_flags import RMEItemTypeCatalog
from core.world_generator.rme_full_map_visual_qa import run_full_map_visual_qa
from rme_rendering.rme_draw_order import RMEDrawOrderEngine, RMEStackItem


@dataclass
class FullMapVisualRepairIteration:
    iteration: int
    before_status: str
    before_issue_counts: dict[str, int]
    repaired_tiles: int
    repaired_positions: list[Position] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "iteration": self.iteration,
            "before_status": self.before_status,
            "before_issue_counts": self.before_issue_counts,
            "repaired_tiles": self.repaired_tiles,
            "repaired_positions": self.repaired_positions,
        }


def repair_full_map_draw_order_mismatches(
    editor_core: RMEEditorCore,
    root: str | Path = ".",
    *,
    chunk_size: int = 4096,
    max_iterations: int = 3,
) -> dict[str, object]:
    iterations: list[FullMapVisualRepairIteration] = []
    final_report: dict[str, object] = {}
    for iteration in range(1, max(1, max_iterations) + 1):
        before = run_full_map_visual_qa(editor_core, root=root, chunk_size=chunk_size)
        positions = _issue_positions(before, {"DRAW_ORDER_MISMATCH", "STACK_ORDER_MISMATCH"})
        if not positions:
            final_report = before
            break
        repaired = _repair_positions(editor_core, positions)
        iterations.append(
            FullMapVisualRepairIteration(
                iteration=iteration,
                before_status=str(before.get("status")),
                before_issue_counts={str(k): int(v) for k, v in (before.get("issue_counts") or {}).items()},
                repaired_tiles=len(repaired),
                repaired_positions=sorted(repaired),
            )
        )
        after = run_full_map_visual_qa(editor_core, root=root, chunk_size=chunk_size)
        final_report = after
        if after.get("status") == "PASS":
            break
        if not repaired:
            break
    if not final_report:
        final_report = run_full_map_visual_qa(editor_core, root=root, chunk_size=chunk_size)
    return {
        "stage": "RME Full Map Visual Auto Repair",
        "status": "PASS" if final_report.get("status") == "PASS" else "BLOCKED",
        "iterations": [item.to_dict() for item in iterations],
        "final_full_map_visual_qa": final_report,
        "repair_policy": "Only stack order/draw order mismatches are auto-reordered; missing sprites or invalid grounds remain blocking.",
    }


def _issue_positions(report: dict[str, object], codes: set[str]) -> list[Position]:
    positions: set[Position] = set()
    for chunk in report.get("chunk_reports") or []:
        if not isinstance(chunk, dict):
            continue
        for issue in chunk.get("issues") or []:
            if not isinstance(issue, dict) or issue.get("code") not in codes:
                continue
            raw_position = issue.get("position")
            if isinstance(raw_position, (list, tuple)) and len(raw_position) == 3:
                positions.add((int(raw_position[0]), int(raw_position[1]), int(raw_position[2])))
    return sorted(positions)


def _repair_positions(editor_core: RMEEditorCore, positions: list[Position]) -> set[Position]:
    repaired: set[Position] = set()
    draw_order = RMEDrawOrderEngine()
    catalog = editor_core.map.item_catalog or RMEItemTypeCatalog()
    for position in positions:
        tile = editor_core.map.get_tile(position)
        if tile is None:
            continue
        ordered_items = _draw_order_items(catalog, draw_order, tile.items)
        if ordered_items == tile.items:
            continue
        editor_core.map.set_stack_exact(position, tile.ground, ordered_items)
        repaired.add(position)
    return repaired


def _draw_order_items(catalog: RMEItemTypeCatalog, draw_order: RMEDrawOrderEngine, item_ids: list[int]) -> list[int]:
    stack = [
        RMEStackItem(
            item_id=int(item_id),
            appearance_id=int(item_id),
            role=_role_for_overlay(catalog, int(item_id)),
            source_index=index,
        )
        for index, item_id in enumerate(item_ids)
    ]
    return [item.item_id for item in draw_order.sort_stack(stack)]


def _role_for_overlay(catalog: RMEItemTypeCatalog, item_id: int) -> str:
    item = catalog.get(item_id)
    if item.is_border:
        return "BORDER"
    if item.is_wall:
        return "WALL"
    if item.is_door:
        return "DOOR"
    if item.is_carpet:
        return "CARPET"
    if item.is_table:
        return "TABLE"
    return "DECORATION"
