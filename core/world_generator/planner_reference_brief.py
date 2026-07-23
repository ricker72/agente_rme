"""Certified, coordinate-free map grammar from world and reference OTBM scans."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any


class CertifiedReferenceBriefBuilder:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def build(self, objective: str, *, reference_limit: int = 3, town_limit: int = 3) -> dict[str, Any]:
        if not self.database_path.is_file():
            return {"status": "UNAVAILABLE", "reference_maps": [], "world_towns": []}
        tokens = _tokens(objective)
        with self._connect() as connection:
            references = self._rank_reference_maps(connection, tokens, reference_limit)
            towns = self._rank_towns(connection, tokens, town_limit)
            reference_profiles = [self._reference_profile(connection, row) for row in references]
            town_profiles = [self._town_profile(connection, row) for row in towns]
        payload = {
            "status": "CERTIFIED",
            "source": "pre-scanned world.otbm + reference OTBMs",
            "reference_maps": reference_profiles,
            "world_towns": town_profiles,
            "facts_are_read_only": True,
            "source_coordinates_included": False,
            "source_geometry_included": False,
            "learning_policy": "derive proportions and grammar; generate new topology",
            "constraints": [
                "Do not copy a footprint, route, room, coastline or source coordinate.",
                "Treat counts, ratios, transitions and brush usage as style evidence only.",
                "Use only material keys present in the certified material brief.",
            ],
        }
        payload["brief_hash"] = hashlib.sha256(
            json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return payload

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            f"file:{self.database_path.resolve().as_posix()}?mode=ro", uri=True, timeout=5.0
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        return connection

    @staticmethod
    def _rank_reference_maps(connection: sqlite3.Connection, tokens: set[str], limit: int) -> list[sqlite3.Row]:
        rows = connection.execute(
            "SELECT id,name,tile_count,min_floor,max_floor,profile_json "
            "FROM reference_maps ORDER BY name"
        ).fetchall()
        aliases = {
            "nature": {"nature", "forest", "vegetation", "vegetacion", "jungle", "swamp"},
            "river": {"river", "water", "sea", "coast", "rio", "agua"},
            "miniboats": {"boat", "boats", "ship", "dock", "barco", "muelle"},
            "towers": {"tower", "vertical", "multifloor", "stairs", "torre", "pisos"},
            "krailos": {"krailos", "dry", "ruin", "sand", "hunt", "roca"},
            "montana": {"mountain", "mountains", "cliff", "montana", "roca"},
            "firecave": {"fire", "cave", "lava", "volcanic", "cueva", "fuego"},
            "roshamuul_map": {"roshamuul", "dark", "mountain", "ruin", "hunt", "wall"},
            "pantano": {"swamp", "pantano", "water", "nature", "mud"},
            "nor": {"island", "isla", "sea", "coast", "nature"},
            "carlin town": {"carlin", "town", "city", "ciudad", "house", "depot"},
            "dawnport": {"dawnport", "town", "tutorial", "temple"},
            "nature town": {"nature", "town", "forest", "city", "ciudad"},
            "rathleton town": {"rathleton", "town", "city", "industrial"},
            "venore town": {"venore", "town", "swamp", "city", "wood"},
        }
        ranked = []
        for row in rows:
            name = _ascii(str(row["name"]))
            score = 20 * len(tokens & _tokens(name)) + 5 * len(tokens & aliases.get(name, set()))
            ranked.append((score, -int(row["tile_count"]), name, row))
        ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
        relevant = [item for item in ranked if item[0] > 0] or ranked
        return [item[3] for item in relevant[: max(1, min(5, int(limit)))]]

    @staticmethod
    def _rank_towns(connection: sqlite3.Connection, tokens: set[str], limit: int) -> list[sqlite3.Row]:
        rows = connection.execute(
            "SELECT town_id,town_name,report_json FROM world_town_scan_reports ORDER BY town_name"
        ).fetchall()
        ranked = []
        for row in rows:
            name_tokens = _tokens(str(row["town_name"]))
            report = json.loads(row["report_json"])
            searchable = _ascii(json.dumps(report.get("structure_counts", {}), sort_keys=True))
            score = 30 * len(tokens & name_tokens) + sum(token in searchable for token in tokens)
            if str(row["town_name"]).casefold() in {"venore", "roshamuul"}:
                score += 1
            ranked.append((score, str(row["town_name"]).casefold(), row))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        relevant = [item for item in ranked if item[0] > 1]
        if not relevant:
            relevant = [item for item in ranked if item[2]["town_name"].casefold() in {"venore", "roshamuul"}]
        return [item[2] for item in relevant[: max(1, min(4, int(limit)))]]

    @staticmethod
    def _reference_profile(connection: sqlite3.Connection, reference: sqlite3.Row) -> dict[str, Any]:
        reference_id = int(reference["id"])
        raw_profile = json.loads(reference["profile_json"]) if reference["profile_json"] else {}
        floors = [dict(row) for row in connection.execute(
            "SELECT floor,tile_count,item_density,ground_diversity FROM reference_floor_profiles "
            "WHERE reference_id=? ORDER BY tile_count DESC LIMIT 4",
            (reference_id,),
        )]
        for floor in floors:
            floor["top_materials"] = [
                {
                    "item_id": int(row["item_id"]), "usage_count": int(row["usage_count"]),
                    "per_tile": round(float(row["per_tile"]), 5),
                    "categories": json.loads(row["categories_json"]),
                    "brushes": json.loads(row["brushes_json"]),
                }
                for row in connection.execute(
                    "SELECT item_id,usage_count,per_tile,categories_json,brushes_json "
                    "FROM reference_floor_material_usage WHERE reference_id=? AND floor=? "
                    "ORDER BY usage_count DESC LIMIT 7",
                    (reference_id, int(floor["floor"])),
                )
            ]
        transitions = [dict(row) for row in connection.execute(
            "SELECT ground_a,ground_b,edge_count FROM reference_ground_transitions "
            "WHERE reference_id=? ORDER BY edge_count DESC LIMIT 10",
            (reference_id,),
        )]
        border_mixes = [dict(row) for row in connection.execute(
            "SELECT floor,ground_id,border_id,usage_count FROM reference_border_mixes "
            "WHERE reference_id=? ORDER BY usage_count DESC LIMIT 10",
            (reference_id,),
        )]
        brush_usage = [dict(row) for row in connection.execute(
            "SELECT kind,name,usage_count FROM reference_brush_usage WHERE reference_id=? "
            "ORDER BY usage_count DESC LIMIT 12",
            (reference_id,),
        )]
        return {
            "name": str(reference["name"]),
            "tile_count": int(reference["tile_count"]),
            "floor_range": [int(reference["min_floor"]), int(reference["max_floor"])],
            "floor_profiles": floors,
            "dominant_brushes": brush_usage,
            "ground_transitions": transitions,
            "ground_border_mixes": border_mixes,
            "family_coverage": raw_profile.get("family_coverage", [])[:20],
            "biome_family_mixes": raw_profile.get("biome_family_mixes", [])[:20],
            "vertical_connectors": raw_profile.get("vertical_connectors", [])[:20],
            "coordinates_included": False,
        }

    @staticmethod
    def _town_profile(connection: sqlite3.Connection, town: sqlite3.Row) -> dict[str, Any]:
        town_id = int(town["town_id"])
        report = json.loads(town["report_json"])
        material_floors = []
        floor_counts = []
        for key, floor in report.get("floors", {}).items():
            floor_counts.append((int(floor.get("tile_count", 0)), int(key)))
        for _, z in sorted(floor_counts, reverse=True)[:4]:
            materials = [
                {
                    "item_id": int(row["item_id"]), "usage_count": int(row["usage_count"]),
                    "per_tile": round(float(row["per_tile"]), 5),
                    "categories": json.loads(row["categories_json"]),
                    "brushes": json.loads(row["brushes_json"]),
                }
                for row in connection.execute(
                    "SELECT item_id,usage_count,per_tile,categories_json,brushes_json "
                    "FROM world_town_floor_material_usage WHERE town_id=? AND floor=? "
                    "ORDER BY usage_count DESC LIMIT 8",
                    (town_id, z),
                )
            ]
            material_floors.append({"z": z, "top_materials": materials})
        observations = [dict(row) for row in connection.execute(
            "SELECT floor,ROUND(AVG(water_ratio),5) water_ratio,"
            "ROUND(AVG(nature_ratio),5) nature_ratio,ROUND(AVG(edge_density),5) edge_density "
            "FROM town_floor_observations WHERE town_id=? GROUP BY floor ORDER BY floor",
            (town_id,),
        )]
        structures = [dict(row) for row in connection.execute(
            "SELECT kind,COUNT(*) count,ROUND(AVG(width),2) avg_width,"
            "ROUND(AVG(height),2) avg_height,ROUND(AVG(floors),2) avg_floors "
            "FROM town_structures WHERE town_id=? GROUP BY kind ORDER BY count DESC LIMIT 14",
            (town_id,),
        )]
        return {
            "town": str(town["town_name"]),
            "content_floors": report.get("content_floors", []),
            "structure_counts": report.get("structure_counts", {}),
            "floor_environment": observations,
            "structure_dimensions": structures,
            "floor_material_usage": material_floors,
            "coordinates_included": False,
        }


def _ascii(value: str) -> str:
    return unicodedata.normalize("NFKD", str(value).casefold()).encode("ascii", "ignore").decode("ascii")


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", _ascii(value)) if len(token) > 2}


__all__ = ["CertifiedReferenceBriefBuilder"]
