"""Prompt-facing scanner for compact, non-copyable reference-map knowledge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.world_generator.reference_map_corpus import ReferenceMapCorpusAnalyzer


SCANNER_VERSION = 4


class ReferenceMapScanner:
    """Scan reference OTBMs into floor/material/brush guidance for the Planner."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def scan_all(self) -> dict[str, Any]:
        corpus = ReferenceMapCorpusAnalyzer(self.root).analyze()
        reports = [
            self.report_from_profile(profile)
            for profile in corpus["profiles"]
            if profile.get("status") == "PASS"
        ]
        return {
            "stage": "Reference Map Scanner",
            "status": "PASS" if reports and corpus.get("status") == "PASS" else "BLOCKED",
            "format": f"rme-reference-map-scanner-v{SCANNER_VERSION}",
            "policy": {
                "reads_reference_otbm": True,
                "loads_world_otbm_for_prompt_queries": False,
                "returns_source_coordinates": False,
                "returns_tile_stacks": False,
                "returns_exact_chunks": False,
            },
            "reports": reports,
        }

    @staticmethod
    def report_from_profile(profile: dict[str, Any]) -> dict[str, Any]:
        floor_reports = []
        for floor in profile["floor_profiles"]:
            floor_reports.append({
                "floor": floor["floor"],
                "tile_count": floor["tile_count"],
                "dimensions": {"width": floor["width"], "height": floor["height"]},
                "item_density": floor["item_density"],
                "ground_ids": ReferenceMapScanner._compact_materials(floor["ground_materials"]),
                "nature_ids": ReferenceMapScanner._compact_materials(floor["nature_materials"]),
                "border_ids": ReferenceMapScanner._compact_materials(floor["border_materials"]),
                "wall_ids": ReferenceMapScanner._compact_materials(floor["wall_materials"]),
                "doodad_ids": ReferenceMapScanner._compact_materials(floor["doodad_materials"]),
                "material_count": len(floor["material_usage"]),
                "materials": floor["material_usage"],
                "category_mix": floor["category_mix"],
                "minimap_colors": floor["minimap_color_profile"],
            })
        grounds = ReferenceMapScanner._merge_role(floor_reports, "ground_ids")
        nature = ReferenceMapScanner._merge_role(floor_reports, "nature_ids")
        borders = ReferenceMapScanner._merge_role(floor_reports, "border_ids")
        return {
            "scanner_version": SCANNER_VERSION,
            "map": profile["name"],
            "source": profile["source"],
            "town": profile["town"],
            "used_floors": [row["floor"] for row in floor_reports],
            "floor_count": len(floor_reports),
            "floors": floor_reports,
            "summary": {
                "tile_count": profile["tile_count"],
                "material_diversity": profile["material_diversity"],
                "ground_ids": grounds,
                "nature_ids": nature,
                "border_ids": borders,
                "dominant_brushes": profile["top_brushes"],
                "border_mix_count": len(profile["border_mixes"]),
                "minimap_colors": profile["minimap_color_profile"],
                "family_coverage": profile.get("family_coverage", []),
                "biome_family_mixes": profile.get("biome_family_mixes", []),
                "vertical_connectors": profile.get("vertical_connectors", []),
            },
            "border_mixes": profile["border_mixes"],
            "generation_rules": profile["generation_rules"],
            "guidance": ReferenceMapScanner._guidance(profile, grounds, nature, borders),
            "similarity_guard_required": True,
        }

    @staticmethod
    def compact_for_prompt(report: dict[str, Any], limit: int = 16) -> dict[str, Any]:
        """Keep prompt context useful without injecting the complete source inventory."""
        summary = report["summary"]
        return {
            "map": report["map"],
            "used_floors": report["used_floors"],
            "floor_count": report["floor_count"],
            "grounds": summary["ground_ids"][:limit],
            "nature": summary["nature_ids"][:limit],
            "borders": summary["border_ids"][:limit],
            "dominant_brushes": summary["dominant_brushes"][:limit],
            "family_coverage": summary.get("family_coverage", [])[:limit],
            "biome_family_mixes": summary.get("biome_family_mixes", [])[:limit],
            "vertical_connectors": summary.get("vertical_connectors", [])[:limit],
            "minimap_colors": {
                "coverage": summary["minimap_colors"]["coverage"],
                "distinct_colors": summary["minimap_colors"]["distinct_colors"],
                "colors": summary["minimap_colors"]["colors"][:limit],
            },
            "guidance": report["guidance"],
            "generation_rules": report["generation_rules"],
            "similarity_guard_required": True,
        }

    @staticmethod
    def _compact_materials(materials: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "item_id": row["item_id"],
                "count": row["count"],
                "brushes": row["brushes"],
                "categories": row["categories"],
            }
            for row in materials
        ]

    @staticmethod
    def _merge_role(floors: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
        merged: dict[int, dict[str, Any]] = {}
        for floor in floors:
            for row in floor[key]:
                target = merged.setdefault(row["item_id"], {**row, "count": 0, "floors": []})
                target["count"] += row["count"]
                target["floors"].append(floor["floor"])
        return sorted(merged.values(), key=lambda row: (-row["count"], row["item_id"]))

    @staticmethod
    def _guidance(
        profile: dict[str, Any],
        grounds: list[dict[str, Any]],
        nature: list[dict[str, Any]],
        borders: list[dict[str, Any]],
    ) -> list[str]:
        floors = profile["dimensions"]
        connector_count = len(profile.get("vertical_connectors", ()))
        family_count = len(profile.get("family_coverage", ()))
        return [
            f"Usa como referencia abstracta los pisos {floors['min_floor']} a {floors['max_floor']}.",
            f"Se detectaron {len(grounds)} ground IDs, {len(borders)} border IDs y {len(nature)} nature IDs.",
            f"Se certificaron {family_count} familias RME usadas y {connector_count} patrones de conectividad vertical.",
            "Resuelve materiales por brush oficial y contexto de vecinos; no reproduzcas coordenadas fuente.",
            "Para montanas y edificios, conserva soporte transitable alrededor de escaleras, rampas y ladders.",
            "Mezcla biomas mediante familias vecinas observadas; no uses parches rectangulares ni familias incompletas.",
            "Conserva proporciones y familias visuales, pero genera topologia y geometria nuevas.",
        ]


__all__ = ["ReferenceMapScanner", "SCANNER_VERSION"]
