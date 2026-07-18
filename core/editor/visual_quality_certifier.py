from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.opentibia.assets.appearance_dat_flags import SpriteAnimationInfo, SpritePhaseTiming
from rme_rendering.ingame_render_mode import IngameRenderMode
from rme_rendering.sprites.sprite_animation_resolver import SpriteAnimationResolver
from rme_rendering.sprites.sprite_index_resolver import SpriteIndexResolver, SpriteSelectionContext
from rme_rendering.sprites.sprite_reference_loader import SpriteReference


@dataclass(frozen=True)
class VisualQualityGate:
    name: str
    passed: bool
    evidence: dict[str, Any]


@dataclass(frozen=True)
class VisualQualityCertification:
    status: str
    score: int
    gates: tuple[VisualQualityGate, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": "RME Full-Map Visual Quality Certification",
            "status": self.status,
            "score": self.score,
            "gates": [asdict(gate) for gate in self.gates],
        }


class VisualQualityCertifier:
    """Certifies renderer behavior without treating synthetic evidence as Canary parity."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def certify(self, *, canary_pixel_diff_evidence: str = "") -> VisualQualityCertification:
        rendered = self._json("exports/RME_RENDERED_CHUNK_QA_NECRO_REPORT.json")
        stack_qa = self._json("exports/RME_FULL_MAP_VISUAL_QA_NECRO_REPORT.json")
        item_safety = self._json("exports/GENERATED_OTBM_ITEM_SAFETY_CERTIFICATION.json")
        pixel_diff = self._pixel_diff(canary_pixel_diff_evidence)

        reference = SpriteReference(
            appearance_id=1,
            sprite_ids=list(range(100, 148)),
            frame_count=2,
            layers=2,
            patterns={"width": 3, "height": 2, "depth": 2},
        )
        resolver = SpriteIndexResolver()
        context = SpriteSelectionContext(
            animation_frame=1,
            layer=1,
            pattern_x=2,
            pattern_y=1,
            pattern_z=1,
        )
        selection = resolver.resolve(reference, context)
        expected_index = (((1 * 2 + 1) * 2 + 1) * 3 + 2) * 2 + 1

        animation = SpriteAnimationInfo(
            default_start_phase=0,
            synchronized=True,
            loop_type=0,
            phases=(SpritePhaseTiming(100, 100), SpritePhaseTiming(200, 200)),
        )
        animation_resolver = SpriteAnimationResolver()
        frame_0 = animation_resolver.resolve(animation, 50)
        frame_1 = animation_resolver.resolve(animation, 150)
        layer_0 = resolver.resolve(reference, SpriteSelectionContext(pattern_x=1, layer=0))
        layer_1 = resolver.resolve(reference, SpriteSelectionContext(pattern_x=1, layer=1))

        checked = int(rendered.get("checked_tiles", 0) or 0)
        rendered_tiles = int(rendered.get("rendered_tiles", 0) or 0)
        issue_counts = dict(rendered.get("issue_counts", {}) or {})
        full_map_pass = rendered.get("status") == "PASS" and checked > 0 and checked == rendered_tiles
        sprite_sources = tuple(self.root.glob("assets/appearances-*.dat"))
        catalog = self.root / "assets/catalog-content.json"
        official_pixels = full_map_pass and bool(sprite_sources) and catalog.is_file()
        draw_order = (
            stack_qa.get("status") == "PASS"
            and not dict(stack_qa.get("issue_counts", {}) or {})
            and item_safety.get("status") == "PASS"
        )
        floors = {
            int(chunk["bounds"][key])
            for chunk in rendered.get("chunk_reports", [])
            for key in ("min_z", "max_z")
            if isinstance(chunk.get("bounds"), dict) and key in chunk["bounds"]
        }
        ingame_audit = IngameRenderMode().audit()

        gates = (
            VisualQualityGate("official_pixels", official_pixels, {"appearances": [str(path) for path in sprite_sources], "catalog": str(catalog), "rendered_tiles": rendered_tiles}),
            VisualQualityGate("sprite_index", bool(selection and selection.sprite_index == expected_index), {"actual": selection.sprite_index if selection else None, "expected": expected_index}),
            VisualQualityGate("animation_timing", frame_0.frame == 0 and frame_1.frame == 1, {"frame_at_50ms": frame_0.to_dict(), "frame_at_150ms": frame_1.to_dict()}),
            VisualQualityGate("patterns_layers", bool(layer_0 and layer_1 and layer_0.sprite_index != layer_1.sprite_index), {"layer_0": layer_0.to_dict() if layer_0 else None, "layer_1": layer_1.to_dict() if layer_1 else None}),
            VisualQualityGate("draw_order", draw_order, {"full_map_stack_qa": stack_qa.get("status"), "item_safety": item_safety.get("status")}),
            VisualQualityGate("multifloor_occlusion", len(floors) > 1, {"floors_scanned": sorted(floors)}),
            VisualQualityGate("light_elevation", all(name in ingame_audit.get("implemented", []) for name in ("elevation draw offset", "light/translucency post effects")), ingame_audit),
            VisualQualityGate("full_map_chunks", full_map_pass and int(rendered.get("chunk_count", 0) or 0) > 1, {"checked_tiles": checked, "rendered_tiles": rendered_tiles, "chunk_count": rendered.get("chunk_count")}),
            VisualQualityGate("zero_black_tiles", full_map_pass and not any(issue_counts.get(code, 0) for code in ("BLACK_RENDERED_TILE", "TRANSPARENT_RENDERED_TILE", "MISSING_STACK_SPRITE")), {"issue_counts": issue_counts}),
            VisualQualityGate("canary_pixel_diff", pixel_diff.get("status") == "PASS", pixel_diff),
        )
        score = sum(gate.passed for gate in gates)
        return VisualQualityCertification("CERTIFIED" if score == 10 else "INCOMPLETE", score, gates)

    def _json(self, relative_path: str) -> dict[str, Any]:
        path = self.root / relative_path
        if not path.is_file():
            return {}
        value = json.loads(path.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else {}

    def _pixel_diff(self, evidence: str) -> dict[str, Any]:
        if not evidence:
            return {"status": "MISSING", "evidence": ""}
        path = self.root / evidence
        value = self._json(evidence)
        return {
            "status": value.get("status", "INVALID"),
            "evidence": str(path),
            "average_delta": value.get("average_delta"),
            "size_match": value.get("size_match"),
        }
