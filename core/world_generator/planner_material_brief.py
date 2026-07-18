"""Build compact, certified RME material context for semantic AI planning."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


_CORE_TERMS = {
    "sea", "grass", "swamp", "mud", "dirt", "stone", "mountain", "wood",
    "road", "floor", "wall", "roof", "tree", "plant", "jungle", "ruin",
}


class CertifiedMaterialBriefBuilder:
    """Select real brushes and reference statistics without exposing source geometry."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def build(self, objective: str, *, brush_limit: int = 40, town_limit: int = 3) -> dict[str, Any]:
        if not self.database_path.is_file():
            return self._unavailable()
        tokens = _tokens(objective)
        with self._connect() as connection:
            town_names = self._rank_towns(connection, tokens, town_limit)
            usage = self._reference_brush_usage(connection, town_names)
            brushes = self._select_brushes(connection, tokens, usage, brush_limit)
            entries = [self._brush_entry(connection, row) for row in brushes]
            entries = [entry for entry in entries if entry is not None]
            town_profiles = self._town_profiles(connection, town_names)
            catalog_version = self._catalog_version(connection)
        allowed_keys = [entry["key"] for entry in entries]
        digest_source = json.dumps(
            {"version": catalog_version, "keys": allowed_keys},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return {
            "status": "CERTIFIED",
            "source": "Canary/RME materials.db + Planner reference scans",
            "catalog_version": catalog_version,
            "catalog_hash": hashlib.sha256(digest_source).hexdigest(),
            "all_ids_certified": True,
            "placement_authority": "RME Brush Engine",
            "selection_policy": "AI selects allowed keys; engine resolves IDs, chance, neighbors and stack order",
            "allowed_material_keys": allowed_keys,
            "brushes": entries,
            "reference_profiles": town_profiles,
            "constraints": [
                "Never invent a brush, material, item or border ID.",
                "Never place border pieces directly; select a ground key and let AutoBorder resolve neighbors.",
                "Never place wall parts directly; select a wall key and let WallBrush resolve orientation, doors and windows.",
                "Use reference profiles as proportions and grammar only; never reproduce coordinates or footprints.",
                "GroundBrush commits ground and AutoBorder atomically, then invalidates every affected neighbor.",
                "WallBrush reorients the complete connected neighborhood after every structural gesture.",
                "Treat missing optional OTBM sidecars as recoverable diagnostics; never discard the loaded map.",
            ],
        }

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            f"file:{self.database_path.resolve().as_posix()}?mode=ro", uri=True, timeout=5.0
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only = ON")
        return connection

    @staticmethod
    def _rank_towns(connection: sqlite3.Connection, tokens: set[str], limit: int) -> list[str]:
        rows = connection.execute("SELECT town_name FROM world_town_scan_reports ORDER BY town_name").fetchall()
        ranked: list[tuple[int, str]] = []
        for row in rows:
            name = str(row["town_name"])
            name_tokens = _tokens(name)
            score = 20 * len(tokens & name_tokens)
            if name.casefold() in {"venore", "roshamuul", "krailos"}:
                score += 1
            ranked.append((score, name))
        ranked.sort(key=lambda item: (-item[0], item[1].casefold()))
        selected = [name for score, name in ranked if score > 0][:limit]
        if selected:
            return selected
        defaults = [name for _, name in ranked if name.casefold() in {"venore", "roshamuul"}]
        return defaults[:limit]

    @staticmethod
    def _reference_brush_usage(connection: sqlite3.Connection, towns: Iterable[str]) -> Counter[tuple[str, str]]:
        usage: Counter[tuple[str, str]] = Counter()
        for town in towns:
            rows = connection.execute(
                "SELECT w.usage_count, w.brushes_json FROM world_town_floor_material_usage w "
                "JOIN towns t ON t.town_id=w.town_id WHERE lower(t.name)=lower(?) "
                "ORDER BY w.usage_count DESC LIMIT 600",
                (town,),
            ).fetchall()
            for row in rows:
                try:
                    brushes = json.loads(row["brushes_json"] or "[]")
                except (TypeError, json.JSONDecodeError):
                    continue
                for brush in brushes:
                    name = str(brush.get("name", "")).strip()
                    kind = str(brush.get("kind", "")).strip().lower()
                    if name and kind:
                        usage[(kind, name.casefold())] += int(row["usage_count"] or 0)
        return usage

    @staticmethod
    def _select_brushes(
        connection: sqlite3.Connection,
        tokens: set[str],
        usage: Counter[tuple[str, str]],
        limit: int,
    ) -> list[sqlite3.Row]:
        rows = connection.execute(
            "SELECT id,name,type,look_id,z_order,source_file FROM rme_brushes "
            "WHERE type IN ('ground','wall','doodad','carpet','table') ORDER BY id"
        ).fetchall()
        ranked: list[tuple[float, int, sqlite3.Row]] = []
        for row in rows:
            name = str(row["name"])
            kind = str(row["type"]).lower()
            name_tokens = _tokens(name)
            score = 9.0 * len(tokens & name_tokens)
            score += 2.0 * len(_CORE_TERMS & name_tokens & (tokens | _CORE_TERMS))
            count = usage[(kind, name.casefold())]
            if count:
                score += min(18.0, 2.0 + (count.bit_length() * 1.25))
            if name.casefold() in {"sea", "grass", "mountain", "venore brick wall"}:
                score += 12.0
            if kind in {"ground", "wall"}:
                score += 1.0
            ranked.append((score, count, row))
        ranked.sort(key=lambda item: (-item[0], -item[1], str(item[2]["name"]).casefold()))
        selected: list[sqlite3.Row] = []
        kind_counts: Counter[str] = Counter()
        for _, _, row in ranked:
            kind = str(row["type"]).lower()
            kind_cap = {"ground": 16, "wall": 10, "doodad": 10, "carpet": 3, "table": 3}.get(kind, 4)
            if kind_counts[kind] >= kind_cap:
                continue
            selected.append(row)
            kind_counts[kind] += 1
            if len(selected) >= max(8, min(64, int(limit))):
                break
        return selected

    @staticmethod
    def _brush_entry(connection: sqlite3.Connection, row: sqlite3.Row) -> dict[str, Any] | None:
        brush_id = int(row["id"])
        kind = str(row["type"]).lower()
        name = str(row["name"])
        key = f"{kind}/{_key_fragment(name)}"
        items = [
            {"id": int(item["item_id"]), "chance": int(item["chance"] or 0)}
            for item in connection.execute(
                "SELECT item_id,chance FROM rme_brush_items WHERE brush_id=? ORDER BY sort_order LIMIT 24",
                (brush_id,),
            )
        ]
        entry: dict[str, Any] = {
            "key": key,
            "name": name,
            "type": kind,
            "look_id": int(row["look_id"] or 0),
            "z_order": int(row["z_order"] or 0),
            "items": items,
        }
        if kind == "ground":
            borders = []
            border_rows = connection.execute(
                "SELECT gb.border_role,gb.align,gb.target_mode,gb.target_brush_name,bs.xml_border_id,bs.id "
                "FROM rme_ground_brush_borders gb JOIN rme_border_sets bs ON bs.id=gb.border_set_id "
                "WHERE gb.brush_id=? ORDER BY gb.sort_order LIMIT 6",
                (brush_id,),
            ).fetchall()
            for border in border_rows:
                pieces = {
                    str(piece["edge"]): int(piece["item_id"])
                    for piece in connection.execute(
                        "SELECT edge,item_id FROM rme_border_set_items WHERE border_set_id=? ORDER BY sort_order",
                        (int(border["id"]),),
                    )
                }
                borders.append({
                    "border_id": int(border["xml_border_id"] or 0),
                    "role": str(border["border_role"]),
                    "align": str(border["align"]),
                    "target_mode": str(border["target_mode"]),
                    "target_brush": str(border["target_brush_name"] or ""),
                    "orientation_items": pieces,
                })
            entry["autoborders"] = borders
        elif kind == "wall":
            parts = []
            for part in connection.execute(
                "SELECT id,part_type FROM rme_wall_parts WHERE brush_id=? ORDER BY sort_order",
                (brush_id,),
            ):
                part_items = [int(item["item_id"]) for item in connection.execute(
                    "SELECT item_id FROM rme_wall_part_items WHERE wall_part_id=? ORDER BY sort_order LIMIT 12",
                    (int(part["id"]),),
                )]
                doors = [
                    {"id": int(door["item_id"]), "type": str(door["door_type"]), "open": bool(door["is_open"])}
                    for door in connection.execute(
                        "SELECT item_id,door_type,is_open FROM rme_wall_part_doors "
                        "WHERE wall_part_id=? ORDER BY sort_order LIMIT 12",
                        (int(part["id"]),),
                    )
                ]
                parts.append({"orientation": str(part["part_type"]), "items": part_items, "doors": doors})
            entry["neighbor_parts"] = parts
        elif kind == "doodad":
            entry["placement"] = "weighted alternatives/composites resolved by DoodadBrush"
        return entry

    @staticmethod
    def _town_profiles(connection: sqlite3.Connection, towns: Iterable[str]) -> list[dict[str, Any]]:
        profiles = []
        for town in towns:
            observations = connection.execute(
                "SELECT floor,AVG(water_ratio) water,AVG(nature_ratio) nature,AVG(edge_density) edges "
                "FROM town_floor_observations o JOIN towns t ON t.town_id=o.town_id "
                "WHERE lower(t.name)=lower(?) GROUP BY floor ORDER BY floor",
                (town,),
            ).fetchall()
            structures = connection.execute(
                "SELECT kind,COUNT(*) count,ROUND(AVG(width),2) avg_width,ROUND(AVG(height),2) avg_height,"
                "ROUND(AVG(floors),2) avg_floors FROM town_structures s JOIN towns t ON t.town_id=s.town_id "
                "WHERE lower(t.name)=lower(?) GROUP BY kind ORDER BY count DESC LIMIT 10",
                (town,),
            ).fetchall()
            profiles.append({
                "town": town,
                "floors": [
                    {"z": int(row["floor"]), "water_ratio": round(float(row["water"] or 0), 4),
                     "nature_ratio": round(float(row["nature"] or 0), 4),
                     "edge_density": round(float(row["edges"] or 0), 4)}
                    for row in observations
                ],
                "structures": [dict(row) for row in structures],
                "reference_only": True,
                "source_coordinates_included": False,
            })
        return profiles

    @staticmethod
    def _catalog_version(connection: sqlite3.Connection) -> str:
        row = connection.execute("SELECT version FROM rme_schema_version LIMIT 1").fetchone()
        return str(row["version"] if row else "unknown")

    @staticmethod
    def _unavailable() -> dict[str, Any]:
        return {
            "status": "UNAVAILABLE", "all_ids_certified": False,
            "allowed_material_keys": [], "brushes": [], "reference_profiles": [],
        }


def _tokens(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", str(value).casefold()).encode("ascii", "ignore").decode("ascii")
    return {token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 2}


def _key_fragment(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold()).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")


__all__ = ["CertifiedMaterialBriefBuilder"]
