from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from core.editor.editable_map import EditableMap, Position
from core.editor.item_type_flags import RMEItemTypeCatalog
from core.editor.material_catalog import RMEMaterialCatalog
from rme_rendering.rme_draw_order import RMEDrawOrderEngine, RMEStackItem
from rme_rendering.rme_visual_compat import audit_rme_visual_contract


@dataclass
class RMEFidelityIssue:
    code: str
    severity: str
    position: Position | None
    item_id: int | None
    message: str

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "severity": self.severity,
            "position": self.position,
            "item_id": self.item_id,
            "message": self.message,
        }


@dataclass
class RMEFidelityReport:
    status: str = "PASS"
    checked_tiles: int = 0
    checked_items: int = 0
    sprite_backed_items: int = 0
    issues: list[RMEFidelityIssue] = field(default_factory=list)
    render_contract: dict[str, object] = field(default_factory=dict)
    brush_contract: dict[str, object] = field(default_factory=dict)
    item_flag_contract: dict[str, object] = field(default_factory=dict)

    def add_issue(self, issue: RMEFidelityIssue) -> None:
        self.issues.append(issue)
        if issue.severity == "BLOCKER":
            self.status = "BLOCKED"
        elif self.status == "PASS":
            self.status = "WARN"

    def to_dict(self) -> dict[str, object]:
        counts: dict[str, int] = {}
        for issue in self.issues:
            counts[issue.code] = counts.get(issue.code, 0) + 1
        return {
            "stage": "RME Fidelity Gate",
            "status": self.status,
            "checked_tiles": self.checked_tiles,
            "checked_items": self.checked_items,
            "sprite_backed_items": self.sprite_backed_items,
            "issue_counts": dict(sorted(counts.items())),
            "issues": [issue.to_dict() for issue in self.issues[:200]],
            "render_contract": self.render_contract,
            "brush_contract": self.brush_contract,
            "item_flag_contract": self.item_flag_contract,
            "contracts": ["render", "brush_engine", "item_flags", "visual_qa"],
        }


class RMEFidelityGate:
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)
        self.item_catalog = RMEItemTypeCatalog.load(self.root)
        self.material_catalog = RMEMaterialCatalog.load(self.root)
        self.draw_order = RMEDrawOrderEngine()
        self.sprite_backed_ids = _load_sprite_backed_item_ids(self.root)
        self.invalid_ground_ids = _load_invalid_ground_ids(self.root)

    def validate(self, editable_map: EditableMap, touched: Iterable[Position] | None = None) -> RMEFidelityReport:
        catalog = editable_map.item_catalog or self.item_catalog
        positions = sorted({tuple(position) for position in touched}) if touched is not None else sorted(editable_map.tiles)
        report = RMEFidelityReport(
            render_contract={
                **audit_rme_visual_contract(),
                **self.draw_order.audit(),
                "sprite_backed_catalog_loaded": bool(self.sprite_backed_ids),
                "strict_no_placeholder_policy": True,
            },
            brush_contract={
                **self.material_catalog.audit(),
                "postprocess_hooks_required": ["borderize", "wallize", "tableize", "carpetize"],
            },
            item_flag_contract={
                **catalog.audit(),
                "invalid_ground_catalog_loaded": bool(self.invalid_ground_ids),
                "invalid_ground_count": len(self.invalid_ground_ids),
            },
        )
        for position in positions:
            tile = editable_map.get_tile(position)
            if tile is None:
                continue
            stack = tile.stack_ids()
            report.checked_tiles += 1
            report.checked_items += len(stack)
            self._validate_sprites(report, position, stack)
            self._validate_ground(report, position, tile.ground, catalog)
            self._validate_stack_order(report, position, stack, catalog)
        return report

    def _validate_sprites(self, report: RMEFidelityReport, position: Position, stack: list[int]) -> None:
        if not self.sprite_backed_ids:
            report.add_issue(
                RMEFidelityIssue(
                    code="SPRITE_CATALOG_MISSING",
                    severity="WARN",
                    position=position,
                    item_id=None,
                    message="No APPEARANCE sprite-backed catalog was found; render QA cannot prove official sprites.",
                )
            )
            return
        for item_id in stack:
            if int(item_id) in self.sprite_backed_ids:
                report.sprite_backed_items += 1
                continue
            report.add_issue(
                RMEFidelityIssue(
                    code="MISSING_OFFICIAL_SPRITE",
                    severity="BLOCKER",
                    position=position,
                    item_id=int(item_id),
                    message="Item is not backed by official appearance/catalog sprite data.",
                )
            )

    def _validate_ground(
        self,
        report: RMEFidelityReport,
        position: Position,
        ground: int | None,
        catalog: RMEItemTypeCatalog,
    ) -> None:
        if ground is None:
            report.add_issue(
                RMEFidelityIssue(
                    code="MISSING_GROUND",
                    severity="WARN",
                    position=position,
                    item_id=None,
                    message="Tile has no ground; RME can display void/black around map edges if this is accidental.",
                )
            )
            return
        item = catalog.get(ground)
        exact_canary_ground = (
            item.is_ground and item.flag_source == "appearances.dat:Canary loadFromProtobuf"
        )
        if (not exact_canary_ground and (
            int(ground) in self.invalid_ground_ids
            or item.is_border
            or item.is_wall
            or item.is_table
            or item.is_carpet
        )) or item.pickupable:
            report.add_issue(
                RMEFidelityIssue(
                    code="INVALID_GROUND_ITEM",
                    severity="BLOCKER",
                    position=position,
                    item_id=int(ground),
                    message="Ground slot contains an item category that RME should keep as overlay/item, not base ground.",
                )
            )

    def _validate_stack_order(
        self,
        report: RMEFidelityReport,
        position: Position,
        stack: list[int],
        catalog: RMEItemTypeCatalog,
    ) -> None:
        if len(stack) <= 1:
            return
        ground, items = catalog.classify_stack(stack)
        expected = ([ground] if ground else []) + items
        if expected != stack:
            report.add_issue(
                RMEFidelityIssue(
                    code="STACK_ORDER_MISMATCH",
                    severity="WARN",
                    position=position,
                    item_id=None,
                    message=f"Stack order differs from RME item flag ordering: expected {expected}, got {stack}.",
                )
            )
        visual_stack = [
            RMEStackItem(
                item_id=item_id,
                appearance_id=item_id,
                role=_role_for_item(catalog, item_id, index),
                source_index=index,
            )
            for index, item_id in enumerate(stack)
        ]
        if [item.item_id for item in self.draw_order.sort_stack(visual_stack)] != stack:
            report.add_issue(
                RMEFidelityIssue(
                    code="DRAW_ORDER_MISMATCH",
                    severity="WARN",
                    position=position,
                    item_id=None,
                    message="Rendered stack would be reordered by the RME draw order contract.",
                )
            )


def _role_for_item(catalog: RMEItemTypeCatalog, item_id: int, index: int) -> str:
    item = catalog.get(item_id)
    if index == 0 or item.is_ground:
        return "GROUND"
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


def _load_sprite_backed_item_ids(root: Path) -> set[int]:
    item_catalog_path = root / "APPEARANCE_ITEM_CATALOG.json"
    render_catalog_path = root / "APPEARANCE_RENDER_CATALOG.json"
    if not item_catalog_path.exists() or not render_catalog_path.exists():
        return set()
    try:
        item_catalog = json.loads(item_catalog_path.read_text(encoding="utf-8"))
        render_catalog = json.loads(render_catalog_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return set()
    out: set[int] = set()
    for raw_id, item in item_catalog.items():
        if not str(raw_id).isdigit() or not isinstance(item, dict):
            continue
        candidates = [raw_id, item.get("appearance_id"), item.get("client_id"), item.get("lookid")]
        for brush in item.get("brushes", []) or []:
            if isinstance(brush, dict):
                candidates.append(brush.get("lookid"))
        if any(_has_sprite(render_catalog, candidate) for candidate in candidates):
            out.add(int(raw_id))
    return out


def _has_sprite(render_catalog: dict[str, object], candidate: object) -> bool:
    if candidate is None:
        return False
    render = render_catalog.get(str(candidate))
    return isinstance(render, dict) and bool(render.get("sprite_ids"))


def _load_invalid_ground_ids(root: Path) -> set[int]:
    candidates = [
        root / "exports" / "RME_MATERIAL_CLASSIFICATION.json",
        root / "exports" / "WG18H_RME_MATERIAL_CLASSIFICATION.json",
        root / "exports" / "WG18G_ITEM_CLASSIFICATION.json",
        root / "exports" / "WG18HD_GEOMETRY_ITEM_CLASSIFICATION.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        categories = data.get("categories") if isinstance(data, dict) else None
        invalid = categories.get("invalid_for_ground") if isinstance(categories, dict) else None
        if invalid:
            return {int(item_id) for item_id in invalid}
    return set()
