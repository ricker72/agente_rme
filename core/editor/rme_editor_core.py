from __future__ import annotations

from pathlib import Path
from typing import Iterable

from core.editor.action_queue import ActionQueue
from core.editor.advanced_tools_p2p3 import AdvancedToolsP2P3
from core.editor.brush_postprocessor import BrushPostprocessor
from core.editor.editable_map import EditableMap, Position
from core.editor.gameplay_p1 import CreatureCatalog, GameplayP1System
from core.editor.item_type_flags import RMEItemTypeCatalog
from core.editor.material_catalog import RMEMaterialCatalog
from core.editor.otbm_roundtrip_validator import OTBMRoundtripValidator
from core.editor.rme_fidelity_gate import RMEFidelityGate
from core.editor.rme_source_gap_scanner import RMESourceGapScanner
from core.world_generator.rme_brush_engine import RMEBrushEngine
from core.world_generator.rme_materials_necro_v5 import classify_items, load_material_catalog


class RMEEditorCore:
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)
        self.item_catalog = RMEItemTypeCatalog.load(self.root)
        self.material_catalog = RMEMaterialCatalog.load(self.root)
        self.map = EditableMap(self.item_catalog)
        self.actions = ActionQueue(self.map)
        classification = classify_items(load_material_catalog(self.root))
        self.brush_engine = RMEBrushEngine.load(self.root, classification)
        self.postprocessor = BrushPostprocessor(self.map, self.brush_engine)
        self.roundtrip = OTBMRoundtripValidator()
        self.gameplay = GameplayP1System(self.map, CreatureCatalog.load(self.root))
        self.advanced = AdvancedToolsP2P3(self.map, self.actions, self.gameplay)
        self.fidelity_gate = RMEFidelityGate(self.root)
        self.source_gap_scanner = RMESourceGapScanner(self.root)

    def paint_stack(self, position: Position, item_ids: Iterable[int], label: str = "Paint Stack") -> dict[str, object]:
        action = self.actions.make_stack_action(label, position, item_ids)
        self.actions.commit(action)
        postprocess = self.postprocessor.run([position])
        return {
            "action": label,
            "position": position,
            "postprocess": postprocess.to_dict(),
            "tile": self.map.ensure_tile(position).stack_ids(),
        }

    def validate_otbm(self, path: str | Path) -> dict[str, object]:
        return self.roundtrip.validate_file(path).to_dict()

    def validate_visual_fidelity(self) -> dict[str, object]:
        return self.fidelity_gate.validate(self.map).to_dict()

    def scan_official_source_gaps(self) -> dict[str, object]:
        return self.source_gap_scanner.scan()

    def audit(self) -> dict[str, object]:
        return {
            "rme_editor_core_ready": True,
            "item_catalog": self.item_catalog.audit(),
            "material_catalog": self.material_catalog.audit(),
            "editable_map": self.map.audit(),
            "action_queue": self.actions.audit(),
            "brush_postprocessor": self.postprocessor.audit(),
            "gameplay_p1": self.gameplay.audit(),
            "advanced_tools_p2p3": self.advanced.audit(),
            "rme_fidelity_gate": self.fidelity_gate.validate(self.map).to_dict(),
            "official_source_gap_scan": self.source_gap_scanner.scan(),
        }
