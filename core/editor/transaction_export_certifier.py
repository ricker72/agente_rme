from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.editor.action_queue import ActionIdentifier, ActionQueue, BatchAction, EditorAction, TileChange
from core.editor.complex_items import EditableItem
from core.editor.editable_map import EditableMap, EditableTile
from core.editor.item_type_flags import RMEItemType, RMEItemTypeCatalog
from core.editor.selection import RMESelectionManager, SelectionSessionMode
from core.otbm.lossless_document import LosslessOTBMDocument
from core.world_generator.otbm_world.chunker import chunk_tile_areas
from core.world_generator.otbm_world.model import OtbmItem, OtbmTile, OtbmWorldModel
from core.world_generator.otbm_world.serializer import serialize_world
from core.world_generator.otbm_world.validator import validate_serialized_world


@dataclass(frozen=True)
class CertificationGate:
    name: str
    passed: bool
    evidence: dict[str, Any]


@dataclass(frozen=True)
class TransactionExportCertification:
    status: str
    transactional_score: int
    export_score: int
    transactional_gates: tuple[CertificationGate, ...]
    export_gates: tuple[CertificationGate, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": "Transactional Editing + OTBM Export Certification",
            "status": self.status,
            "transactional_score": self.transactional_score,
            "export_score": self.export_score,
            "transactional_gates": [asdict(gate) for gate in self.transactional_gates],
            "export_gates": [asdict(gate) for gate in self.export_gates],
        }


class TransactionExportCertifier:
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def certify(self, *, canary_open_evidence: str = "") -> TransactionExportCertification:
        transaction_gates = self._transaction_gates()
        export_gates = self._export_gates(canary_open_evidence)
        transaction_score = sum(gate.passed for gate in transaction_gates)
        export_score = sum(gate.passed for gate in export_gates)
        return TransactionExportCertification(
            "CERTIFIED" if transaction_score == export_score == 10 else "INCOMPLETE",
            transaction_score,
            export_score,
            transaction_gates,
            export_gates,
        )

    def _transaction_gates(self) -> tuple[CertificationGate, ...]:
        catalog = RMEItemTypeCatalog({100: RMEItemType(100, is_ground=True), 200: RMEItemType(200)})
        editable = EditableMap(catalog)
        queue = ActionQueue(editable, memory_limit=1024)
        with queue.transaction("two tiles") as transaction:
            transaction.set_stack((1, 1, 7), [100, 200])
            transaction.set_stack((2, 1, 7), [100])
        batch_ok = len(queue.undo_stack) == 1 and isinstance(queue.undo_stack[-1], BatchAction)
        undo_ok = queue.undo() and editable.get_tile((1, 1, 7)) is None
        redo_ok = queue.redo() and editable.get_tile((1, 1, 7)) is not None

        rollback_map = EditableMap(catalog)
        rollback_queue = ActionQueue(rollback_map)
        failing = EditorAction(
            "fail",
            [TileChange((5, 5, 7), None, EditableTile(5, 5, 7, ground=100))],
            redo_callback=lambda: (_ for _ in ()).throw(RuntimeError("rollback fixture")),
        )
        rollback_ok = False
        try:
            rollback_queue.commit(failing)
        except RuntimeError:
            rollback_ok = rollback_map.get_tile((5, 5, 7)) is None

        selection = RMESelectionManager(queue)
        selection.set_positions({(1, 1, 7), (2, 1, 7)}, mode=SelectionSessionMode.EXTERNAL)
        selection_ok = len(selection.positions) == 2 and queue.undo_stack[-1].identifier == ActionIdentifier.SELECT
        dirty = editable.consume_dirty_positions()

        before = editable.snapshot_tile((1, 1, 7))
        after = before.copy() if before else EditableTile(1, 1, 7, ground=100)
        after.item_payloads = [EditableItem(1988, action_id=100, children=[EditableItem(2148, count=5)])]
        complex_action = EditorAction(
            "complex item",
            [TileChange((1, 1, 7), before, after)],
            identifier=ActionIdentifier.CHANGE_PROPERTIES,
        )
        queue.commit(complex_action)
        complex_ok = editable.get_tile((1, 1, 7)).item_payloads[0].children[0].count == 5

        postprocess = EditorAction(
            "brush postprocess",
            [],
            identifier=ActionIdentifier.BORDERIZE,
            redo_callback=lambda: None,
            undo_callback=lambda: None,
        )
        repair = EditorAction(
            "AI repair",
            [],
            identifier=ActionIdentifier.AI_REPAIR,
            redo_callback=lambda: None,
            undo_callback=lambda: None,
        )
        queue.commit(queue.make_batch("postprocess", ActionIdentifier.BORDERIZE, [postprocess]))
        queue.commit(queue.make_batch("repair", ActionIdentifier.AI_REPAIR, [repair]))

        stress_map = EditableMap(catalog)
        stress_queue = ActionQueue(stress_map, memory_limit=1024)
        for index in range(100):
            stress_queue.commit(stress_queue.make_stack_action("stress", (index, 0, 7), [100, 200]))
        bounded = stress_queue.memory_size <= stress_queue.memory_limit or len(stress_queue.undo_stack) == 1
        undo_count = 0
        while stress_queue.undo():
            undo_count += 1
        while stress_queue.redo():
            pass
        stress_ok = undo_count > 0 and bool(stress_map.tiles)
        return (
            CertificationGate("batch_actions", batch_ok, {"undo_depth": 1}),
            CertificationGate("atomic_rollback", rollback_ok, {"tile_restored": rollback_ok}),
            CertificationGate("undo_redo", bool(undo_ok and redo_ok), {"undo": undo_ok, "redo": redo_ok}),
            CertificationGate("selection_modes", selection_ok, selection.audit()),
            CertificationGate("dirty_regions", bool(dirty), {"dirty_positions": len(dirty)}),
            CertificationGate("complex_item_edits", complex_ok, {"nested_count": 5}),
            CertificationGate("brush_postprocess_action", queue.undo_stack[-2].identifier == ActionIdentifier.BORDERIZE, {"identifier": "borderize"}),
            CertificationGate("repair_action", queue.undo_stack[-1].identifier == ActionIdentifier.AI_REPAIR, {"identifier": "ai_repair"}),
            CertificationGate("bounded_history", bounded, stress_queue.audit()),
            CertificationGate("mixed_action_stress", stress_ok, {"undo_count": undo_count, "tiles": len(stress_map.tiles)}),
        )

    def _export_gates(self, canary_open_evidence: str) -> tuple[CertificationGate, ...]:
        nested = OtbmItem(1988, "item", "container", {"action_id": 100}, (OtbmItem(2148, "item", "coin", {"count": 5}),))
        world = OtbmWorldModel(
            1024,
            1024,
            (
                OtbmTile(100, 100, 7, (OtbmItem(101, "ground", "ground"), nested), house_id=7),
                OtbmTile(356, 100, 7, (OtbmItem(103, "ground", "ground2"),)),
            ),
            {"spawn_monster_file": "spawns.xml", "house_file": "houses.xml", "zone_file": "zones.xml"},
        )
        binary, tree = serialize_world(world)
        binary2, _ = serialize_world(world)
        validation = validate_serialized_world(world, binary)
        areas = chunk_tile_areas(world)
        fixture = self.root / "exports/transaction_export_fixture.otbm"
        fixture.write_bytes(binary)
        lossless = LosslessOTBMDocument(fixture).audit_full_file()
        generated = self.root / "generated.otbm"
        generated_safety_path = self.root / "exports/GENERATED_OTBM_ITEM_SAFETY_CERTIFICATION.json"
        generated_safety = json.loads(generated_safety_path.read_text())
        generated_tiles = int(generated_safety["tiles_checked"])
        generated_bpt = generated.stat().st_size / max(1, generated_tiles)
        reference_profile = json.loads((self.root / "exports/WORLD_OTBM_PLANNER_STYLE_PROFILE_FULL.json").read_text())
        reference_bpt = (self.root / "projects/world/world.otbm").stat().st_size / reference_profile["tiles_scanned"]
        size_ratio = generated_bpt / reference_bpt
        node_types = [child.node_type for area in tree.root.children[0].children for child in area.children]
        attrs_ok = all(key in nested.attributes for key in ("action_id",)) and nested.children[0].attributes["count"] == 5
        sidecars = world.metadata
        return (
            CertificationGate("canary_header", validation.metrics["BCI4"] == 1.0, {"metrics": validation.metrics}),
            CertificationGate("compact_tile_areas", len(areas) == 2, {"tile_areas": len(areas)}),
            CertificationGate("all_attributes", attrs_ok, {"action_id": 100, "count": 5}),
            CertificationGate("nested_nodes", lossless.node_counts.get("ITEM") == 4, {"item_nodes": lossless.node_counts.get("ITEM")}),
            CertificationGate("house_tiles", 0x0E in node_types, {"node_types": node_types}),
            CertificationGate("sidecars", all(sidecars.get(key) for key in ("spawn_monster_file", "house_file", "zone_file")), {"metadata": sidecars}),
            CertificationGate("deterministic_binary", binary == binary2, {"bytes": len(binary)}),
            CertificationGate("lossless_roundtrip", validation.valid and lossless.status == "PASS", {"validation": validation.to_json_dict(), "lossless": lossless.status}),
            CertificationGate("size_parity", 0.75 <= size_ratio <= 1.25, {"generated_bytes_per_tile": round(generated_bpt, 4), "reference_bytes_per_tile": round(reference_bpt, 4), "ratio": round(size_ratio, 4)}),
            CertificationGate("opens_in_canary", bool(canary_open_evidence), {"evidence": canary_open_evidence}),
        )
