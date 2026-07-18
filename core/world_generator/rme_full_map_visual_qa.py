from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from core.editor import RMEEditorCore
from core.editor.editable_map import Position


FULL_MAP_BLOCKING_ISSUES = {
    "MISSING_OFFICIAL_SPRITE",
    "INVALID_GROUND_ITEM",
    "MISSING_GROUND",
    "STACK_ORDER_MISMATCH",
    "DRAW_ORDER_MISMATCH",
}


@dataclass
class FullMapChunkReport:
    chunk_index: int
    checked_tiles: int
    checked_items: int
    status: str
    issue_counts: dict[str, int]
    bounds: dict[str, int]
    issues: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "chunk_index": self.chunk_index,
            "status": self.status,
            "checked_tiles": self.checked_tiles,
            "checked_items": self.checked_items,
            "issue_counts": self.issue_counts,
            "bounds": self.bounds,
            "issues": self.issues,
        }


@dataclass
class FullMapVisualQAReport:
    status: str = "PASS"
    checked_tiles: int = 0
    checked_items: int = 0
    sprite_backed_items: int = 0
    chunk_size: int = 4096
    chunk_count: int = 0
    issue_counts: dict[str, int] = field(default_factory=dict)
    chunk_reports: list[FullMapChunkReport] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)

    def merge_chunk(self, chunk: FullMapChunkReport, raw_report: dict[str, object]) -> None:
        self.chunk_count += 1
        self.checked_tiles += chunk.checked_tiles
        self.checked_items += chunk.checked_items
        self.sprite_backed_items += int(raw_report.get("sprite_backed_items") or 0)
        for code, count in chunk.issue_counts.items():
            self.issue_counts[code] = self.issue_counts.get(code, 0) + int(count)
        if chunk.status == "BLOCKED" or any(code in FULL_MAP_BLOCKING_ISSUES for code in chunk.issue_counts):
            self.status = "BLOCKED"
        elif chunk.status == "WARN" and self.status == "PASS":
            self.status = "WARN"
        self.chunk_reports.append(chunk)

    def to_dict(self) -> dict[str, object]:
        return {
            "stage": "RME Full Map Chunked Visual QA",
            "status": self.status,
            "mandatory": True,
            "checked_tiles": self.checked_tiles,
            "checked_items": self.checked_items,
            "sprite_backed_items": self.sprite_backed_items,
            "chunk_size": self.chunk_size,
            "chunk_count": self.chunk_count,
            "issue_counts": dict(sorted(self.issue_counts.items())),
            "chunk_reports": [chunk.to_dict() for chunk in self.chunk_reports],
            "diagnostics": self.diagnostics,
            "blocks_on": [
                "MISSING_OFFICIAL_SPRITE",
                "INVALID_GROUND_ITEM",
                "MISSING_GROUND",
                "STACK_ORDER_MISMATCH",
                "DRAW_ORDER_MISMATCH",
                "RME_FIDELITY_GATE_BLOCKED",
            ],
            "warns_on": [],
        }


class RMEFullMapVisualQA:
    def __init__(self, root: str | Path = ".", chunk_size: int = 4096, max_issue_samples_per_chunk: int = 12) -> None:
        self.root = Path(root)
        self.chunk_size = max(1, int(chunk_size))
        self.max_issue_samples_per_chunk = max(0, int(max_issue_samples_per_chunk))

    def validate_editor_core(self, editor_core: RMEEditorCore) -> dict[str, object]:
        positions = sorted(editor_core.map.tiles)
        report = FullMapVisualQAReport(chunk_size=self.chunk_size)
        if not positions:
            report.status = "BLOCKED"
            report.diagnostics.append("No tiles available for full-map visual QA.")
            return report.to_dict()
        for chunk_index, chunk_positions in enumerate(_chunks(positions, self.chunk_size), start=1):
            raw = editor_core.fidelity_gate.validate(editor_core.map, chunk_positions).to_dict()
            chunk = FullMapChunkReport(
                chunk_index=chunk_index,
                checked_tiles=int(raw.get("checked_tiles") or 0),
                checked_items=int(raw.get("checked_items") or 0),
                status=str(raw.get("status") or "BLOCKED"),
                issue_counts={str(key): int(value) for key, value in (raw.get("issue_counts") or {}).items()},
                bounds=_bounds(chunk_positions),
                issues=list(raw.get("issues") or [])[: self.max_issue_samples_per_chunk],
            )
            report.merge_chunk(chunk, raw)
        return report.to_dict()


def run_full_map_visual_qa(
    editor_core: RMEEditorCore,
    root: str | Path = ".",
    chunk_size: int = 4096,
) -> dict[str, object]:
    return RMEFullMapVisualQA(root=root, chunk_size=chunk_size).validate_editor_core(editor_core)


def _chunks(positions: list[Position], chunk_size: int) -> Iterable[list[Position]]:
    for index in range(0, len(positions), chunk_size):
        yield positions[index : index + chunk_size]


def _bounds(positions: list[Position]) -> dict[str, int]:
    return {
        "min_x": min(position[0] for position in positions),
        "min_y": min(position[1] for position in positions),
        "min_z": min(position[2] for position in positions),
        "max_x": max(position[0] for position in positions),
        "max_y": max(position[1] for position in positions),
        "max_z": max(position[2] for position in positions),
    }
