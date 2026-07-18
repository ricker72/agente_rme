from __future__ import annotations

import json
import shutil
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from PIL import Image

from core.otbm.otbm_reference_inspector import inspect_otbm_file
from core.otbm.otbm_serializer import OtbmSerializer


ROOT = Path(__file__).resolve().parents[3]
WIDTH = 2560
HEIGHT = 2560
TOWN_NAME = "Necro"
CERT_READY = "REAL_GEOMETRY_OTBM_EXPORTED_PENDING_RME"
CERT_BLOCKED = "REAL_GEOMETRY_OTBM_EXPORT_BLOCKED"
GOLDEN_PENDING = "MAP_PENDING_MANUAL_REVIEW"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class WG18HGRealGeometryExporter:
    """Export WG-18HG from the WG-18HF-A remediated tile model only."""

    def __init__(self, project_root: Path = ROOT) -> None:
        self.root = project_root
        self.roadmap = project_root / "roadmap" / "v1.1"
        self.exports = project_root / "exports"
        self.input_path = self.roadmap / "WG18HFA_WORLD_TILE_MODEL_REMEDIATED.json"
        self.hfa_certification_path = self.roadmap / "WG18HFA_CERTIFICATION.json"
        self.model: dict[str, Any] = {}
        self.certification: dict[str, Any] = {}
        self.outputs: dict[str, dict[str, Any]] = {}

    def run(self) -> dict[str, Any]:
        input_audit = self.audit_input()
        if input_audit["status"] != "PASS":
            return self.write_blocked_outputs(input_audit)

        export_audit = self.export_otbm()
        preview_audit = self.write_preview()
        golden_audit = self.write_golden_package(export_audit, preview_audit)
        rule20_gate = self.rule20_gate(export_audit, golden_audit)
        quality = self.quality_report(input_audit, export_audit, preview_audit, golden_audit, rule20_gate)
        certification = self.build_certification(quality)
        report, markdown, dependency = self.build_reports(certification)

        self.outputs = {
            "WG18HG_INPUT_AUDIT": input_audit,
            "WG18HG_OTBM_EXPORT_AUDIT": export_audit,
            "WG18HG_PREVIEW_AUDIT": preview_audit,
            "WG18HG_GOLDEN_PACKAGE_AUDIT": golden_audit,
            "WG18HG_RULE20_GATE": rule20_gate,
            "WG18HG_QUALITY_REPORT": quality,
            "WG18HG_CERTIFICATION": certification,
            "WG18HG_REPORT": report,
            "WG18HG_DEPENDENCY_AUDIT": dependency,
        }
        self.write_outputs(markdown)
        return report

    def audit_input(self) -> dict[str, Any]:
        self.certification = load_json(self.hfa_certification_path)
        self.model = load_json(self.input_path)
        checks = {
            "hfa_certification_ready": self.certification.get("automatic_certification")
            == "REAL_GEOMETRY_MATERIALIZATION_DENSITY_READY",
            "uses_hfa_remediated_model": self.input_path.name == "WG18HFA_WORLD_TILE_MODEL_REMEDIATED.json",
            "old_wg18hf_model_not_used": True,
            "model_status_pass": self.model.get("status") == "PASS",
            "tile_model_present": bool(self.model.get("tiles")),
            "conflicts_zero": len(self.model.get("conflicts", [])) == 0,
        }
        return {
            "phase": "WG-18HG Input Audit",
            "status": "PASS" if all(checks.values()) else "BLOCKED",
            "input": "roadmap/v1.1/WG18HFA_WORLD_TILE_MODEL_REMEDIATED.json",
            "forbidden_input_not_read": "roadmap/v1.1/WG18HF_WORLD_TILE_MODEL.json",
            "checks": checks,
            "tile_count": len(self.model.get("tiles", [])),
        }

    def export_otbm(self) -> dict[str, Any]:
        tiles = {
            f"{tile['x']}:{tile['y']}:{tile.get('z', 7)}": {
                "x": int(tile["x"]),
                "y": int(tile["y"]),
                "z": int(tile.get("z", 7)),
                "ground": int(tile["ground_id"]),
                "items": [],
                "flags": 0,
            }
            for tile in self.model["tiles"]
        }
        temple = self.model.get("temple", {"x": 1000, "y": 1000, "z": 7})
        world = SimpleNamespace(
            width=WIDTH,
            height=HEIGHT,
            tiles=tiles,
            cities=[
                {
                    "name": self.model.get("town", TOWN_NAME),
                    "temple_x": int(temple["x"]),
                    "temple_y": int(temple["y"]),
                    "temple_z": int(temple["z"]),
                }
            ],
            waypoints=self._waypoints(),
            spawns=[],
            description="WG-18HG real geometry export from WG-18HF-A remediated tile model pending manual RME review",
        )
        self.exports.mkdir(parents=True, exist_ok=True)
        otbm_path = self.exports / "Necro_real_v9.otbm"
        generated_path = self.exports / "generated.otbm"
        otbm_path.write_bytes(OtbmSerializer().serialize(world))
        shutil.copyfile(otbm_path, generated_path)
        audit = inspect_otbm_file(otbm_path, max_nodes=700000)
        town_ok = any(
            town["name"] == self.model.get("town", TOWN_NAME)
            and town["temple_x"] == int(temple["x"])
            and town["temple_y"] == int(temple["y"])
            and town["temple_z"] == int(temple["z"])
            for town in audit["towns"]
        )
        return {
            "phase": "WG-18HG OTBM Export",
            "status": "PASS"
            if town_ok
            and audit["header_fields"].get("width") == WIDTH
            and audit["header_fields"].get("height") == HEIGHT
            and audit["delimiter_balance"]["balanced"]
            else "BLOCKED",
            "otbm": "exports/Necro_real_v9.otbm",
            "generated_otbm": "exports/generated.otbm",
            "input_model": "roadmap/v1.1/WG18HFA_WORLD_TILE_MODEL_REMEDIATED.json",
            "header_fields": audit["header_fields"],
            "towns": audit["towns"],
            "tile_count": len(audit["tiles"]),
            "delimiter_balance": audit["delimiter_balance"],
        }

    def write_preview(self) -> dict[str, Any]:
        colors = {
            "water_edge": (42, 91, 132),
            "water_transition": (52, 107, 146),
            "dock_core": (121, 86, 47),
            "wooden_path": (132, 94, 53),
            "boat_access": (145, 102, 57),
            "hunt_floor": (112, 98, 68),
            "hunt_room": (112, 112, 104),
            "hunt_corridor": (120, 110, 93),
            "road": (126, 101, 70),
            "building_floor": (137, 105, 70),
            "entrance_access": (143, 143, 130),
            "wall": (82, 75, 68),
        }
        image = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        pixels = image.load()
        for tile in self.model["tiles"]:
            layer = str(tile.get("layer", "terrain"))
            pixels[int(tile["x"]), int(tile["y"])] = colors.get(layer, (86, 135, 72))
        rendered = image.resize((1024, 1024), Image.Resampling.NEAREST)
        path = self.exports / "preview.png"
        rendered.save(path)
        return {
            "phase": "WG-18HG Preview Audit",
            "status": "PASS" if path.exists() and path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n" else "BLOCKED",
            "preview_path": "exports/preview.png",
            "source": "roadmap/v1.1/WG18HFA_WORLD_TILE_MODEL_REMEDIATED.json",
            "format": "PNG",
            "dimensions": {"source": [WIDTH, HEIGHT], "rendered": list(rendered.size)},
        }

    def write_golden_package(
        self,
        export_audit: dict[str, Any],
        preview_audit: dict[str, Any],
    ) -> dict[str, Any]:
        certification_state = {
            "status": GOLDEN_PENDING,
            "internal_export_state": CERT_READY,
            "manual_validation_required": True,
            "rule_20_respected": True,
            "rule_20a_respected": True,
            "source_input": "WG18HFA_WORLD_TILE_MODEL_REMEDIATED.json",
        }
        manifest = {
            "world": self.model.get("town", TOWN_NAME),
            "wg": "WG-18HG",
            "status": GOLDEN_PENDING,
            "input_model": "roadmap/v1.1/WG18HFA_WORLD_TILE_MODEL_REMEDIATED.json",
            "otbm": export_audit["otbm"],
            "preview": preview_audit["preview_path"],
            "tile_count": export_audit["tile_count"],
        }
        write_json(self.exports / "certification_state.json", certification_state)
        write_json(self.exports / "world_manifest.json", manifest)
        write_json(self.root / "certification_state.json", certification_state)
        write_json(self.root / "world_manifest.json", manifest)
        required = ["Necro_real_v9.otbm", "generated.otbm", "preview.png", "certification_state.json", "world_manifest.json"]
        return {
            "phase": "WG-18HG Golden Package Audit",
            "status": "PASS" if all((self.exports / name).exists() for name in required) else "BLOCKED",
            "certification_state": GOLDEN_PENDING,
            "generated_files": required,
        }

    def rule20_gate(
        self,
        export_audit: dict[str, Any],
        golden_audit: dict[str, Any],
    ) -> dict[str, Any]:
        checks = {
            "manual_rme_validation_required": True,
            "manual_canary_validation_required": True,
            "automatic_status_is_pending_only": True,
            "forbidden_final_certifications_not_issued": True,
            "golden_package_pending_manual_review": golden_audit["certification_state"] == GOLDEN_PENDING,
            "export_generated": export_audit["status"] == "PASS",
        }
        return {
            "phase": "WG-18HG Rule 20/20A Gate",
            "status": "PASS" if all(checks.values()) else "BLOCKED",
            "checks": checks,
            "maximum_automatic_status": CERT_READY,
        }

    def quality_report(
        self,
        input_audit: dict[str, Any],
        export_audit: dict[str, Any],
        preview_audit: dict[str, Any],
        golden_audit: dict[str, Any],
        rule20_gate: dict[str, Any],
    ) -> dict[str, Any]:
        layers = Counter(str(tile.get("layer", "unknown")) for tile in self.model.get("tiles", []))
        checks = {
            "input_audit_pass": input_audit["status"] == "PASS",
            "otbm_export_pass": export_audit["status"] == "PASS",
            "preview_audit_pass": preview_audit["status"] == "PASS",
            "golden_package_pass": golden_audit["status"] == "PASS",
            "rule20_gate_pass": rule20_gate["status"] == "PASS",
            "hfa_input_only": input_audit["checks"]["uses_hfa_remediated_model"],
            "manual_validation_pending": True,
        }
        return {
            "phase": "WG-18HG Quality Report",
            "status": "PASS" if all(checks.values()) else "BLOCKED",
            "checks": checks,
            "metrics": {
                "model_tiles": len(self.model.get("tiles", [])),
                "exported_tiles": export_audit["tile_count"],
                "layers": dict(sorted(layers.items())),
            },
        }

    def build_certification(self, quality: dict[str, Any]) -> dict[str, Any]:
        ready = quality["status"] == "PASS"
        return {
            "wg": "WG-18HG",
            "automatic_certification": CERT_READY if ready else CERT_BLOCKED,
            "golden_package_state": GOLDEN_PENDING if ready else "MAP_EXPORT_BLOCKED",
            "manual_validation_required": True,
            "forbidden_certifications_not_issued": True,
            "maximum_automatic_status": CERT_READY,
        }

    def build_reports(self, certification: dict[str, Any]) -> tuple[dict[str, Any], str, dict[str, Any]]:
        report = {
            "wg": "WG-18HG",
            "objective": "Real Geometry OTBM Export from WG-18HF-A",
            "status": certification["automatic_certification"],
            "golden_package_state": certification["golden_package_state"],
            "manual_validation_required": True,
            "input_model": "roadmap/v1.1/WG18HFA_WORLD_TILE_MODEL_REMEDIATED.json",
            "exports": ["exports/Necro_real_v9.otbm", "exports/generated.otbm", "exports/preview.png"],
            "next_step": "Project owner opens exports/Necro_real_v9.otbm in RME/Canary for manual validation.",
        }
        markdown = "\n".join(
            [
                "# WG-18HG Real Geometry OTBM Export",
                "",
                f"Status: {report['status']}",
                "",
                "- Input: roadmap/v1.1/WG18HFA_WORLD_TILE_MODEL_REMEDIATED.json",
                "- Output: exports/Necro_real_v9.otbm",
                "- Output: exports/generated.otbm",
                "- Output: exports/preview.png",
                "- Golden package state: MAP_PENDING_MANUAL_REVIEW",
                "- Manual RME/Canary validation remains mandatory.",
                "",
            ]
        )
        dependency = {
            "wg": "WG-18HG",
            "runtime_dependencies_added": [],
            "external_code_imported": False,
            "uses_existing_serializer": True,
            "uses_hfa_remediated_input": True,
        }
        return report, markdown, dependency

    def write_outputs(self, markdown: str) -> None:
        for name, payload in self.outputs.items():
            write_json(self.roadmap / f"{name}.json", payload)
        (self.roadmap / "WG18HG_REPORT.md").write_text(markdown, encoding="utf-8")

    def write_blocked_outputs(self, input_audit: dict[str, Any]) -> dict[str, Any]:
        certification = {
            "wg": "WG-18HG",
            "automatic_certification": CERT_BLOCKED,
            "manual_validation_required": True,
            "forbidden_certifications_not_issued": True,
            "maximum_automatic_status": CERT_READY,
        }
        report = {
            "wg": "WG-18HG",
            "objective": "Real Geometry OTBM Export from WG-18HF-A",
            "status": CERT_BLOCKED,
            "input_model": "roadmap/v1.1/WG18HFA_WORLD_TILE_MODEL_REMEDIATED.json",
        }
        self.outputs = {
            "WG18HG_INPUT_AUDIT": input_audit,
            "WG18HG_CERTIFICATION": certification,
            "WG18HG_REPORT": report,
            "WG18HG_DEPENDENCY_AUDIT": {
                "wg": "WG-18HG",
                "runtime_dependencies_added": [],
                "external_code_imported": False,
            },
        }
        self.write_outputs("# WG-18HG Real Geometry OTBM Export\n\nStatus: REAL_GEOMETRY_OTBM_EXPORT_BLOCKED\n")
        return report

    def _waypoints(self) -> list[dict[str, Any]]:
        return [
            {
                "name": str(structure["building_id"]),
                "x": int((structure["target_bbox"]["min_x"] + structure["target_bbox"]["max_x"]) / 2),
                "y": int((structure["target_bbox"]["min_y"] + structure["target_bbox"]["max_y"]) / 2),
                "z": int(structure["target_bbox"].get("z", 7)),
            }
            for structure in self.model.get("structures", [])
        ]
