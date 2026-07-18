from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


AREA_GATES: dict[str, tuple[str, ...]] = {
    "otbm_reading": (
        "header_and_versions", "all_node_types", "tile_and_house_tiles", "inline_and_child_items",
        "all_item_attributes", "nested_containers", "towns_waypoints_spawns_zones", "unknown_data_preserved",
        "full_file_not_truncated", "world_otbm_reference_profile",
    ),
    "item_safety": (
        "exact_itemtype_flags", "official_appearance_binding", "sprite_backed_only", "valid_ground_slot",
        "typed_attributes", "complex_items", "draw_order", "material_role_constraints",
        "full_map_scan", "zero_blockers",
    ),
    "rme_brushes": (
        "ground", "autoborder", "optional_border", "wall", "doodad", "table_carpet",
        "door_wall_decoration", "multitile_composites", "erase_postprocess", "canary_parity_fixtures",
    ),
    "semantic_planning": (
        "prompt_contract", "reference_style_profile", "layered_color_masks", "biome_coherence",
        "road_graph", "structure_program", "multifloor_plan", "gameplay_intent", "critic", "repair_loop",
    ),
    "original_geometry": (
        "nonrectangular_landmass", "terrain_transitions", "connected_roads", "functional_buildings",
        "mountain_relief", "nature_distribution", "decoration_distribution", "vertical_connectors",
        "similarity_guard", "novelty_certified",
    ),
    "transactional_editing": (
        "batch_actions", "atomic_rollback", "undo_redo", "selection_modes", "dirty_regions",
        "complex_item_edits", "brush_postprocess_action", "repair_action", "bounded_history", "mixed_action_stress",
    ),
    "otbm_export": (
        "canary_header", "compact_tile_areas", "all_attributes", "nested_nodes", "house_tiles",
        "sidecars", "deterministic_binary", "lossless_roundtrip", "size_parity", "opens_in_canary",
    ),
    "visual_quality": (
        "official_pixels", "sprite_index", "animation_timing", "patterns_layers", "draw_order",
        "multifloor_occlusion", "light_elevation", "full_map_chunks", "zero_black_tiles", "canary_pixel_diff",
    ),
    "playability": (
        "walkability", "city_hunt_reachability", "return_routes", "stairs_ramps", "safe_danger_zones",
        "spawn_validity", "kite_routes", "house_function", "progression_balance", "runtime_playtest",
    ),
}


@dataclass(frozen=True)
class GateResult:
    gate: str
    passed: bool
    evidence: str


@dataclass(frozen=True)
class AreaResult:
    area: str
    score: int
    status: str
    gates: tuple[GateResult, ...]


@dataclass(frozen=True)
class RME10Report:
    status: str
    overall_score: float
    areas: tuple[AreaResult, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": "RME Agent 10/10 Certification",
            "status": self.status,
            "overall_score": self.overall_score,
            "rule": "An area is 10/10 only when all ten evidence gates pass.",
            "areas": [
                {
                    "area": area.area,
                    "score": area.score,
                    "status": area.status,
                    "gates": [gate.__dict__ for gate in area.gates],
                }
                for area in self.areas
            ],
        }


class RME10Certification:
    def certify(self, evidence: Mapping[str, Mapping[str, Any]]) -> RME10Report:
        areas: list[AreaResult] = []
        for area, gate_names in AREA_GATES.items():
            supplied = evidence.get(area, {})
            gates = tuple(self._gate(name, supplied.get(name)) for name in gate_names)
            score = sum(gate.passed for gate in gates)
            areas.append(AreaResult(area, score, "CERTIFIED" if score == 10 else "INCOMPLETE", gates))
        overall = round(sum(area.score for area in areas) / len(areas), 2)
        return RME10Report(
            "CERTIFIED_10" if all(area.score == 10 for area in areas) else "INCOMPLETE",
            overall,
            tuple(areas),
        )

    def write(self, evidence: Mapping[str, Mapping[str, Any]], path: str | Path) -> RME10Report:
        report = self.certify(evidence)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return report

    @staticmethod
    def _gate(name: str, raw: Any) -> GateResult:
        if isinstance(raw, Mapping):
            passed = raw.get("status") in {"PASS", "CERTIFIED", True} and not raw.get("truncated", False)
            evidence = str(raw.get("evidence") or raw.get("path") or "")
        else:
            passed = raw is True
            evidence = "explicit boolean evidence" if passed else ""
        return GateResult(name, bool(passed and evidence), evidence)
