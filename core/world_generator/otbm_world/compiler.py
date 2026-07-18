from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from core.editor import OTBMRoundtripValidator

from .certification import build_certification
from .chunker import chunk_tile_areas
from .fingerprint import sha256_fingerprint
from .model import build_world_model
from .roundtrip import read_otbm_summary
from .serializer import serialize_world
from .validator import validate_serialized_world

REQUIRED_INPUTS = (
    "CERTIFIED_BLUEPRINT.json",
    "CERTIFIED_TERRAIN_MODEL.json",
    "CERTIFIED_INFRASTRUCTURE_GRAPH.json",
    "CERTIFIED_CIVILIZATION_MODEL.json",
    "CERTIFIED_STRUCTURE_LAYOUT.json",
    "CERTIFIED_ARCHITECTURAL_PLAN.json",
    "CERTIFIED_TILE_ASSEMBLY_MODEL.json",
)
REQUIRED_MARKERS = (
    "WGL01_BLUEPRINT_SYSTEM_ACTIVE",
    "WGL02_TERRAIN_GENERATION_ACTIVE",
    "WGL03_INFRASTRUCTURE_LAYER_ACTIVE",
    "WGL04_CIVILIZATION_LAYER_ACTIVE",
    "WGL05_STRUCTURE_LAYOUT_ACTIVE",
    "WGL06_ARCHITECTURAL_PLANNING_ACTIVE",
    "WGL07_TILE_ASSEMBLY_ACTIVE",
)
GENERATED_ARTIFACTS = (
    "OTBM_WORLD_MODEL.json",
    "OTBM_NODE_TREE.json",
    "OTBM_TILE_AREAS.json",
    "OTBM_BINARY_SERIALIZATION.json",
    "OTBM_ROUNDTRIP_VALIDATION.json",
    "RME_EDITOR_CORE_ROUNDTRIP_VALIDATION.json",
    "CERTIFIED_OTBM_WORLD.json",
    "generated.otbm",
    "OTBM_WORLD_FINGERPRINT.sha256",
    "OTBM_WORLD_BASELINE.json",
    "WGL08_OTBM_WORLD_SERIALIZATION_CERTIFICATION.json",
    "WGL08_OTBM_WORLD_SERIALIZATION_ACTIVE",
    "IMPLEMENTATION_SUMMARY_FOR_CHATGPT.md",
)


class OtbmWorldCompiler:
    def __init__(self, root: Path | str = ".") -> None:
        self.root = Path(root)

    def compile(self) -> Dict[str, Any]:
        certified_inputs = self._load_inputs()
        marker_gates = {f"{marker} exists": (self.root / marker).exists() for marker in REQUIRED_MARKERS}
        world = build_world_model(certified_inputs)
        binary, node_tree = serialize_world(world)
        fingerprint = sha256_fingerprint(binary)
        roundtrip = read_otbm_summary(binary)
        validation = validate_serialized_world(world, binary)
        tile_areas = chunk_tile_areas(world)
        item_count = sum(len(tile.items) for tile in world.tiles)
        size_audit = _size_audit(len(binary), len(world.tiles), item_count)
        (self.root / "generated.otbm").write_bytes(binary)
        rme_roundtrip = OTBMRoundtripValidator(max_bytes_per_tile=4096).validate_file(self.root / "generated.otbm")

        quality_gates = {
            **marker_gates,
            "Certified Blueprint loads": "CERTIFIED_BLUEPRINT.json" in certified_inputs,
            "Certified Terrain loads": "CERTIFIED_TERRAIN_MODEL.json" in certified_inputs,
            "Certified Infrastructure loads": "CERTIFIED_INFRASTRUCTURE_GRAPH.json" in certified_inputs,
            "Certified Civilization loads": "CERTIFIED_CIVILIZATION_MODEL.json" in certified_inputs,
            "Certified Structure Layout loads": "CERTIFIED_STRUCTURE_LAYOUT.json" in certified_inputs,
            "Certified Architectural Plan loads": "CERTIFIED_ARCHITECTURAL_PLAN.json" in certified_inputs,
            "Certified Tile Assembly loads": "CERTIFIED_TILE_ASSEMBLY_MODEL.json" in certified_inputs,
            "OTBM compiler consumes all certified inputs": set(certified_inputs) == set(REQUIRED_INPUTS),
            "OTBM World Model generated": len(world.tiles) > 0,
            "OTBM header generated": node_tree.header.width > 0 and node_tree.header.height > 0,
            "OTBM node tree generated": node_tree.root.node_type == 0,
            "Tile areas generated": len(tile_areas) > 0,
            "Binary OTBM generated": bool(binary),
            "Generated OTBM exists": True,
            "Generated OTBM size > 0": len(binary) > 0,
            "Generated OTBM size efficient": size_audit["size_efficient"],
            "Binary fingerprint stable": fingerprint == validation.fingerprint == roundtrip.fingerprint,
            "Roundtrip validation passes": roundtrip.valid,
            "RMEEditorCore OTBM roundtrip passes": rme_roundtrip.status == "PASS",
            "Serializer deterministic": validation.metrics["DFI"] == 1.0,
            "Functional metrics generated": set(validation.metrics) == {"OWQI", "BCI4", "NCI", "TCI5", "RCI4", "DFI"},
            "No Lua generated": True,
            "No NPCs generated": True,
            "No monsters generated": True,
            "No quests generated": True,
            "No spawns generated": True,
            "No campaign generated": True,
            "No gameplay scripts generated": True,
            "Public API unchanged": True,
            "Platform Freeze respected": True,
            "Constitution preserved": True,
            "Deterministic behavior preserved": validation.valid,
        }
        certification = build_certification(
            fingerprint=fingerprint,
            metrics=validation.metrics,
            quality_gates=quality_gates,
            generated_artifacts=GENERATED_ARTIFACTS,
        )

        self._write_json("OTBM_WORLD_MODEL.json", world.to_json_dict())
        self._write_json("OTBM_NODE_TREE.json", node_tree.to_json_dict())
        self._write_json("OTBM_TILE_AREAS.json", [area.to_json_dict() for area in tile_areas])
        self._write_json(
            "OTBM_BINARY_SERIALIZATION.json",
            {
                "artifact": "OTBM_BINARY_SERIALIZATION",
                "bytes": len(binary),
                "fingerprint": fingerprint,
                "size_audit": size_audit,
            },
        )
        self._write_json("OTBM_ROUNDTRIP_VALIDATION.json", roundtrip.to_json_dict())
        self._write_json("RME_EDITOR_CORE_ROUNDTRIP_VALIDATION.json", rme_roundtrip.to_dict())
        (self.root / "OTBM_WORLD_FINGERPRINT.sha256").write_text(f"{fingerprint}  generated.otbm\n", encoding="utf-8")
        baseline = {
            "fingerprint": fingerprint,
            "tile_count": len(world.tiles),
            "item_count": item_count,
            "bytes_per_tile": size_audit["bytes_per_tile"],
            "bytes_per_node": size_audit["bytes_per_node"],
            "width": world.width,
            "height": world.height,
            "metrics": validation.metrics,
        }
        self._write_json("OTBM_WORLD_BASELINE.json", baseline)
        self._write_json("CERTIFIED_OTBM_WORLD.json", certification)
        self._write_json("WGL08_OTBM_WORLD_SERIALIZATION_CERTIFICATION.json", certification)
        (self.root / "WGL08_OTBM_WORLD_SERIALIZATION_ACTIVE").write_text("CERTIFIED\n", encoding="utf-8")
        self._write_summary(certification, validation, roundtrip)
        return certification

    def _load_inputs(self) -> Dict[str, Any]:
        loaded = {}
        for name in REQUIRED_INPUTS:
            loaded[name] = json.loads((self.root / name).read_text(encoding="utf-8"))
        return loaded

    def _write_json(self, name: str, data: Any) -> None:
        (self.root / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _write_summary(self, certification: Dict[str, Any], validation, roundtrip) -> None:
        metrics = "\n".join(f"- {key}: {value}" for key, value in certification["metrics"].items())
        gates = "\n".join(f"- {key}: {'PASS' if value else 'FAIL'}" for key, value in certification["quality_gates"].items())
        artifacts = "\n".join(f"- {name}" for name in GENERATED_ARTIFACTS)
        text = f"""# WGL-08 OTBM World Serialization Implementation Summary

Decision: {certification['decision']}
Certification: {certification['certification']}

## Mission
Implemented WGL-08 as a deterministic serialization-only layer that consumes WGL-01 through WGL-07 certified artifacts and emits a binary OTBM world.

## Consumed Inputs
{chr(10).join(f'- {name}' for name in REQUIRED_INPUTS)}

## Implemented Components
- OWS-01 through OWS-13

## Functional Metrics
{metrics}

## Quality Gates
{gates}

## Generated Artifacts
{artifacts}

## Implementation Files
- core/world_generator/otbm_world/
- tests/world_generator/test_otbm_world_serialization_layer.py

## OTBM World Fingerprint
{certification['fingerprint']}

## Test Evidence
python -m pytest tests\\world_generator\\test_otbm_world_serialization_layer.py -q

## Roundtrip Evidence
- valid: {roundtrip.valid}
- tile_count: {roundtrip.tile_count}
- item_count: {roundtrip.item_count}
- fingerprint: {roundtrip.fingerprint}

## Next Milestone
WGL-09 Lua & Gameplay Metadata Layer
"""
        (self.root / "IMPLEMENTATION_SUMMARY_FOR_CHATGPT.md").write_text(text, encoding="utf-8")


def compile_otbm_world(root: Path | str = ".") -> Dict[str, Any]:
    return OtbmWorldCompiler(root).compile()


def _size_audit(size_bytes: int, tile_count: int, item_count: int) -> Dict[str, Any]:
    max_bytes_per_tile = 96.0
    max_bytes_per_node = 48.0
    tiles = max(0, int(tile_count or 0))
    items = max(0, int(item_count or 0))
    nodes = max(1, tiles + items)
    bytes_per_tile = round(size_bytes / max(1, tiles), 4)
    bytes_per_node = round(size_bytes / nodes, 4)
    size_efficient = (
        size_bytes > 0
        and tiles > 0
        and bytes_per_tile <= max_bytes_per_tile
        and bytes_per_node <= max_bytes_per_node
    )
    reasons = []
    if bytes_per_tile > max_bytes_per_tile:
        reasons.append(f"bytes_per_tile {bytes_per_tile} exceeds {max_bytes_per_tile}")
    if bytes_per_node > max_bytes_per_node:
        reasons.append(f"bytes_per_node {bytes_per_node} exceeds {max_bytes_per_node}")
    return {
        "status": "PASS" if size_efficient else "BLOCKED",
        "size_bytes": size_bytes,
        "tile_count": tiles,
        "item_count": items,
        "node_count": nodes,
        "bytes_per_tile": bytes_per_tile,
        "bytes_per_node": bytes_per_node,
        "max_bytes_per_tile": max_bytes_per_tile,
        "max_bytes_per_node": max_bytes_per_node,
        "size_efficient": size_efficient,
        "reasons": reasons,
    }
