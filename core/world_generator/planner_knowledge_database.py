from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
import time
import unicodedata
import zlib
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

from core.opentibia.assets.material_loader import BrushMaterialLoader
from core.opentibia.assets.appearance_dat_flags import AppearanceDatFlagExtractor
from core.world_generator.rme_materials_necro_v5 import (
    classify_items,
    expand_item_ids,
    load_material_catalog,
    resolve_materials_dir,
)


SCHEMA_VERSION = 12

_LIVE_RME_TERRAIN_TILESETS = (
    "Grounds - Mountains", "Grounds - Nature", "Grounds - Ornamented",
    "Grounds - Tiny Borders", "Nature - Grass", "Nature - Tiny Borders",
    "Railings", "Roofs", "Snow", "Stairs / Ramps / Ladders", "Walls",
)


class ReferenceCorpusChangedError(RuntimeError):
    """A live reference changed before its staged database could be published."""


class PlannerKnowledgeDatabase:
    """Build the Planner's normalized, provenance-aware technical catalog."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def connect(self, *, read_only: bool = False) -> sqlite3.Connection:
        if read_only:
            connection = sqlite3.connect(
                f"file:{self.path.resolve().as_posix()}?mode=ro",
                uri=True,
                timeout=30.0,
            )
            connection.execute("PRAGMA query_only = ON")
        else:
            connection = sqlite3.connect(self.path, timeout=30.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        if not read_only:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = NORMAL")
        return connection

    def search_materials(self, query: str, limit: int = 50) -> list[dict[str, Any]]:
        pattern = f"%{query.lower()}%"
        with self.connect(read_only=True) as connection:
            rows = connection.execute(
                "SELECT 'brush' AS kind, id, name, type AS detail, source_file AS source "
                "FROM rme_brushes WHERE lower(name) LIKE ? "
                "UNION ALL SELECT 'tileset', id, name, '', source_file FROM rme_tilesets "
                "WHERE lower(name) LIKE ? ORDER BY kind, name LIMIT ?",
                (pattern, pattern, max(1, int(limit))),
            ).fetchall()
        return [dict(row) for row in rows]

    def brush_grammar(self, query: str, limit: int = 16) -> list[dict[str, Any]]:
        """Return exact parsed brush trees ranked by name/type without reparsing XML."""
        normalized = unicodedata.normalize("NFKD", query.casefold()).encode("ascii", "ignore").decode("ascii")
        tokens = {token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 1}
        with self.connect(read_only=True) as connection:
            if not _table_exists(connection, "parsed_brush_grammar"):
                return []
            rows = connection.execute(
                "SELECT brush_key,name,type,look_id,server_look_id,member_count,grammar_sha256,source_file "
                "FROM parsed_brush_grammar ORDER BY type,name"
            ).fetchall()
            ranked: list[tuple[int, str, sqlite3.Row]] = []
            for row in rows:
                normalized_name = unicodedata.normalize(
                    "NFKD", str(row["name"]).casefold()
                ).encode("ascii", "ignore").decode("ascii")
                searchable_tokens = set(re.findall(
                    r"[a-z0-9]+", f"{normalized_name} {str(row['type']).casefold()}"
                ))
                score = 1000 if normalized.strip() == normalized_name else 0
                score += 200 if normalized_name in tokens else 0
                score += 20 * len(tokens & searchable_tokens)
                ranked.append((score, str(row["name"]).casefold(), row))
            ranked.sort(key=lambda entry: (-entry[0], entry[1]))
            selected = [row for score, _, row in ranked if score > 0]
            if not selected and not tokens:
                selected = [row for _, _, row in ranked]
            selected = selected[: max(1, min(64, int(limit)))]
            results = []
            for row in selected:
                grammar_row = connection.execute(
                    "SELECT grammar_json FROM parsed_brush_grammar WHERE brush_key=?", (row["brush_key"],)
                ).fetchone()
                results.append({
                    "brush_key": row["brush_key"], "name": row["name"], "type": row["type"],
                    "look_id": row["look_id"], "server_look_id": row["server_look_id"],
                    "member_count": int(row["member_count"] or 0),
                    "grammar_sha256": row["grammar_sha256"], "source_file": row["source_file"],
                    "grammar": json.loads(grammar_row["grammar_json"]),
                })
        return results

    def refresh_brush_grammar(self, root: str | Path = ".") -> dict[str, Any]:
        """Atomically refresh the parsed brush cache in an existing Planner database."""
        base = Path(root).resolve()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                _create_parsed_brush_grammar_table(connection)
                count, members = self._parsed_brush_grammar(connection, base, replace=True)
                connection.executemany(
                    "INSERT INTO metadata(key,value) VALUES (?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (("schema_version", str(SCHEMA_VERSION)), ("format", "rme-planner-knowledge-sqlite-v12")),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        return {
            "status": "PASS" if integrity == "ok" else "BLOCKED",
            "database": str(self.path), "schema_version": SCHEMA_VERSION,
            "brushes": count, "members": members, "integrity": integrity,
        }

    def refresh_runtime_knowledge(self) -> dict[str, Any]:
        """Refresh live-observed RME behavior without rebuilding the heavy catalog."""
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                self._editor_runtime_observations(connection)
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            count = connection.execute(
                "SELECT COUNT(*) FROM editor_runtime_observations"
            ).fetchone()[0]
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        return {
            "status": "PASS" if integrity == "ok" else "BLOCKED",
            "database": str(self.path),
            "runtime_rules": int(count),
            "integrity": integrity,
        }

    def refresh_reference_corpus(self, root: str | Path = ".") -> dict[str, Any]:
        """Rebuild references off-line and publish them without stopping live readers."""
        base = Path(root).resolve()
        source_snapshot = _reference_source_snapshot(base)
        dependent_tables = (
            "reference_minimap_color_materials",
            "reference_minimap_colors",
            "reference_border_mixes",
            "reference_floor_material_usage",
            "reference_scan_reports",
            "reference_ground_transitions",
            "reference_brush_usage",
            "reference_floor_profiles",
            "reference_material_usage",
            "reference_source_archives",
            "reference_maps",
            "reference_archetypes",
        )
        temporary = self.path.with_name(
            f".{self.path.name}.reference-refresh-{os.getpid()}-{threading.get_ident()}.tmp"
        )
        temporary.unlink(missing_ok=True)
        started = time.monotonic()
        try:
            source = self.connect(read_only=True)
            staging = sqlite3.connect(temporary, timeout=30.0)
            try:
                source.backup(staging)
            finally:
                staging.close()
                source.close()
            connection = sqlite3.connect(temporary, timeout=30.0)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            try:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    for table in dependent_tables:
                        connection.execute(f"DELETE FROM {table}")
                    self._reference_map_corpus(connection, base)
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                counts = {
                    table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                    for table in dependent_tables
                }
            finally:
                connection.close()
            if integrity != "ok":
                raise sqlite3.DatabaseError(
                    f"Reference staging database failed integrity_check: {integrity}"
                )
            if _reference_source_snapshot(base) != source_snapshot:
                raise ReferenceCorpusChangedError(
                    "Reference corpus changed while its staging database was being built"
                )
            self._publish_live_database(temporary)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return {
            "status": "PASS" if integrity == "ok" else "BLOCKED",
            "database": str(self.path),
            "schema_version": SCHEMA_VERSION,
            "integrity": integrity,
            "counts": counts,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "readers_remained_available": True,
        }
    def _publish_live_database(self, temporary: Path) -> None:
        source = sqlite3.connect(temporary, timeout=30.0)
        destination = self.connect()
        try:
            source.backup(destination)
            destination.commit()
            integrity = destination.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise sqlite3.DatabaseError(
                    f"Published Planner database failed integrity_check: {integrity}"
                )
        finally:
            destination.close()
            source.close()
            temporary.unlink(missing_ok=True)

    def tileset_knowledge(self, query: str = "", limit: int = 32) -> list[dict[str, Any]]:
        """Expose the complete RME tileset membership already cached in SQLite."""
        normalized = unicodedata.normalize("NFKD", query.casefold()).encode("ascii", "ignore").decode("ascii")
        tokens = {token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 2}
        expansions = {
            "venore": {"swamp", "nature", "grass", "sea", "wood", "roof", "wall"},
            "roshamuul": {"dark", "mountain", "cave", "wall", "ruin", "nature"},
            "krailos": {"dry", "earth", "rock", "mountain", "ruin", "nature"},
            "city": {"wall", "roof", "ornamented", "railing", "street"},
            "ciudad": {"wall", "roof", "ornamented", "railing", "street"},
            "hunt": {"nature", "mountain", "ground", "cave", "doodad"},
            "pantano": {"swamp", "nature", "grass", "water"},
            "montana": {"mountain", "rock", "cave", "stairs"},
        }
        for token in tuple(tokens):
            tokens.update(expansions.get(token, ()))
        with self.connect(read_only=True) as connection:
            tilesets = connection.execute(
                "SELECT t.id,t.name,t.source_file,COUNT(DISTINCT s.id) AS section_count,"
                "COUNT(e.id) AS entry_count,GROUP_CONCAT(COALESCE(e.brush_name,''),' ') AS brush_names "
                "FROM rme_tilesets t "
                "LEFT JOIN rme_tileset_sections s ON s.tileset_id=t.id "
                "LEFT JOIN rme_tileset_brush_entries e ON e.tileset_section_id=s.id "
                "GROUP BY t.id,t.name,t.source_file ORDER BY t.name",
            ).fetchall()
            ranked = []
            for tileset in tilesets:
                searchable = unicodedata.normalize(
                    "NFKD", f"{tileset['name']} {tileset['brush_names']}".casefold()
                ).encode("ascii", "ignore").decode("ascii")
                searchable_tokens = set(re.findall(r"[a-z0-9]+", searchable))
                score = 20 * len(tokens & searchable_tokens)
                score += 100 if normalized and normalized in searchable else 0
                ranked.append((score, str(tileset["name"]).casefold(), tileset))
            ranked.sort(key=lambda value: (-value[0], value[1]))
            selected = [row for score, _name, row in ranked if score > 0]
            if not selected:
                selected = [row for _score, _name, row in ranked]
            selected = selected[: max(1, min(128, int(limit)))]
            results: list[dict[str, Any]] = []
            for tileset in selected:
                rows = connection.execute(
                    "SELECT s.section_type,e.entry_kind,e.brush_id,e.brush_name,e.item_id,"
                    "e.from_item_id,e.to_item_id,e.after_brush_name,e.after_item_id,e.sort_order,"
                    "b.type AS brush_type,b.look_id,b.server_look_id,b.z_order,b.source_file "
                    "FROM rme_tileset_sections s "
                    "LEFT JOIN rme_tileset_brush_entries e ON e.tileset_section_id=s.id "
                    "LEFT JOIN rme_brushes b ON b.id=e.brush_id WHERE s.tileset_id=? "
                    "ORDER BY s.sort_order,e.sort_order",
                    (tileset["id"],),
                ).fetchall()
                results.append({
                    "id": int(tileset["id"]),
                    "name": tileset["name"],
                    "source_file": tileset["source_file"],
                    "section_count": int(tileset["section_count"] or 0),
                    "entry_count": int(tileset["entry_count"] or 0),
                    "sections": sorted({str(row["section_type"]) for row in rows if row["section_type"]}),
                    "entries": [dict(row) for row in rows],
                })
        return results

    def reference_archetypes(self, objective: str = "", limit: int = 8) -> list[dict[str, Any]]:
        """Return compact reference grammars ranked by the requested map intent."""
        normalized = unicodedata.normalize("NFKD", objective.lower()).encode("ascii", "ignore").decode("ascii")
        tokens = {token for token in normalized.replace("_", " ").split() if len(token) > 2}
        aliases = {
            "river": {"river", "rio", "agua", "water", "canal", "orilla", "bank"},
            "nature": {"nature", "naturaleza", "vegetacion", "vegetation", "bosque", "forest", "jungle"},
            "miniboats": {"miniboats", "boat", "boats", "barco", "barcos", "bote", "muelle", "dock"},
            "towers": {"tower", "towers", "torre", "torres", "vertical", "multifloor", "pisos"},
            "krailos": {"krailos", "dry", "seco", "ruins", "ruinas", "hunt", "roca", "rocky"},
            "roshamuul_map": {
                "roshamuul", "dark", "oscuro", "ruins", "ruinas", "hunt",
                "mountain", "montana", "moss", "muddy", "swamp", "pavement",
            },
            "montaña": {"montana", "mountain", "mountains", "montana", "relieve", "cliff", "acantilado"},
            "firecave": {"firecave", "fire", "cave", "cueva", "fuego", "lava", "volcanic", "volcanico"},
        }
        with self.connect(read_only=True) as connection:
            rows = connection.execute(
                "SELECT name, source_count, metrics_json, generation_rules_json "
                "FROM reference_archetypes ORDER BY name"
            ).fetchall()
        ranked = []
        for row in rows:
            payload = {
                "name": row["name"],
                "source_count": row["source_count"],
                "metrics": json.loads(row["metrics_json"]),
                "generation_rules": json.loads(row["generation_rules_json"]),
            }
            searchable = json.dumps(payload, sort_keys=True).lower()
            score = sum(1 for token in tokens if token in searchable)
            normalized_name = unicodedata.normalize("NFKD", payload["name"].lower()).encode("ascii", "ignore").decode("ascii")
            score += 3 * len(tokens.intersection(aliases.get(payload["name"], aliases.get(normalized_name, set()))))
            ranked.append((score, payload["name"], payload))
        ranked.sort(key=lambda entry: (-entry[0], entry[1]))
        return [payload for _, _, payload in ranked[: max(1, int(limit))]]

    def reference_scans(self, objective: str = "", limit: int = 3) -> list[dict[str, Any]]:
        """Return ranked scanner summaries without opening source OTBMs."""
        from core.world_generator.reference_map_scanner import ReferenceMapScanner

        normalized = unicodedata.normalize("NFKD", objective.lower()).encode("ascii", "ignore").decode("ascii")
        tokens = {token for token in normalized.replace("_", " ").split() if len(token) > 2}
        aliases = {
            "river": {"river", "rio", "agua", "canal", "orilla"},
            "nature": {"nature", "naturaleza", "vegetacion", "bosque", "jungle"},
            "miniboats": {"boat", "boats", "barco", "barcos", "bote", "muelle"},
            "towers": {"tower", "towers", "torre", "torres", "vertical", "pisos"},
            "krailos": {"krailos", "seco", "ruinas", "hunt", "roca", "rocky"},
            "roshamuul_map": {
                "roshamuul", "oscuro", "ruinas", "hunt", "montana",
                "moss", "muddy", "swamp", "pavement",
            },
            "montana": {"montana", "mountain", "mountains", "relieve", "cliff", "acantilado"},
            "firecave": {"firecave", "fire", "cave", "cueva", "fuego", "lava", "volcanic", "volcanico"},
        }
        with self.connect(read_only=True) as connection:
            rows = connection.execute(
                "SELECT rm.name, rs.report_json FROM reference_scan_reports rs "
                "JOIN reference_maps rm ON rm.id = rs.reference_id ORDER BY rm.name"
            ).fetchall()
        ranked = []
        for row in rows:
            report = json.loads(row["report_json"])
            name = unicodedata.normalize("NFKD", row["name"].lower()).encode("ascii", "ignore").decode("ascii")
            searchable = json.dumps(report["guidance"] + [report["generation_rules"]], sort_keys=True).lower()
            score = sum(1 for token in tokens if token in searchable)
            alias_matches = tokens.intersection(aliases.get(name, set()))
            score += 3 * len(alias_matches)
            explicitly_named = bool(
                tokens.intersection({token for token in name.replace("_", " ").split() if len(token) > 2})
                or alias_matches
            )
            ranked.append((score, name, explicitly_named, ReferenceMapScanner.compact_for_prompt(report)))
        ranked.sort(key=lambda entry: (-entry[0], entry[1]))
        explicitly_named = [entry for entry in ranked if entry[2]]
        relevant = explicitly_named or ([entry for entry in ranked if entry[0] > 0] if tokens else ranked)
        return [payload for _, _, _, payload in relevant[: max(1, int(limit))]]

    def world_town_scans(self, objective: str = "", limit: int = 3) -> list[dict[str, Any]]:
        """Return compact town scans from SQLite; never reopen world.otbm."""
        normalized = unicodedata.normalize("NFKD", objective.lower()).encode("ascii", "ignore").decode("ascii")
        tokens = {token for token in normalized.replace("_", " ").replace("'", "").split() if len(token) > 2}
        with self.connect(read_only=True) as connection:
            rows = connection.execute(
                "SELECT town_name, report_json FROM world_town_scan_reports ORDER BY town_name"
            ).fetchall()
        ranked = []
        for row in rows:
            report = json.loads(row["report_json"])
            town_tokens = set(
                unicodedata.normalize("NFKD", row["town_name"].lower())
                .encode("ascii", "ignore").decode("ascii").replace("'", "").split()
            )
            exact_score = len(tokens.intersection(town_tokens))
            structural = json.dumps(report.get("structure_counts", {}), sort_keys=True).lower()
            semantic_score = sum(1 for token in tokens if token in structural)
            ranked.append((exact_score * 10 + semantic_score, exact_score, row["town_name"], self._compact_town_scan(report)))
        ranked.sort(key=lambda entry: (-entry[0], entry[2]))
        explicitly_named = [entry for entry in ranked if entry[1] > 0]
        relevant = explicitly_named or ([entry for entry in ranked if entry[0] > 0] if tokens else ranked)
        return [entry[3] for entry in relevant[: max(1, int(limit))]]

    def quest_script_patterns(self, objective: str = "", limit: int = 6) -> list[dict[str, Any]]:
        """Return compact quest grammars; archived Lua is intentionally inaccessible here."""
        from core.world_generator.quest_script_scanner import QuestScriptScanner

        normalized = unicodedata.normalize("NFKD", objective.lower()).encode("ascii", "ignore").decode("ascii")
        tokens = {token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 2}
        aliases = {
            "reward": {"reward", "recompensa", "chest", "cofre", "loot", "premio"},
            "movement": {"movement", "movimiento", "teleport", "escalera", "lever", "palanca"},
            "storage": {"storage", "questline", "mission", "mision", "estado"},
            "boss": {"boss", "jefe", "arena", "lever", "palanca"},
        }
        with self.connect(read_only=True) as connection:
            rows = connection.execute(
                "SELECT name, scope, script_count, language, summary_json, grammar_json "
                "FROM quest_packages ORDER BY name"
            ).fetchall()
        ranked = []
        for row in rows:
            summary = json.loads(row["summary_json"])
            package = {
                "name": row["name"], "scope": row["scope"], "script_count": row["script_count"],
                "language": row["language"], **summary,
                "generation_grammar": json.loads(row["grammar_json"]),
            }
            searchable = json.dumps(package, sort_keys=True).lower().replace("_", " ")
            score = sum(1 for token in tokens if token in searchable)
            for key, words in aliases.items():
                if tokens.intersection(words) and key in searchable:
                    score += 3
            if package["scope"] == "quest":
                score += 1
            ranked.append((score, package["name"], QuestScriptScanner.compact_for_prompt(package)))
        ranked.sort(key=lambda entry: (-entry[0], entry[1]))
        relevant = [entry for entry in ranked if entry[0] > 1] or ranked
        return [entry[2] for entry in relevant[: max(1, int(limit))]]

    def editor_runtime_rules(self, objective: str = "", limit: int = 32) -> list[dict[str, Any]]:
        """Return verified editor behavior, never captured source geometry."""
        tokens = {
            token for token in re.findall(
                r"[a-z0-9]+",
                unicodedata.normalize("NFKD", objective.casefold()).encode("ascii", "ignore").decode("ascii"),
            ) if len(token) > 2
        }
        with self.connect(read_only=True) as connection:
            rows = connection.execute(
                "SELECT domain, rule_key, behavior_json, provenance, confidence "
                "FROM editor_runtime_observations ORDER BY domain, rule_key"
            ).fetchall()
        ranked = []
        for row in rows:
            payload = {
                "domain": row["domain"],
                "rule": row["rule_key"],
                "behavior": json.loads(row["behavior_json"]),
                "provenance": row["provenance"],
                "confidence": row["confidence"],
            }
            searchable = json.dumps(payload, sort_keys=True).casefold()
            ranked.append((sum(token in searchable for token in tokens), payload))
        ranked.sort(key=lambda entry: (-entry[0], entry[1]["domain"], entry[1]["rule"]))
        return [payload for _, payload in ranked[: max(1, int(limit))]]

    def rme_technical_grammar(self, objective: str = "", limit: int = 16) -> dict[str, Any]:
        """Return bounded exact brush mathematics and operation grammar for Planner/AI use."""
        tokens = {
            token for token in re.findall(
                r"[a-z0-9]+",
                unicodedata.normalize("NFKD", objective.casefold()).encode("ascii", "ignore").decode("ascii"),
            ) if len(token) > 2
        }
        with self.connect(read_only=True) as connection:
            grammar_rows = connection.execute(
                "SELECT domain,rule_key,grammar_json,provenance,confidence FROM rme_operation_grammar"
            ).fetchall()
            lookup_counts = {
                row["system"]: int(row["amount"])
                for row in connection.execute(
                    "SELECT system,COUNT(*) amount FROM rme_neighbor_lookup GROUP BY system ORDER BY system"
                )
            }
            directions = [dict(row) for row in connection.execute(
                "SELECT system,bit,direction,dx,dy,dz FROM rme_neighbor_bits ORDER BY system,bit"
            )]
            coverage = [dict(row) for row in connection.execute(
                "SELECT category,row_count,certified,source FROM rme_knowledge_coverage ORDER BY category"
            )]
            source_hashes = [dict(row) for row in connection.execute(
                "SELECT source_file,sha256,bytes,provenance FROM rme_algorithm_sources ORDER BY source_file"
            )]
            menu_entries = [dict(row) for row in connection.execute(
                "SELECT entry_path,parent_path,depth,ordinal,entry_kind,raw_name,display_name,action,hotkey,help,special "
                "FROM rme_menu_entries ORDER BY sequence LIMIT 256"
            )]
            action_handlers = [dict(row) for row in connection.execute(
                "SELECT action,kind,handler,visible_in_menu,source_file FROM rme_action_handlers ORDER BY action"
            )]
        ranked = []
        for row in grammar_rows:
            payload = {
                "domain": row["domain"], "rule": row["rule_key"],
                "grammar": json.loads(row["grammar_json"]), "provenance": row["provenance"],
                "confidence": float(row["confidence"]),
            }
            searchable = json.dumps(payload, sort_keys=True).casefold()
            score = sum(token in searchable for token in tokens)
            ranked.append((score, payload["domain"], payload))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return {
            "status": "CERTIFIED",
            "schema_version": SCHEMA_VERSION,
            "lookup_table_cardinality": lookup_counts,
            "neighbor_bit_contract": directions,
            "operation_grammar": [row[2] for row in ranked[: max(1, min(32, int(limit)))]],
            "catalog_coverage": coverage,
            "source_hashes": source_hashes,
            "menu_contract": menu_entries,
            "action_handlers": action_handlers,
            "materialization_authority": "RME Brush Engine",
            "geometry_copying_allowed": False,
        }

    def rme_neighbor_lookup(self, system: str, mask: int | None = None, limit: int = 256) -> list[dict[str, Any]]:
        """Resolve an exact official neighbor mask without reimplementing RME tables in callers."""
        normalized = str(system).strip().lower()
        allowed = {"ground_border", "wall_full", "wall_half", "table", "carpet"}
        if normalized not in allowed:
            raise ValueError("unsupported RME lookup system")
        with self.connect(read_only=True) as connection:
            if mask is None:
                rows = connection.execute(
                    "SELECT system,mask,mask_binary,input_expression,output_expression,decoded_json,source_file "
                    "FROM rme_neighbor_lookup WHERE system=? ORDER BY mask LIMIT ?",
                    (normalized, max(1, min(256, int(limit)))),
                ).fetchall()
            else:
                max_mask = 15 if normalized.startswith("wall_") else 255
                value = int(mask)
                if not 0 <= value <= max_mask:
                    raise ValueError("neighbor mask is outside the lookup range")
                rows = connection.execute(
                    "SELECT system,mask,mask_binary,input_expression,output_expression,decoded_json,source_file "
                    "FROM rme_neighbor_lookup WHERE system=? AND mask=?",
                    (normalized, value),
                ).fetchall()
        return [
            {
                "system": row["system"], "mask": int(row["mask"]), "mask_binary": row["mask_binary"],
                "input_expression": row["input_expression"], "output_expression": row["output_expression"],
                "decoded": json.loads(row["decoded_json"]), "source_file": row["source_file"],
            }
            for row in rows
        ]

    @staticmethod
    def _compact_town_scan(report: dict[str, Any], material_limit: int = 16) -> dict[str, Any]:
        floors = []
        for z in report.get("floors_examined", range(16)):
            floor = report.get("floors", {}).get(str(z), {})
            floors.append({
                "floor": z,
                "tile_count": floor.get("tile_count", 0),
                "grounds": [row["item_id"] for row in floor.get("grounds", ())[:material_limit]],
                "nature": [row["item_id"] for row in floor.get("nature", ())[:material_limit]],
                "borders": [row["item_id"] for row in floor.get("borders", ())[:material_limit]],
                "walls": [row["item_id"] for row in floor.get("walls", ())[:material_limit]],
                "semantic_features": {
                    kind: value.get("evidence_tiles", 0)
                    for kind, value in floor.get("semantic_features", {}).items()
                },
            })
        spawns = report.get("spawns", {})
        return {
            "town": report["town"],
            "anchor_floor": report.get("anchor_floor"),
            "floors_examined": report.get("floors_examined", list(range(16))),
            "content_floors": report.get("content_floors", []),
            "floors": floors,
            "structure_counts": report.get("structure_counts", {}),
            "houses": {key: value for key, value in report.get("houses", {}).items() if key != "structures"},
            "spawns": {
                "spawn_groups": spawns.get("spawn_groups", 0),
                "monster_count": spawns.get("monster_count", 0),
                "floors": spawns.get("floors", {}),
                "monster_mix": dict(list(spawns.get("monster_mix", {}).items())[:32]),
                "boss_evidence": spawns.get("boss_evidence", {}),
                "hunt_zone_count": len(spawns.get("hunt_zones", ())),
            },
            "npcs": report.get("npcs", {}),
            "classification_policy": report.get("classification_policy", {}),
            "similarity_guard_required": True,
        }

    def build(self, root: str | Path = ".") -> dict[str, Any]:
        try:
            return self._build(root)
        except (OSError, UnicodeError, sqlite3.Error, ValueError) as exc:
            self.path.with_suffix(self.path.suffix + ".tmp").unlink(missing_ok=True)
            return {
                "status": "BLOCKED",
                "database": str(self.path),
                "schema_version": SCHEMA_VERSION,
                "retained_previous_database": self.path.is_file(),
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

    def _build(self, root: str | Path = ".") -> dict[str, Any]:
        base = Path(root).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.unlink(missing_ok=True)
        connection = sqlite3.connect(temporary)
        try:
            connection.executescript(_SCHEMA)
            self._metadata(connection)
            self._sources(connection, base)
            self._appearances(connection, base)
            self._materials(connection, base)
            self._canary_material_archive(connection, base)
            self._rme_technical_knowledge(connection, base)
            self._towns(connection, base)
            self._visual_observations(connection, base)
            self._structural_patterns(connection, base)
            self._town_topology(connection, base)
            self._reference_map_corpus(connection, base)
            self._world_town_scans(connection, base)
            self._quest_script_knowledge(connection, base)
            self._editor_runtime_observations(connection)
            connection.commit()
            counts = {
                table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in _COUNTED_TABLES
            }
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            material_database = {
                "table_count": connection.execute(
                    "SELECT COUNT(*) FROM material_db_inventory"
                ).fetchone()[0],
                "row_count": connection.execute(
                    "SELECT COALESCE(SUM(row_count), 0) FROM material_db_inventory"
                ).fetchone()[0],
            }
        finally:
            connection.close()
        self._publish_database(temporary)
        return {
            "status": "PASS" if integrity == "ok" else "BLOCKED",
            "database": str(self.path),
            "schema_version": SCHEMA_VERSION,
            "integrity": integrity,
            "counts": counts,
            "material_database": material_database,
            "policy": (
                "technical catalogs, complete analysis-only reference archives, cached world-town scans and "
                "abstract planner profiles; runtime generation receives no source screenshots, coordinates "
                "or tile stacks"
            ),
        }

    def _publish_database(self, temporary: Path) -> None:
        """Publish a complete build even when the local server holds a read handle."""
        try:
            temporary.replace(self.path)
            return
        except PermissionError:
            if not self.path.is_file():
                raise

        source = sqlite3.connect(temporary, timeout=30.0)
        destination = sqlite3.connect(self.path, timeout=30.0)
        try:
            source.backup(destination)
            destination.commit()
            integrity = destination.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise sqlite3.DatabaseError(
                    f"Published Planner database failed integrity_check: {integrity}"
                )
        finally:
            destination.close()
            source.close()
        temporary.unlink()

    @staticmethod
    def _metadata(db: sqlite3.Connection) -> None:
        db.executemany(
            "INSERT INTO metadata(key, value) VALUES (?, ?)",
            (("schema_version", str(SCHEMA_VERSION)), ("format", "rme-planner-knowledge-sqlite-v12")),
        )

    @staticmethod
    def _rme_technical_knowledge(db: sqlite3.Connection, root: Path) -> None:
        from core.world_generator.rme_technical_knowledge import RMETechnicalKnowledgeCompiler

        RMETechnicalKnowledgeCompiler(root).populate(db)

    @staticmethod
    def _editor_runtime_observations(db: sqlite3.Connection) -> None:
        rows = (
            ("assets", "client_root_resolution", {"select": "client root or assets folder", "canonical": "client_root/assets", "required": ["appearances-*.dat", "catalog-content.json", "sprite sheets"]}),
            ("document", "generated_sidecar_bundle", {"otbm": "open", "required_siblings": ["house", "monster", "npc", "zones"], "filename_rule": "<otbm-stem>-<kind>.xml", "empty_document": "write a valid empty root", "goal": "open in Canary without missing-sidecar dialogs"}),
            ("document", "generated_navigation_header", {"minimum_dimensions": [2048, 2048], "margin_after_max_coordinate": 32, "navigation_town": True, "temple_anchor": [1000, 1000, 7], "goal": "open generated compact maps near their content"}),
            ("document", "workspace_new_map_bounds", {"dimensions": [2048, 2048], "coordinate_range": [0, 2047], "planner_anchor": [1000, 1000, 7], "reason": "RME-compatible untitled documents must accept centered Planner proposals"}),
            ("palette", "semantic_brush_selection", {"selection": "brush key", "forbidden": "raw member id as semantic substitute", "engine_resolves": ["chance", "variant", "orientation", "stack order"]}),
            ("ground_brush", "neighbor_autoborder", {"commit": "atomic", "neighbor_aware": True, "border_timing": "same gesture", "invalidate": "all affected coordinates"}),
            ("border_options", "automagic_pair", {"source": "main_menubar.cpp", "menu": "Edit/Border Options", "shortcut": "A", "toggles_together": ["USE_AUTOMAGIC", "BORDER_IS_GROUND"], "compiled_default": True, "persist_user_preference": True}),
            ("border_options", "selection_operations", {"borderize": "Ctrl+B", "randomize": True, "enabled_when": "selection is non-empty", "history": "transactional and undoable"}),
            ("border_options", "full_map_operations", {"operations": ["Borderize Map", "Randomize Map"], "confirmation": True, "rme_history": "not undoable", "workspace_stability": "bounded progressive batches"}),
            ("brush_engine", "postprocess_matrix", {"ground": {"borderize": "only when automagic"}, "eraser": {"when_automagic": ["wallize", "tableize", "carpetize", "borderize"]}, "table": {"tableize": "always"}, "carpet": {"carpetize": "always"}, "wall": {"clean_same_family": "always", "wallize_neighbors": "when automagic", "alt_temporary_map": "always wallize"}, "door": {"transform_existing_wall_alignment": True, "wallize": "when automagic"}, "optional_border": {"set_tile_optional_flag": True, "then_borderize": True}}),
            ("brush_engine", "semantic_stack_placement", {"ground_brush": "replace ground and preserve items", "non_ground_brush": "append item to existing tile stack", "forbidden": "store roof railing stair wall doodad or decoration as ground", "draw_order": "ItemType stack order"}),
            ("brush_engine", "connected_item_masks", {"source": "brush_tables.cpp", "systems": {"table": 256, "carpet": 256}, "neighbor_bits": ["northwest", "north", "northeast", "west", "east", "southwest", "south", "southeast"], "table_alignments": ["alone", "vertical", "horizontal", "north", "south", "east", "west"], "carpet_alignments": ["center", "n", "e", "s", "w", "cnw", "cne", "cse", "csw", "dnw", "dne", "dse", "dsw"], "postprocess": "always, independent of automagic", "transaction": "same BatchAction as draw"}),
            ("ground_brush", "border_mask_table", {"source": "brush_tables.cpp GroundBrush::border_types[256]", "neighbor_bits": ["northwest", "north", "northeast", "west", "east", "southwest", "south", "southeast"], "outputs_per_tile": {"minimum": 0, "maximum": 4}, "rule": "retain every returned border piece in output-slot order; never collapse a mask to its first edge"}),
            ("ground_brush", "contextual_border_family_resolution", {"source": "ground_brush.cpp GroundBrush::getBrushTo/doBorders", "inputs": ["current ground family", "neighbor ground family", "z-order", "inner/outer role", "to target", "friend relationship"], "clustering": "build one 8-neighbor mask per distinct neighboring ground family", "selection": "prefer matching inner border when lower z meets higher z, otherwise matching outer border of the higher family", "none_boundary": "requires explicit inner to=none", "forbidden": "apply the selected ground brush outer border to every different neighbor"}),
            ("ground_brush", "optional_border_tool", {"source": ["brush.cpp OptionalBorderBrush", "editor.cpp Editor::drawInternal", "ground_brush.cpp GroundBrush::doBorders"], "draw": "set explicit optional-border flag on target tile then borderize", "erase": "clear flag then borderize", "can_draw": "target ground must not itself own an optional border and at least one of eight neighbors must own one", "border_source": "the neighboring optional-border ground family", "forbidden": "pseudo-random modulo placement", "idempotence": "replace previously generated optional pieces before rebuilding"}),
            ("ground_brush", "specific_case_rewrites", {"source": "ground_brush.cpp plus official materials", "cases": 117, "conditions": ["match border item", "match exact item", "match border group"], "actions": ["replace border", "replace item", "delete matched borders"], "timing": "after normal border-mask construction in the same transaction", "examples": {"4728+4634": "4728+6652"}}),
            ("ground_brush", "diagonal_border_fallback", {"source": "ground_brush.cpp", "rule": "when a requested diagonal border item is absent, emit both adjacent cardinal pieces", "maximum_output_pieces": 4, "forbidden": "drop the diagonal or keep only one cardinal edge"}),
            ("assets", "sprite_backed_brush_certification", {"sources": ["APPEARANCE_ITEM_CATALOG.json", "APPEARANCE_RENDER_CATALOG.json", "appearances.dat"], "predicate": "appearance_present and non-empty sprite_ids", "certified_item_ids": 42099, "ground_policy": "item must also be a member of an official GroundBrush", "official_ground_declarations": {"unique_names": 253, "materialized_families": 251, "empty_alias_declarations": 6}, "failure_policy": "fail closed; never infer sprite safety from an item name"}),
            ("doodad_brush", "alternative_blocks", {"source": "doodad_brush.cpp DoodadBrush::loadAlternative", "official_unique_families": 1472, "selection": "one coherent alternate block per gesture or Planner-requested variation", "direct_root_semantics": "append root item/composite nodes to the final explicit alternate", "composite_tiles": "preserve every item in source stack order at each x/y/z offset", "forbidden": "flatten south/east variants or composite members into one item roulette"}),
            ("wall_brush", "weighted_alignment_variants", {"source": "wall_brush.cpp WallBrush::load/draw", "alignment_first": True, "selection": "weighted choice among all positive-chance members of the resolved alignment", "zero_chance_items": "ownership/backward compatibility only; never generated", "repair": "remove prior members of the same wall family before rebuilding orientation", "transaction": "wall replacement and neighbor reorientation are idempotent in one BatchAction"}),
            ("palette", "terrain_gesture_dependencies", {"direct_area": ["Grounds - Mountains", "Grounds - Nature", "Grounds - Ornamented", "Nature - Grass", "Nature - Tiny Borders", "Snow", "Roofs"], "support_or_neighbor_context": ["Grounds - Tiny Borders", "Railings", "Stairs / Ramps / Ladders", "Walls"], "rule": "a failed isolated click does not authorize RAW fallback"}),
            ("wall_brush", "connected_orientation", {"commit": "atomic", "reorient_existing_neighbors": True, "parts": ["horizontal", "vertical", "corner", "pole", "intersection"]}),
            ("viewport", "dirty_region_contract", {"source": "operation affected_coords", "forbidden": "seed footprint only", "reason": "postprocessors mutate neighbors"}),
            ("viewport", "nonblank_chunk_replacement", {"cache_ring_chunks": 1, "minimum_cached_chunks": 96, "pan_refresh": "leading-edge prefetch at most once per frame", "replacement": "retain prior pixmap until the newly rendered TileState exists", "forbidden": ["remove cached chunk before replacement", "restart refresh timer on every key repeat"]}),
            ("viewport", "visible_first_chunk_scheduler", {"phase_1": "render current-floor chunks intersecting the visible rectangle", "phase_2": "prefetch the safety ring after the visible frame", "phase_3": "refresh projected-floor overlays independently", "replacement": "keep prior pixels until replacement exists", "forbidden": ["whole-map refresh on pan", "overlay work blocking the first visible frame"]}),
            ("viewport", "default_grid", {"visible": False, "user_toggle": True, "shortcut": "Shift+G"}),
            ("ai_studio", "indexed_otbm_preview_materialization", {"source_mode": "indexed", "tile_area_size": 256, "load": "all indexed areas from the generated preview", "deduplicate": "x/y/z", "mutation": "none before explicit approval", "verified_changed_tiles": 11252}),
            ("ai_studio", "responsive_proposal_pipeline", {"worker_thread": ["model proposal", "Planner materialization", "OTBM indexed extraction", "visual diff construction"], "ui_thread": ["bounded diff presentation", "explicit approval"], "visible_diff_limit": 500, "complete_diff_retained": True}),
            ("ai_studio", "atomic_visual_gate", {"chunk_size": 32, "rendered_pixels_persisted": False, "commit": "only after full affected-chunk PASS", "rollback": "single action", "verified": {"tiles": 12120, "chunks": 20, "status": "PASS", "undo": "restored empty document"}}),
            ("palette", "live_palette_order", {"types": ["Terrain", "Doodad", "Item", "House", "Waypoint", "Zone", "Monster", "Npc", "RAW"], "control": "dropdown"}),
            ("palette", "page_specific_composition", {"source": "palette_window.cpp", "catalog_pages": ["Terrain", "Doodad", "Item", "RAW"], "terrain_panels": ["Tileset", "Tools", "Brush Size"], "doodad_panels": ["Tileset", "Brush Thickness", "Brush Size"], "item_panels": ["Tileset", "Brush Size"], "house_panels": ["Houses", "Brushes", "Brush Size"], "metadata_only_pages": ["Waypoint", "Zone"], "creature_pages": ["Monster", "Npc"], "forbidden": "render every palette as one generic material list"}),
            ("palette", "terrain_tools_exact", {"source": "palette_common.cpp BrushToolPanel", "large_layout": {"columns": 6, "rows": 2, "cell_pixels": 45}, "row_1": ["optional_border", "eraser", "protection_zone", "no_pvp", "no_logout", "pvp_zone"], "row_2": ["normal_door", "locked_door", "magic_door", "quest_door", "hatch_window", "window"], "selection": "exclusive semantic brush", "forbidden": ["mix viewport select/move/fill into RME Tools", "disable door and zone tools as placeholders"]}),
            ("palette", "brush_size_exact", {"source": "palette_common.cpp BrushSizePanel", "shapes": ["square", "circle"], "display_sizes": [1, 2, 3, 5, 7, 9, 12], "internal_radii": [0, 1, 2, 4, 6, 8, 11], "page_local_memory": True, "pages": ["Terrain", "Doodad", "Item", "House", "RAW"]}),
            ("palette", "doodad_thickness_exact", {"source": "palette_common.cpp BrushThicknessPanel", "custom_toggle": True, "slider_range": [1, 10], "lookup": [1, 2, 3, 5, 8, 13, 23, 35, 50, 80], "default_slider": 5, "selection_scope": "one DoodadBrush gesture"}),
            ("palette", "house_page_contract", {"source": "palette_house.cpp", "town_filter": True, "house_list": "sorted names for selected town", "actions": ["Add", "Edit", "Remove"], "brushes": ["House tiles", "Select Exit"], "double_click": "edit house", "map_refresh": "reload towns and houses when active document changes", "brush_size": True}),
            ("palette", "waypoint_page_contract", {"source": "palette_waypoints.cpp", "list": "single selection editable labels", "actions": ["Add", "Remove"], "select": "center viewport and bind waypoint brush", "rename": "must remain unique", "empty_name": "remove", "minimum_otbm": 3, "brush_size": False}),
            ("palette", "zone_page_contract", {"source": "palette_zones.cpp", "list": "single selection editable labels", "actions": ["Add", "Remove", "Import", "Export"], "left_select": "bind zone brush", "right_select": "bind zone brush and center first zone position", "xml": {"root": "zones", "zone_attributes": ["name", "id"], "positions": ["x", "y", "z"]}, "minimum_otbm": 3, "brush_size": False}),
            ("palette", "monster_page_contract", {"sources": ["palette_monster.cpp", "spawn_monster.cpp"], "rme_commit": "57ee0e5b915909f207aa7a60968c8ed6e4f7f406", "controls": ["tileset", "name search", "checkable sorted monster list", "place monster", "spawn monster", "spawn time 0..3600", "spawn size", "density percentage control 0..3600", "default weight 0..100"], "selection": "monster brush uses selected row; spawn brush uses checked rows as candidates", "spawn_settings_persist": True, "brush_size_source": "spawn size", "monster_constraints": ["ground required", "non-blocking tile", "spawn coverage or automatic spawn", "protection zone rejected", "same monster is not duplicated"], "spawn_center": "ground required and one monster spawn center per tile", "spawn_area": "square side 2*radius+1", "materialization_bound": "never request more unique placements than the finite square contains"}),
            ("palette", "npc_page_contract", {"sources": ["palette_npc.cpp", "spawn_npc.cpp"], "rme_commit": "57ee0e5b915909f207aa7a60968c8ed6e4f7f406", "controls": ["tileset", "sorted npc list", "place npc", "spawn npc", "spawn time 0..3600", "spawn size"], "selection": "place selected NPC or spawn center", "spawn_settings_persist": True, "brush_size_source": "spawn size", "catalog_category": "npc is independent from creature and RAW", "npc_constraints": ["ground required", "non-blocking tile", "spawn coverage or automatic spawn", "protection zone allowed", "existing NPC is replaced"], "spawn_center": "ground required and one NPC spawn center per tile", "spawn_area": "square side 2*radius+1"}),
            ("palette", "monster_type_catalog_source", {"sources": ["monsters.cpp", "lua_parser.h", "preferences.cpp", "settings.h"], "rme_commit": "57ee0e5b915909f207aa7a60968c8ed6e4f7f406", "preference": "MONSTERS_LUA_DIRECTORY", "lua_declarations": ["Game.createMonsterType(\"name\")", "local internalMonsterName = \"name\""], "required_outfit": [".outfit", ":outfit("], "required_look": ["lookType", "lookTypeEx"], "xml_fallback": {"root": "monster", "name": "declaration name", "look_attributes": ["type", "item", "lookex", "typeex"]}, "spawn_sidecar": "instance references only; never a resolved appearance catalog", "failure_policy": "keep unresolved names disabled and request the configured Lua directory"}),
            ("palette", "npc_type_catalog_source", {"sources": ["npcs.cpp", "lua_parser.h", "preferences.cpp", "settings.h"], "rme_commit": "57ee0e5b915909f207aa7a60968c8ed6e4f7f406", "preference": "NPCS_LUA_DIRECTORY", "lua_declarations": ["Game.createNpcType(\"name\")", "local internalNpcName = \"name\""], "required_outfit": [".outfit", ":outfit("], "required_look": ["lookType", "lookTypeEx"], "xml_fallback": {"root": "npc", "name": "filename stem", "look_attributes": ["type", "item", "lookex", "typeex"]}, "spawn_sidecar": "instance references only; never a resolved appearance catalog", "failure_policy": "keep unresolved names disabled and request the configured Lua directory"}),
            ("editing", "missing_creature_type_resolution", {"sources": ["application.cpp", "monsters.cpp", "npcs.cpp"], "rme_commit": "57ee0e5b915909f207aa7a60968c8ed6e4f7f406", "trigger": "opened map references an unknown monster or NPC", "official_flow": ["offer Preferences", "configure the corresponding Lua directory", "reload missing definitions", "refresh palette"], "workspace_flow": ["File/Preferences", "persist both Lua directories", "rebuild certified catalogs", "refresh Monster and Npc palettes"], "forbidden": ["invent lookType", "infer appearance from a name", "treat spawn sidecars as type definitions"]}),
            ("editing", "semantic_palette_mutation_contract", {"sources": ["brush.cpp FlagBrush", "tile.h", "palette_house.cpp", "palette_waypoints.cpp", "palette_zones.cpp", "palette_monster.cpp", "palette_npc.cpp"], "sprite_required": False, "tile_flags": {"protection_zone": 1, "no_pvp": 4, "no_logout": 8, "pvp_zone": 16}, "metadata_tools": ["house_tiles", "house_exit", "waypoint", "zone"], "entity_tools": ["monster", "npc", "monster_spawn", "npc_spawn"], "transaction": "one gesture and one rollback boundary", "invariant": "semantic tools must not be rejected merely because no item sprite is selected", "verified": {"workspace_smoke": "PASS", "combined_flag_mask": 29}}),
            ("wall_brush", "door_tool_family_transform", {"source": "brush.cpp DoorBrush::draw", "precondition": "target tile contains a wall member owned by an official WallBrush", "resolve": ["wall family", "wall alignment", "door type", "open state"], "types": ["normal", "locked", "magic", "quest", "hatch_window", "window"], "mutation": "transform the existing wall item; never append an unrelated door ID", "fallback": "same family and alignment close match", "postprocess": "wallize when automagic", "verified": {"source_wall_id": 6251, "locked_wall_id": 6256, "workspace_smoke": "PASS"}}),
            ("doodad_brush", "custom_thickness_runtime", {"sources": ["palette_common.cpp BrushThicknessPanel", "gui.cpp GUI::SetBrushThickness", "gui.cpp FillDoodadPreviewBuffer"], "slider_lookup": [1, 2, 3, 5, 8, 13, 23, 35, 50, 80], "ratio_denominator": 100, "object_range": "floor(brush_area * selected_value / 100)", "final_count": "max(1, object_range + random(object_range))", "scope": "selected DoodadBrush gesture", "verified": {"workspace_density_override": "PASS"}}),
            ("palette", "terrain_tilesets", {"names": list(_LIVE_RME_TERRAIN_TILESETS), "source": "Canary materials plus live UI"}),
            ("document", "new_map_behavior", {"action": "create Untitled document immediately", "dialog": False}),
            ("menus", "top_level_order", {"official_rme": ["File", "Edit", "Map", "Select", "View", "Window", "Floor", "Scripts", "About"], "workspace_successor": ["File", "Edit", "Map", "Select", "View", "Window", "Floor", "AI Studio", "About"], "extension": "AI Studio replaces the empty Scripts surface by explicit product requirement", "rme_commit": "57ee0e5b915909f207aa7a60968c8ed6e4f7f406"}),
            ("menus", "edit_command_grammar", {"source": "data/menubar.xml", "rme_commit": "57ee0e5b915909f207aa7a60968c8ed6e4f7f406", "groups": [["Undo", "Redo"], ["Find Item", "Replace Items", "Find on Map"], ["Border Options", "Tools"], ["Previous Position", "Go To Position", "Jump to Brush", "Jump to Item"], ["Cut", "Copy", "Paste"]], "find_categories": ["everything", "unique", "action", "container", "writeable", "duplicates", "walls upon walls"], "scope": "all floors for Find on Map"}),
            ("menus", "map_command_grammar", {"source": "data/menubar.xml", "rme_commit": "57ee0e5b915909f207aa7a60968c8ed6e4f7f406", "commands": ["Edit Towns", "Edit Items", "Edit Monsters", "Cleanup", "Properties", "Statistics"], "source_status": {"Edit Items": "empty official handler", "Edit Monsters": "empty official handler"}, "workspace_policy": "empty official handlers remain disabled rather than reporting fake success"}),
            ("menus", "select_command_grammar", {"source": "data/menubar.xml", "rme_commit": "57ee0e5b915909f207aa7a60968c8ed6e4f7f406", "operations": ["replace items", "find item", "remove item", "remove monsters", "count monsters", "remove duplicates", "update monster spawntime"], "find_categories": ["everything", "unique", "action", "container", "writeable", "duplicates", "walls upon walls"], "selection_modes": ["compensate", "current floor", "lower floors", "visible floors"], "postprocess": ["borderize selection", "randomize selection"]}),
            ("menus", "view_window_command_grammar", {"source": "data/menubar.xml", "rme_commit": "57ee0e5b915909f207aa7a60968c8ed6e4f7f406", "view_groups": ["toolbars", "new view/fullscreen/screenshot", "zoom", "floor display", "lights/grid/highlight", "monster/npc/spawn overlays", "minimap/colors/modified/houses/pathing/tooltips/preview", "indicators"], "window_primary": ["Minimap", "Actions History", "SQLite Materials Inspector", "New Palette"], "palette_shortcuts": {"terrain": "T", "doodad": "D", "item": "I", "house": "H", "creature": "C", "npc": "N", "waypoint": "W", "zones": "Z", "raw": "R"}}),
            ("editing", "spawn_cleanup_and_spawntime", {"sources": ["main_menubar.cpp", "spawn_monster.cpp", "spawn_npc.cpp"], "rme_commit": "57ee0e5b915909f207aa7a60968c8ed6e4f7f406", "empty_spawn_cleanup": "search square radius around every center and remove centers without matching entities", "monster_spawntime_selection": {"minimum": 1, "maximum": 3600}, "transaction": "one atomic BatchAction per command"}),
            ("shortcuts", "document_and_search", {"new": "Ctrl+N", "open": "Ctrl+O", "save": "Ctrl+S", "close_document": "Ctrl+Q", "find_item": "Ctrl+F", "replace_items": "Ctrl+Shift+F"}),
            ("shortcuts", "map_navigation", {"go_to_position": "Ctrl+G", "jump_to_brush": "J", "jump_to_item": "Ctrl+J", "floor_up": "+", "floor_down": "-", "zoom_in": "Ctrl++", "zoom_out": "Ctrl+-", "zoom_reset": "Ctrl+0"}),
            ("shortcuts", "view_and_metadata", {"toggle_grid": "Shift+G", "show_all_floors": "Ctrl+W", "minimap": "M", "map_statistics": "F8", "towns": "Ctrl+T", "map_properties": "Ctrl+P"}),
            ("shortcuts", "brush_operations", {"borderize_selection": "Ctrl+B", "border_automagic": "A", "previous_brush": "P", "palette_shortcuts": {"terrain": "T", "doodad": "D", "item": "I", "house": "H", "creature": "C", "npc": "N", "waypoint": "W", "zone": "Z", "raw": "R"}}),
            ("palette", "brush_geometry_controls", {"shapes": ["square", "circle"], "sizes": [1, 2, 3, 5, 7, 9, 12], "semantic_kind_separate_from_shape": True}),
            ("palette", "preview_and_pagination", {"sprite_columns": 5, "preview_cell_pixels": 45, "pagination": True, "selection_changes_semantic_brush": True}),
            ("palette", "authoritative_tileset_selection", {"visible_control": "single RME Tileset dropdown", "terrain_tilesets": 11, "selection_order": ["BrushState compatibility signals", "authoritative PaletteManager category", "authoritative PaletteManager tileset", "material grid refresh"], "invariant": "hidden compatibility docks cannot reset the selected tileset to the first row"}),
            ("editing", "viewport_ground_paint_flow", {"input": "left click on viewport with selected semantic GroundBrush", "pipeline": ["palette entry", "BrushData with material_id", "viewport tile coordinate", "transactional dispatch_paint_brush", "ground mutation", "neighbor auto-border", "dirty chunk invalidation"], "verified": {"reference": "River.otbm", "tileset": "Grounds - Nature", "material": "terrain:grounds-nature:cave", "ground_id": 351}, "failure": "reject visibly when no active brush or certified core is not ready"}),
            ("documents", "certified_untitled_document", {"trigger": "Ctrl+N or New", "required_model": "core.world_engine.WorldModel", "ui": "Untitled-N.otbm map tab", "invariant": "an untitled viewport must own the same certified mutation bridge as an opened OTBM", "verified_edit": {"ground_id": 351, "floor": 7, "autoborder": "neighbor-aware commit"}}),
            ("editing", "rme_viewport_mouse_contract", {"left_click": "commit active brush", "right_click": ["Cut", "Copy", "Copy Position", "Paste", "Delete", "Copy Item Id", "Copy Item Name", "Select RAW", "Select Groundbrush", "Properties", "Browse Field"], "middle_drag": "pan"}),
            ("viewport", "successor_floor_keyboard_extension", {"workspace_extension": {"floor_up": ["+", "PageUp"], "floor_down": ["-", "PageDown"]}, "official_menu_xml": "no floor hotkeys declared", "range": [0, 15], "verified_transition": "7 -> 6 -> 7"}),
            ("render", "appearance_layer_composition", {"source": "Canary map_drawer.cpp BlitItem", "order": "resolve every appearance layer at one anchor, then apply draw height to the following stack item", "pattern": "x/y/z and animation frame are resolved before layer composition"}),
            ("render", "otbm_stack_order", {"source": "Canary map_drawer.cpp DrawTile", "sequence": ["ground", "tile.items in stored order"], "forbidden": "resort loaded stacks by broad visual layer", "reason": "ItemType insertion rules already established overlap order"}),
            ("viewport", "incremental_action_redraw", {"source": "Canary Editor Action/BatchAction", "update": "patch affected tile states in cached chunks", "forbidden": "reload a complete 64x64 chunk per dirty coordinate", "measured_reference": {"map": "River.otbm", "full_scene_paint_ms": 29.69}}),
            ("otbm", "known_empty_region_cache", {"rule": "an absent tile inside an already loaded rectangle is a known empty coordinate", "forbidden": "reparse source OTBM for every empty neighbor lookup", "consumer": ["BorderSolver", "WallBrush", "DoodadBrush", "viewport"]}),
            ("planner", "krailos_compact_biome", {"source": "Krailos.otbm full-file abstract scan plus z7 spawn sidecar", "reference_tiles": 94471, "ground_families": ["sea", "krailos dirt", "grass (krailos)", "rock soil", "krailos orange", "krailos yellow", "krailos purple", "mountain"], "nature_families": ["krailos rocks", "krailos mountains", "jungle fern"], "conditional_families": ["krailos hut", "krailos roof", "krailos roof - end", "krailos structure1", "krailos structure2", "krailos structure3", "krailos structure4", "krailos spikes1", "krailos spikes2", "krailos blood", "krailos fence", "krailos tanned skin", "krailos thing"], "architecture": {"temple_entrance": "open, three tiles, no door", "temple_decorations": ["krailos banner", "krailos pot", "krailos totem pole"], "protection_zone": "interior including player spawn", "landmarks": "place only on compatible terrain and move an invalid requested anchor to the nearest connected valid tile"}, "material_safety": {"explicit_terrain_ground_is_authoritative": True, "border_items_never_own_ground_slot": True, "forbidden_legacy_border_ground_ids": [4535, 4536, 4537, 4538]}, "z7_creature_prevalence": ["Ogre Brute", "Clomp", "Ogre Shaman", "Ogre Savage"], "generation_policy": "learn material ratios, family grammar and connectivity only; always create original geometry"}),
            ("planner", "ecological_distribution_budget", {"sources": ["official Canary materials/brushs", "DoodadBrush weighted alternatives", "Krailos.otbm abstract family metrics"], "input": "semantic family token plus habitat mask", "habitats": ["coast", "dry", "oasis", "rocky"], "blockers": ["roads", "structures", "gameplay anchors", "spawn safety buffers"], "selection": "deterministic ranked candidates constrained by family quota and minimum spacing", "materialization": "resolve only through official palette tokens and positive-chance brush members", "forbidden": ["model supplied server IDs", "name inferred item safety", "uniform global scatter"]}),
            ("planner", "ecological_density_budget", {"sources": ["Krailos.otbm abstract family ratios", "official DoodadBrush thickness semantics"], "rule": "derive a bounded total decoration budget from buildable habitat area, then divide it by explicit family weights", "family_constraints": ["maximum share", "minimum spacing", "maximum cluster size", "compatible habitats"], "protected_space": "preserve traversal, structure entrances, coastline readability and spawn safety", "determinism": "same semantic plan and seed produce the same candidate ordering"}),
            ("critic", "ecological_repetition_critic", {"input": "materialized ecological placements grouped by semantic family and official brush token", "checks": ["maximum family share", "same-token eight-neighbor connected component cap", "minimum spacing"], "repair": "remove the lowest-priority violating placements and recompute ratios after every removal", "failure_policy": "block export when deterministic repair cannot satisfy every budget", "forbidden": ["silently accept dominant families", "replace a rejected member with an uncertified ID", "visual-only warning without repair"]}),
            ("editing", "semantic_brush_undraw", {"source": ["ground_brush.cpp", "wall_brush.cpp", "doodad_brush.cpp", "raw_brush.cpp"], "ground": "remove only ground owned by active GroundBrush", "wall_doodad_border": "remove only items owned by active family", "raw": "remove only selected item id", "preserve": ["unrelated stack items", "flags", "house", "spawn", "creature", "zone", "attributes"], "transactional": True}),
            ("editing", "flag_brush_undraw_exact", {"source": ["brush.cpp FlagBrush::undraw", "tile.h TileStateFlag"], "flags": {"protection_zone": 1, "no_pvp": 4, "no_logout": 8, "pvp_zone": 16}, "erase": "clear only the active flag bit", "preserve": ["all other flag bits", "ground", "item stack", "house", "spawn", "creature", "zone"], "transactional": True, "verified": {"input_mask": 29, "erase_protection_zone_result": 28, "workspace_smoke": "PASS"}}),
            ("wall_brush", "door_brush_undraw_exact", {"source": ["brush.cpp DoorBrush::undraw", "official materials/brushs/walls.xml"], "erase": "replace the door with a positive-chance normal wall member", "context": ["same WallBrush family", "same horizontal/vertical alignment"], "forbidden": ["delete the complete wall", "pick a wall from another family"], "verified": {"locked_door": 6256, "restored_horizontal_wall": 1295, "workspace_smoke": "PASS"}}),
            ("palette", "agent_palette_live_control_bridge", {"source": ["palette_window.cpp", "palette_common.cpp", "live workspace comparison"], "order": ["Terrain", "Doodad", "Item", "House", "Waypoint", "Zone", "Monster", "Npc", "RAW"], "terrain_tools": 12, "tool_grid": [6, 2], "brush_sizes": [1, 2, 3, 5, 7, 9, 12], "selection": "sprite selection activates the brush tool", "callbacks": ["semantic tool", "brush size", "brush shape", "doodad thickness"], "verified": {"agent_qt_smoke": "PASS"}}),
            ("editing", "context_groundbrush_resolution", {"action": "Select Groundbrush", "lookup": "find GroundBrush whose ground_ids own clicked ground id", "forbidden": "select clicked ground as a RAW brush substitute"}),
            ("editing", "field_context_menu_contract", {"source": "map_display.cpp", "state": {"cut_copy_delete": "selection required", "paste": "editor clipboard required", "copy_item_id_name": "exactly one resolved stack item", "properties": "editable tile or item metadata required"}, "dynamic_selectors": ["RAW", "ground", "wall", "carpet", "table", "doodad", "door", "house"], "selector_visibility": "show only when the clicked stack has a real owning brush or house relationship", "browse_field": "inspect complete ordered stack without mutation", "mutation": "reuse transactional command handlers"}),
            ("editing", "viewport_mouse_precedence", {"left_click": "commit active brush", "right_click": "field context menu", "ctrl_right_drag": "semantic Brush::undraw successor shortcut", "ctrl_left_drag": "paint; never implicit erase", "precedence": ["official source contract", "verified live behavior", "successor extension"]}),
            ("editing", "gesture_history", {"paint_gesture": "one BatchAction", "postprocessors_in_same_action": True, "undo_restores_clean_state_when_at_saved_revision": True, "reference_maps_never_auto_saved": True}),
            ("editing", "tool_surface", {"tools": ["brush", "border", "erase", "select", "move", "fill", "replace", "protection_zone", "no_pvp", "pvp", "logout", "locked", "magic", "quest", "hatch", "normal_window"]}),
            ("window", "default_docks", {"left": ["Palette"], "right": [], "hidden_by_default": ["Minimap", "Action History", "Properties"], "workspace_extension": {"right": ["AI Assistant"]}}),
            ("window", "screen_geometry_contract", {"startup": "fit current available work area", "maximized": True, "restore": "dock state only", "forbidden": "restore stale monitor rectangle before maximization"}),
            ("viewport", "floor_render_contract", {"floors": {"min": 0, "max": 15, "surface": 7}, "projection": "orthogonal tile plane with sprite elevation/offset draw", "show_all_floors_default": True}),
            ("document", "open_reference_behavior", {"otbm_required": True, "optional_sidecars": ["house", "zone", "spawn", "npc"], "missing_optional_sidecars": "warning only", "render_after_load": "visible chunks"}),
            ("runtime", "progressive_certified_core", {
                "rme_parity": "editor controls become mutable only after materials and item types are ready",
                "stages": ["show workspace shell", "reserve certified core namespace", "warm official appearances and planner database in background", "publish certified adapter atomically", "enable document and brush operations", "decode palette previews incrementally"],
                "warmup_policy": "fail closed with visible status; never downgrade to fallback core",
                "ui_thread": ["window construction", "first paint", "event processing", "incremental palette previews"],
                "worker_thread": ["certified core imports", "planner knowledge services", "appearance metadata warmup"],
                "measured_2026_07_16_ms": {"engine_proxy": 34.4, "first_interactive": 3603.0, "certified_ready": 10381.5},
            }),
        )
        db.executemany(
            "INSERT OR REPLACE INTO editor_runtime_observations(domain, rule_key, behavior_json, provenance, confidence) "
            "VALUES (?, ?, ?, 'Canary Map Editor v4 live observation + official source', 1.0)",
            ((domain, key, json.dumps(value, sort_keys=True)) for domain, key, value in rows),
        )

    @staticmethod
    def _sources(db: sqlite3.Connection, root: Path) -> None:
        from core.world_generator.world_town_scanner import resolve_world_path

        candidates = [
            root / "assets" / "appearances-ee339aff5b3cb38289287ff25cec261d8d2790e6e146938d4dfd9f138b065980.dat",
            root / "assets" / "catalog-content.json",
            root / "APPEARANCE_RENDER_CATALOG.json",
            root / "APPEARANCE_ITEM_CATALOG.json",
        ]
        try:
            world_path = resolve_world_path(root)
            candidates.append(world_path)
            candidates.extend(
                world_path.with_name(f"{world_path.stem}-{kind}.xml")
                for kind in ("house", "monster", "npc", "zones")
            )
        except FileNotFoundError:
            pass
        candidates.extend(path for path in resolve_materials_dir(root).rglob("*") if path.is_file())
        reference_root = root / "projects" / "Mapas Referencia"
        candidates.extend(path for path in reference_root.rglob("*") if path.is_file())
        rows = []
        for path in candidates:
            if path.is_file():
                try:
                    rows.append((path.name, str(path), path.stat().st_size, _sha256(path), ""))
                except OSError as exc:
                    rows.append((path.name, str(path), 0, "", f"{type(exc).__name__}: {exc}"))
        db.executemany(
            "INSERT INTO source_files(name, path, bytes, sha256, read_error) VALUES (?, ?, ?, ?, ?)",
            rows,
        )

    @staticmethod
    def _reference_map_corpus(db: sqlite3.Connection, root: Path) -> None:
        from core.world_generator.reference_map_corpus import ReferenceMapCorpusAnalyzer
        from core.world_generator.reference_map_scanner import ReferenceMapScanner

        automap_colors = {
            int(item_id): int(color)
            for item_id, color in db.execute(
                "SELECT i.item_id, af.automap_color FROM items i "
                "JOIN appearance_flags af ON af.appearance_id=i.appearance_id "
                "WHERE af.automap_color IS NOT NULL AND af.automap_color != 0"
            )
        }
        report = ReferenceMapCorpusAnalyzer(root, automap_colors=automap_colors).write()
        if report.get("status") != "PASS":
            raise ValueError("Reference map corpus analysis did not pass")
        for profile in report["profiles"]:
            dimensions = profile["dimensions"]
            town = profile["town"]
            cursor = db.execute(
                "INSERT INTO reference_maps(name, source, source_sha256, bytes, tile_count, width, height, "
                "min_floor, max_floor, town_name, town_x, town_y, town_z, profile_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    profile["name"], profile["source"], profile["source_sha256"], profile["bytes"],
                    profile["tile_count"], dimensions["width"], dimensions["height"],
                    dimensions["min_floor"], dimensions["max_floor"], town["name"], town["x"],
                    town["y"], town["z"], json.dumps(profile, sort_keys=True),
                ),
            )
            reference_id = cursor.lastrowid
            PlannerKnowledgeDatabase._archive_reference_sources(db, root, reference_id, profile)
            scanner_report = ReferenceMapScanner.report_from_profile(profile)
            db.execute(
                "INSERT INTO reference_scan_reports(reference_id, scanner_version, used_floors_json, "
                "report_json) VALUES (?, ?, ?, ?)",
                (
                    reference_id,
                    scanner_report["scanner_version"],
                    json.dumps(scanner_report["used_floors"]),
                    json.dumps(scanner_report, sort_keys=True),
                ),
            )
            db.executemany(
                "INSERT INTO reference_material_usage(reference_id, item_id, usage_count, per_tile, "
                "categories_json, brushes_json) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    (
                        reference_id, material["item_id"], material["count"], material["per_tile"],
                        json.dumps(material["categories"], sort_keys=True),
                        json.dumps(material["brushes"], sort_keys=True),
                    )
                    for material in profile["material_usage"]
                ),
            )
            db.executemany(
                "INSERT INTO reference_brush_usage(reference_id, kind, name, usage_count) VALUES (?, ?, ?, ?)",
                (
                    (reference_id, brush["kind"], brush["name"], brush["count"])
                    for brush in profile["brush_usage"]
                ),
            )
            db.executemany(
                "INSERT INTO reference_ground_transitions(reference_id, ground_a, ground_b, edge_count) "
                "VALUES (?, ?, ?, ?)",
                (
                    (reference_id, row["ground_a"], row["ground_b"], row["edges"])
                    for row in profile["ground_transitions"]
                ),
            )
            db.executemany(
                "INSERT INTO reference_floor_profiles(reference_id, floor, tile_count, width, height, "
                "item_density, ground_diversity, profile_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    (
                        reference_id, floor["floor"], floor["tile_count"], floor["width"], floor["height"],
                        floor["item_density"], floor["ground_diversity"], json.dumps(floor, sort_keys=True),
                    )
                    for floor in profile["floor_profiles"]
                ),
            )
            db.executemany(
                "INSERT INTO reference_floor_material_usage(reference_id, floor, item_id, usage_count, "
                "per_tile, categories_json, brushes_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    (
                        reference_id,
                        floor["floor"],
                        material["item_id"],
                        material["count"],
                        material["per_tile"],
                        json.dumps(material["categories"], sort_keys=True),
                        json.dumps(material["brushes"], sort_keys=True),
                    )
                    for floor in profile["floor_profiles"]
                    for material in floor["material_usage"]
                ),
            )
            db.executemany(
                "INSERT INTO reference_border_mixes(reference_id, floor, ground_id, border_id, usage_count) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    (
                        reference_id, mix["floor"], mix["ground_id"], mix["border_id"], mix["count"]
                    )
                    for mix in profile["border_mixes"]
                ),
            )
            color_profiles = [(-1, profile["minimap_color_profile"])] + [
                (floor["floor"], floor["minimap_color_profile"])
                for floor in profile["floor_profiles"]
            ]
            db.executemany(
                "INSERT INTO reference_minimap_colors(reference_id, floor, color, red, green, blue, "
                "tile_count, tile_ratio) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    (
                        reference_id, floor, row["color"], row["rgb"][0], row["rgb"][1], row["rgb"][2],
                        row["tile_count"], row["tile_ratio"],
                    )
                    for floor, color_profile in color_profiles
                    for row in color_profile["colors"]
                ),
            )
            db.executemany(
                "INSERT INTO reference_minimap_color_materials(reference_id, floor, color, item_id, "
                "selection_role, tile_count) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    (
                        reference_id, floor, row["color"], row["item_id"],
                        row["selection_role"], row["tile_count"],
                    )
                    for floor, color_profile in color_profiles
                    for row in color_profile["material_sources"]
                ),
            )
        db.executemany(
            "INSERT INTO reference_archetypes(name, source_count, metrics_json, generation_rules_json) "
            "VALUES (?, ?, ?, ?)",
            (
                (
                    archetype["name"], archetype["source_count"],
                    json.dumps({
                        "dimensions": archetype["dimensions"],
                        "category_mix": archetype["category_mix"],
                    }, sort_keys=True),
                    json.dumps(archetype["generation_rules"], sort_keys=True),
                )
                for archetype in report["archetypes"]
            ),
        )

    @staticmethod
    def _archive_reference_sources(
        db: sqlite3.Connection,
        root: Path,
        reference_id: int,
        profile: dict[str, Any],
    ) -> None:
        map_path = root / profile["source"]
        candidates = [("otbm", map_path)]
        candidates.extend(
            (f"{kind}_xml", map_path.with_name(f"{map_path.stem}-{kind}.xml"))
            for kind in ("house", "monster", "npc", "zones")
        )
        rows = []
        for kind, path in candidates:
            if not path.is_file():
                continue
            payload = path.read_bytes()
            rows.append((
                reference_id,
                kind,
                path.name,
                hashlib.sha256(payload).hexdigest(),
                len(payload),
                "zlib-9",
                "analysis_only",
                sqlite3.Binary(zlib.compress(payload, level=9)),
            ))
        db.executemany(
            "INSERT INTO reference_source_archives(reference_id, artifact_kind, filename, sha256, "
            "original_bytes, compression, access_scope, payload) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )

    @staticmethod
    def _world_town_scans(db: sqlite3.Connection, root: Path) -> None:
        from core.world_generator.world_town_scanner import WorldTownScanner

        report = WorldTownScanner(root).scan_cached()
        if report.get("status") != "PASS":
            raise ValueError("World town scanner did not pass")
        town_ids = {name: town_id for town_id, name in db.execute("SELECT town_id, name FROM towns")}
        for town_name, town in report["towns"].items():
            town_id = town_ids.get(town_name)
            if town_id is None:
                continue
            db.execute(
                "INSERT INTO world_town_scan_reports(town_id, town_name, scanner_version, world_sha256, "
                "radius, floors_json, report_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    town_id, town_name, report["scanner_version"], report["world_sha256"], report["radius"],
                    json.dumps(report["floors_examined"]), json.dumps(town, sort_keys=True),
                ),
            )
            db.executemany(
                "INSERT INTO world_town_floor_material_usage(town_id, floor, item_id, usage_count, per_tile, "
                "categories_json, brushes_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    (
                        town_id, int(raw_floor), material["item_id"], material["count"], material["per_tile"],
                        json.dumps(material["categories"], sort_keys=True),
                        json.dumps(material["brushes"], sort_keys=True),
                    )
                    for raw_floor, floor in town["floors"].items()
                    for material in floor["materials"]
                ),
            )
            db.executemany(
                "INSERT INTO world_town_scanned_structures(town_id, town_name, kind, min_floor, max_floor, "
                "width, height, evidence_count, confidence, details_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    (
                        town_id, town_name, structure["kind"], structure.get("min_floor"),
                        structure.get("max_floor"), structure.get("width"), structure.get("height"),
                        structure.get("evidence_count", 0), structure.get("confidence", 0.0),
                        json.dumps(structure, sort_keys=True),
                    )
                    for structure in town["structures"]
                ),
            )

    @staticmethod
    def _quest_script_knowledge(db: sqlite3.Connection, root: Path) -> None:
        from core.world_generator.quest_script_scanner import QuestScriptScanner

        scanner = QuestScriptScanner(root)
        report = scanner.scan_cached()
        if report.get("status") != "PASS":
            raise ValueError("Quest script scanner did not pass")
        source_root = Path(report["source_root"])
        for file_row in report["files"]:
            path = source_root / Path(file_row["relative_path"])
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != file_row["sha256"]:
                raise ValueError(f"Quest source changed during database build: {path}")
            cursor = db.execute(
                "INSERT INTO quest_script_files(relative_path, scope, package_name, language, sha256, bytes, "
                "constructors_json, callbacks_json, api_calls_json, dependencies_json, actors_json, metrics_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    file_row["relative_path"], file_row["scope"], file_row["package"], file_row["language"],
                    file_row["sha256"], file_row["bytes"], json.dumps(file_row["constructors"]),
                    json.dumps(file_row["callbacks"]), json.dumps(file_row["api_calls"]),
                    json.dumps(file_row["dependencies"]), json.dumps(file_row["actors"]),
                    json.dumps(file_row["metrics"], sort_keys=True),
                ),
            )
            file_id = int(cursor.lastrowid)
            db.execute(
                "INSERT INTO quest_script_archives(file_id, compression, access_scope, payload) "
                "VALUES (?, 'zlib-9', 'analysis_only', ?)",
                (file_id, sqlite3.Binary(zlib.compress(raw, level=9))),
            )
            db.executemany(
                "INSERT INTO quest_identifiers(file_id, identifier_kind, identifier_value) VALUES (?, ?, ?)",
                ((file_id, row["kind"], row["value"]) for row in file_row["identifiers"]),
            )
            db.executemany(
                "INSERT INTO quest_storage_transitions(file_id, storage_ref, operation, value_expr) "
                "VALUES (?, ?, ?, ?)",
                (
                    (file_id, row["storage"], row["operation"], row["value"])
                    for row in file_row["storage_transitions"]
                ),
            )
            db.executemany(
                "INSERT INTO quest_rewards(file_id, reward_kind, operation, item_expr, amount_expr) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    (file_id, row["kind"], row["operation"], row["item"], row["amount"])
                    for row in file_row["rewards"]
                ),
            )
            db.executemany(
                "INSERT INTO quest_movements(file_id, movement_kind, expression) VALUES (?, ?, ?)",
                ((file_id, row["kind"], row["expression"]) for row in file_row["movements"]),
            )
        db.executemany(
            "INSERT INTO quest_packages(name, scope, script_count, language, summary_json, grammar_json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                (
                    package["name"], package["scope"], package["script_count"], package["language"],
                    json.dumps({
                        "constructors": package["constructors"],
                        "callbacks": package["callbacks"],
                        "identifier_kinds": package["identifier_kinds"],
                        "storage_count": package["storage_count"],
                        "reward_kinds": package["reward_kinds"],
                        "movement_kinds": package["movement_kinds"],
                    }, sort_keys=True),
                    json.dumps(package["generation_grammar"]),
                )
                for package in report["packages"]
            ),
        )

    @staticmethod
    def _appearances(db: sqlite3.Connection, root: Path) -> None:
        render = _read_json(root / "APPEARANCE_RENDER_CATALOG.json", {})
        items = _read_json(root / "APPEARANCE_ITEM_CATALOG.json", {})
        appearances_path = root / "assets" / "appearances-ee339aff5b3cb38289287ff25cec261d8d2790e6e146938d4dfd9f138b065980.dat"
        extractor = AppearanceDatFlagExtractor(appearances_path) if appearances_path.is_file() else None
        appearance_rows = []
        flag_rows = []
        sprite_rows = []
        for raw_id, payload in render.items():
            if not str(raw_id).isdigit() or not isinstance(payload, dict):
                continue
            appearance_id = int(raw_id)
            known = {
                "id", "width", "height", "layers", "pattern_width", "pattern_height",
                "pattern_depth", "animation_phases", "sprite_count", "sprite_ids",
            }
            extra = {key: value for key, value in payload.items() if key not in known}
            appearance_rows.append((
                appearance_id, int(payload.get("width", 1)), int(payload.get("height", 1)),
                int(payload.get("layers", 1)), int(payload.get("pattern_width", 1)),
                int(payload.get("pattern_height", 1)), int(payload.get("pattern_depth", 1)),
                int(payload.get("animation_phases", 1)), int(payload.get("sprite_count", 0)),
                json.dumps(extra, sort_keys=True),
            ))
            if extractor is not None:
                flags = extractor.extract_from_catalog_entry(appearance_id, payload)
                sprite_info = extractor.extract_sprite_info_from_catalog_entry(appearance_id, payload)
                flag_rows.append((
                    appearance_id,
                    flags.flags.get("automap_color"),
                    json.dumps(flags.flags, sort_keys=True),
                    json.dumps(sprite_info.animation.to_dict(), sort_keys=True),
                    json.dumps(list(flags.exact_fields)),
                ))
            sprite_rows.extend(
                (appearance_id, index, int(sprite_id))
                for index, sprite_id in enumerate(payload.get("sprite_ids", ()))
            )
        db.executemany(
            "INSERT INTO appearances VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", appearance_rows,
        )
        db.executemany("INSERT INTO appearance_flags VALUES (?, ?, ?, ?, ?)", flag_rows)
        db.executemany("INSERT INTO appearance_sprites VALUES (?, ?, ?)", sprite_rows)

        item_rows, role_rows, tileset_rows = [], [], []
        for raw_id, payload in items.items():
            if not str(raw_id).isdigit() or not isinstance(payload, dict):
                continue
            item_id = int(raw_id)
            appearance_id = _resolve_appearance_id(item_id, payload, render)
            item_rows.append((
                item_id, appearance_id, payload.get("client_id") or appearance_id,
                str(payload.get("name", "")), str(payload.get("server_type", "")),
                int(bool(payload.get("appearance_present"))),
                json.dumps(payload.get("server_attributes", {}), sort_keys=True),
                json.dumps(payload.get("source_priority", []), sort_keys=True),
            ))
            role_rows.extend((item_id, str(role)) for role in payload.get("roles", ()))
            tileset_rows.extend(
                (item_id, str(row.get("tileset", "")), str(row.get("file", "")))
                for row in payload.get("tilesets", ()) if isinstance(row, dict)
            )
        db.executemany("INSERT INTO items VALUES (?, ?, ?, ?, ?, ?, ?, ?)", item_rows)
        db.executemany("INSERT OR IGNORE INTO item_roles VALUES (?, ?)", role_rows)
        db.executemany("INSERT OR IGNORE INTO item_tilesets VALUES (?, ?, ?)", tileset_rows)

    @staticmethod
    def _materials(db: sqlite3.Connection, root: Path) -> None:
        catalog = load_material_catalog(root)
        classification = classify_items(catalog)
        brush_rows, member_rows = [], []
        for key, brush in catalog["brushes"].items():
            brush_rows.append((key, brush["name"], brush["type"], brush.get("lookid"), brush["source"]))
            member_rows.extend((key, int(item_id), "item") for item_id in brush.get("items", ()))
            member_rows.extend((key, int(border_id), "border") for border_id in brush.get("borders", ()))
        db.executemany("INSERT INTO brushes VALUES (?, ?, ?, ?, ?)", brush_rows)
        db.executemany("INSERT OR IGNORE INTO brush_members VALUES (?, ?, ?)", member_rows)
        PlannerKnowledgeDatabase._complete_canary_brushes(db, root)
        PlannerKnowledgeDatabase._parsed_brush_grammar(db, root)
        for category, item_ids in classification.get("categories", {}).items():
            db.executemany(
                "INSERT OR IGNORE INTO material_categories VALUES (?, ?)",
                ((str(category), int(item_id)) for item_id in item_ids),
            )
        for border_id, border in catalog.get("borders", {}).items():
            db.execute(
                "INSERT INTO borders(border_id, definition_json) VALUES (?, ?)",
                (int(border_id), json.dumps(border, sort_keys=True)),
            )
        for name, payload in catalog.get("tilesets", {}).items():
            db.execute(
                "INSERT INTO tilesets(name, definition_json) VALUES (?, ?)",
                (str(name), json.dumps(payload, sort_keys=True)),
            )

    @staticmethod
    def _parsed_brush_grammar(
        db: sqlite3.Connection, root: Path, *, replace: bool = False
    ) -> tuple[int, int]:
        brush_root = resolve_materials_dir(root) / "brushs"
        parsed = BrushMaterialLoader(brush_root).load()
        if replace:
            old_keys = [row[0] for row in db.execute(
                "SELECT brush_key FROM parsed_brush_grammar"
            ).fetchall()]
            db.executemany("DELETE FROM brush_members WHERE brush_key=?", ((key,) for key in old_keys))
            db.execute("DELETE FROM parsed_brush_grammar")
        source_hashes: dict[str, str] = {}
        member_count = 0
        for brush in parsed.values():
            identity = f"{brush.brush_type.casefold()}\0{brush.name.casefold()}".encode("utf-8")
            brush_key = f"parsed:{hashlib.sha256(identity).hexdigest()[:24]}"
            source = str(Path(brush.source_file).resolve(strict=False))
            if source not in source_hashes:
                try:
                    source_hashes[source] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
                except OSError:
                    source_hashes[source] = ""
            grammar_json = json.dumps(brush.grammar, sort_keys=True, separators=(",", ":"))
            grammar_hash = hashlib.sha256(grammar_json.encode("utf-8")).hexdigest()
            db.execute(
                "INSERT INTO brushes(brush_key,name,type,look_id,source) VALUES (?,?,?,?,?) "
                "ON CONFLICT(brush_key) DO UPDATE SET name=excluded.name,type=excluded.type," 
                "look_id=excluded.look_id,source=excluded.source",
                (brush_key, brush.name, brush.brush_type, brush.look_id, source),
            )
            db.executemany(
                "INSERT OR IGNORE INTO brush_members(brush_key,member_id,role) VALUES (?,?,'item')",
                ((brush_key, int(item_id)) for item_id in brush.item_ids),
            )
            member_count += len(brush.item_ids)
            db.execute(
                "INSERT INTO parsed_brush_grammar(brush_key,name,type,look_id,server_look_id,member_count," 
                "grammar_json,grammar_sha256,source_file,source_sha256) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    brush_key, brush.name, brush.brush_type, brush.look_id, brush.server_look_id,
                    len(brush.item_ids), grammar_json, grammar_hash, source, source_hashes[source],
                ),
            )
        return len(parsed), member_count

    @staticmethod
    def _complete_canary_brushes(db: sqlite3.Connection, root: Path) -> None:
        brush_root = (
            root / "projects" / "canary-extracted" / "canary-map-editor-v4.0-windows"
            / "data" / "materials" / "brushs"
        )
        for path in sorted(brush_root.glob("*.xml")):
            try:
                document = ET.parse(path).getroot()
            except ET.ParseError:
                continue
            for index, element in enumerate(document.iter("brush")):
                name = element.attrib.get("name", "").strip()
                if not name:
                    continue
                brush_type = element.attrib.get("type", "").strip().lower() or "raw"
                key = f"canary:{path.name}:{index}:{name.lower()}"
                look_id = element.attrib.get("lookid")
                db.execute(
                    "INSERT OR IGNORE INTO brushes VALUES (?, ?, ?, ?, ?)",
                    (key, name, brush_type, int(look_id) if str(look_id).isdigit() else None, str(path)),
                )
                item_ids = {
                    item_id
                    for item in element.iter("item")
                    for item_id in expand_item_ids(item)
                }
                db.executemany(
                    "INSERT OR IGNORE INTO brush_members VALUES (?, ?, 'item')",
                    ((key, int(item_id)) for item_id in item_ids),
                )

    @staticmethod
    def _canary_material_archive(db: sqlite3.Connection, root: Path) -> None:
        materials = resolve_materials_dir(root)
        for path in sorted(materials.rglob("*.xml")):
            parse_error = ""
            try:
                content = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                content = ""
                parse_error = f"{type(exc).__name__}: {exc}"
            cursor = db.execute(
                "INSERT INTO material_documents(path, category, sha256, content, parse_error) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    str(path), path.parent.name, hashlib.sha256(content.encode()).hexdigest(),
                    content, parse_error,
                ),
            )
            document_id = int(cursor.lastrowid)
            try:
                xml_root = ET.fromstring(content)
            except ET.ParseError as exc:
                db.execute(
                    "UPDATE material_documents SET parse_error=? WHERE id=?",
                    (f"ParseError: {exc}", document_id),
                )
                continue
            _insert_xml_node(db, document_id, None, 0, xml_root)
            db.executemany(
                "INSERT OR IGNORE INTO material_includes(document_id, included_path) VALUES (?, ?)",
                (
                    (document_id, str(include.attrib.get("file", "")))
                    for include in xml_root.iter("include")
                ),
            )
        source_path = materials / "materials.db"
        if source_path.is_file():
            PlannerKnowledgeDatabase._copy_materials_database(db, source_path)

    @staticmethod
    def _copy_materials_database(db: sqlite3.Connection, source_path: Path) -> None:
        live = sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True, timeout=5.0)
        source = sqlite3.connect(":memory:")
        try:
            live.backup(source)
            tables = [
                row[0]
                for row in source.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' "
                    "AND name NOT LIKE 'sqlite_%' ORDER BY name"
                )
            ]
            for table in tables:
                quoted_table = _quote_identifier(table)
                columns = source.execute(f"PRAGMA table_info({quoted_table})").fetchall()
                target = f"rme_{table}"
                quoted_target = _quote_identifier(target)
                definitions = ", ".join(
                    f"{_quote_identifier(column[1])} {column[2] or 'BLOB'}" for column in columns
                )
                db.execute(f"CREATE TABLE {quoted_target} ({definitions})")
                rows = source.execute(f"SELECT * FROM {quoted_table}").fetchall()
                if rows:
                    placeholders = ",".join("?" for _ in columns)
                    db.executemany(f"INSERT INTO {quoted_target} VALUES ({placeholders})", rows)
                db.execute(
                    "INSERT INTO material_db_inventory(source_table, target_table, row_count, columns_json) "
                    "VALUES (?, ?, ?, ?)",
                    (table, target, len(rows), json.dumps([column[1] for column in columns])),
                )
            db.executescript(_PLANNER_MATERIAL_VIEWS)
        finally:
            source.close()
            live.close()

    @staticmethod
    def _towns(db: sqlite3.Connection, root: Path) -> None:
        from core.world_generator.world_town_scanner import WorldTownScanner

        anchors = WorldTownScanner(root).town_anchors()
        db.executemany(
            "INSERT INTO towns(town_id, name, anchor_x, anchor_y, anchor_z, source) VALUES (?, ?, ?, ?, ?, ?)",
            (
                (row.get("id"), row["name"], row.get("x"), row.get("y"), row.get("z"), "world.otbm:TOWN")
                for row in anchors
            ),
        )

    @staticmethod
    def _visual_observations(db: sqlite3.Connection, root: Path) -> None:
        cache = _read_json(root / "exports" / "planner_visual_memory" / "VISUAL_MEMORY_CACHE.json", {})
        towns = {row[0].lower().replace("'", "").replace(" ", "_"): row[1] for row in db.execute("SELECT name, town_id FROM towns")}
        rows = []
        color_counts: Counter[tuple[str, int, int]] = Counter()
        for entry in cache.get("entries", ()):
            tags = [str(tag) for tag in entry.get("tags", ())]
            zone = next((tag[5:] for tag in tags if tag.startswith("zone_")), None)
            floor = next((int(tag[6:]) for tag in tags if tag.startswith("floor_")), None)
            if zone is None:
                continue
            metrics = entry.get("metrics", {})
            rows.append((
                towns.get(zone), zone, floor, float(entry.get("confidence", 0.0)),
                float(metrics.get("entropy", 0.0)), float(metrics.get("edge_density", 0.0)),
                float(metrics.get("water_ratio", 0.0)), float(metrics.get("nature_ratio", 0.0)),
                float(metrics.get("dark_ratio", 0.0)), json.dumps(tags), entry.get("source_kind", ""),
            ))
            for color, count in metrics.get("minimap_colors", {}).items():
                color_counts[(zone, floor, int(color))] += int(count)
        db.executemany("INSERT INTO town_floor_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", rows)
        db.executemany(
            "INSERT INTO town_minimap_colors VALUES (?, ?, ?, ?)",
            ((zone, floor, color, count) for (zone, floor, color), count in color_counts.items()),
        )

    @staticmethod
    def _structural_patterns(db: sqlite3.Connection, root: Path) -> None:
        candidates = {
            "house": "WG18HAR_BUILDING_FOOTPRINT_LIBRARY.json",
            "road": "WG18HAR_ROAD_TOPOLOGY_LIBRARY.json",
            "bridge": "WG18HAR_WATER_DOCK_LIBRARY.json",
            "boat": "WG18HAR_WATER_DOCK_LIBRARY.json",
            "nature": "WG18HAR_ECOSYSTEM_MATERIAL_LIBRARY.json",
        }
        for kind, filename in candidates.items():
            path = root / "exports" / filename
            if not path.is_file():
                continue
            payload = _read_json(path, {})
            db.execute(
                "INSERT INTO structural_patterns(kind, name, floors, width, height, metrics_json, source, confidence) "
                "VALUES (?, ?, NULL, NULL, NULL, ?, ?, ?)",
                (kind, path.stem, json.dumps(payload, sort_keys=True), str(path), 0.8),
            )

    @staticmethod
    def _town_topology(db: sqlite3.Connection, root: Path) -> None:
        path = root / "exports" / "planner_knowledge" / "WORLD_TOWN_TOPOLOGY.json"
        payload = _read_json(path, {})
        town_ids = {name: town_id for town_id, name in db.execute("SELECT town_id, name FROM towns")}
        for town, profile in payload.get("towns", {}).items():
            town_id = town_ids.get(town)
            for raw_floor, floor in profile.get("floors", {}).items():
                db.execute(
                    "INSERT INTO town_semantic_features(town_id, town_name, floor, role_counts_json, "
                    "feature_counts_json, footprint_count) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        town_id, town, int(raw_floor), json.dumps(floor.get("role_counts", {}), sort_keys=True),
                        json.dumps(floor.get("feature_counts", {}), sort_keys=True),
                        len(floor.get("building_footprints", ())),
                    ),
                )
            for structure in profile.get("structures", ()):
                db.execute(
                    "INSERT INTO town_structures(town_id, town_name, kind, floors, min_floor, max_floor, "
                    "width, height, tile_count, confidence) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        town_id, town, structure.get("kind"), structure.get("floors"),
                        structure.get("floor_range", [None, None])[0],
                        structure.get("floor_range", [None, None])[1], structure.get("width"),
                        structure.get("height"), structure.get("wall_tiles"), 0.75,
                    ),
                )


def _read_json(path: Path, default: Any) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else default


def _insert_xml_node(
    db: sqlite3.Connection,
    document_id: int,
    parent_id: int | None,
    ordinal: int,
    element: ET.Element,
) -> None:
    cursor = db.execute(
        "INSERT INTO material_xml_nodes(document_id, parent_node_id, ordinal, tag, attributes_json, text) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (
            document_id,
            parent_id,
            ordinal,
            str(element.tag),
            json.dumps(dict(element.attrib), sort_keys=True),
            (element.text or "").strip(),
        ),
    )
    node_id = int(cursor.lastrowid)
    for child_ordinal, child in enumerate(list(element)):
        _insert_xml_node(db, document_id, node_id, child_ordinal, child)


def _resolve_appearance_id(item_id: int, item: dict[str, Any], render: dict[str, Any]) -> int | None:
    candidates = [item.get(key) for key in ("appearance_id", "client_id", "lookid", "id")]
    candidates.extend(
        brush.get("lookid") for brush in item.get("brushes", ()) if isinstance(brush, dict)
    )
    candidates.append(item_id)
    return next(
        (int(candidate) for candidate in candidates if candidate is not None and str(candidate) in render),
        None,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reference_source_snapshot(root: Path) -> tuple[tuple[str, int, int], ...]:
    corpus_root = root / "projects" / "Mapas Referencia"
    if not corpus_root.is_dir():
        return ()
    records = []
    for path in corpus_root.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in {".otbm", ".xml"}:
            continue
        stat = path.stat()
        records.append((
            path.relative_to(corpus_root).as_posix(),
            int(stat.st_mtime_ns),
            int(stat.st_size),
        ))
    return tuple(sorted(records))


def _quote_identifier(value: str) -> str:
    if not value or "\x00" in value:
        raise ValueError("Invalid SQLite identifier")
    return '"' + value.replace('"', '""') + '"'


def _table_exists(db: sqlite3.Connection, table: str) -> bool:
    return db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _create_parsed_brush_grammar_table(db: sqlite3.Connection) -> None:
    db.execute(
        "CREATE TABLE IF NOT EXISTS parsed_brush_grammar("
        "brush_key TEXT PRIMARY KEY REFERENCES brushes, name TEXT NOT NULL, type TEXT NOT NULL, "
        "look_id INTEGER, server_look_id INTEGER, member_count INTEGER NOT NULL, "
        "grammar_json TEXT NOT NULL, grammar_sha256 TEXT NOT NULL, source_file TEXT NOT NULL, "
        "source_sha256 TEXT NOT NULL)"
    )
    db.execute(
        "CREATE INDEX IF NOT EXISTS idx_parsed_brush_grammar_name "
        "ON parsed_brush_grammar(name,type)"
    )


_COUNTED_TABLES = (
    "source_files", "appearances", "appearance_flags", "appearance_sprites", "items", "item_roles", "item_tilesets",
    "brushes", "brush_members", "parsed_brush_grammar", "material_categories", "borders", "tilesets", "towns",
    "town_floor_observations", "town_minimap_colors", "structural_patterns",
    "town_semantic_features", "town_structures",
    "material_documents", "material_xml_nodes", "material_includes", "material_db_inventory",
    "reference_maps", "reference_material_usage", "reference_floor_profiles", "reference_archetypes",
    "reference_brush_usage", "reference_ground_transitions", "reference_source_archives",
    "reference_scan_reports", "reference_floor_material_usage", "reference_border_mixes",
    "reference_minimap_colors", "reference_minimap_color_materials",
    "world_town_scan_reports", "world_town_floor_material_usage", "world_town_scanned_structures",
    "quest_script_files", "quest_script_archives", "quest_identifiers", "quest_storage_transitions",
    "quest_rewards", "quest_movements", "quest_packages",
    "editor_runtime_observations",
    "rme_algorithm_sources", "rme_neighbor_bits", "rme_neighbor_lookup",
    "rme_operation_grammar", "rme_knowledge_coverage", "rme_menu_entries", "rme_action_handlers",
)


_SCHEMA = """
CREATE TABLE metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE source_files(id INTEGER PRIMARY KEY, name TEXT, path TEXT, bytes INTEGER, sha256 TEXT,
 read_error TEXT NOT NULL DEFAULT '');
CREATE TABLE material_documents(id INTEGER PRIMARY KEY, path TEXT UNIQUE, category TEXT, sha256 TEXT, content TEXT,
 parse_error TEXT NOT NULL DEFAULT '');
CREATE TABLE material_xml_nodes(id INTEGER PRIMARY KEY, document_id INTEGER REFERENCES material_documents,
 parent_node_id INTEGER REFERENCES material_xml_nodes, ordinal INTEGER, tag TEXT, attributes_json TEXT, text TEXT);
CREATE TABLE material_includes(document_id INTEGER REFERENCES material_documents, included_path TEXT,
 PRIMARY KEY(document_id, included_path));
CREATE TABLE material_db_inventory(source_table TEXT PRIMARY KEY, target_table TEXT, row_count INTEGER,
 columns_json TEXT);
CREATE TABLE appearances(appearance_id INTEGER PRIMARY KEY, width INTEGER, height INTEGER, layers INTEGER,
 pattern_width INTEGER, pattern_height INTEGER, pattern_depth INTEGER, animation_phases INTEGER,
 sprite_count INTEGER, properties_json TEXT NOT NULL);
CREATE TABLE appearance_sprites(appearance_id INTEGER REFERENCES appearances, sprite_index INTEGER,
 sprite_id INTEGER, PRIMARY KEY(appearance_id, sprite_index));
CREATE TABLE appearance_flags(appearance_id INTEGER PRIMARY KEY REFERENCES appearances, automap_color INTEGER,
 flags_json TEXT NOT NULL, animation_json TEXT NOT NULL, exact_fields_json TEXT NOT NULL);
CREATE TABLE items(item_id INTEGER PRIMARY KEY, appearance_id INTEGER, client_id INTEGER, name TEXT,
 server_type TEXT, appearance_present INTEGER, attributes_json TEXT, provenance_json TEXT);
CREATE TABLE item_roles(item_id INTEGER REFERENCES items, role TEXT, PRIMARY KEY(item_id, role));
CREATE TABLE item_tilesets(item_id INTEGER REFERENCES items, tileset TEXT, source TEXT,
 PRIMARY KEY(item_id, tileset, source));
CREATE TABLE brushes(brush_key TEXT PRIMARY KEY, name TEXT, type TEXT, look_id INTEGER, source TEXT);
CREATE TABLE brush_members(brush_key TEXT REFERENCES brushes, member_id INTEGER, role TEXT,
 PRIMARY KEY(brush_key, member_id, role));
CREATE TABLE parsed_brush_grammar(brush_key TEXT PRIMARY KEY REFERENCES brushes, name TEXT NOT NULL,
 type TEXT NOT NULL, look_id INTEGER, server_look_id INTEGER, member_count INTEGER NOT NULL,
 grammar_json TEXT NOT NULL, grammar_sha256 TEXT NOT NULL, source_file TEXT NOT NULL,
 source_sha256 TEXT NOT NULL);
CREATE INDEX idx_parsed_brush_grammar_name ON parsed_brush_grammar(name,type);
CREATE TABLE material_categories(category TEXT, item_id INTEGER, PRIMARY KEY(category, item_id));
CREATE TABLE borders(border_id INTEGER PRIMARY KEY, definition_json TEXT);
CREATE TABLE tilesets(name TEXT PRIMARY KEY, definition_json TEXT);
CREATE TABLE towns(town_id INTEGER PRIMARY KEY, name TEXT UNIQUE, anchor_x INTEGER, anchor_y INTEGER,
 anchor_z INTEGER, source TEXT);
CREATE TABLE town_floor_observations(town_id INTEGER REFERENCES towns, zone_tag TEXT, floor INTEGER,
 confidence REAL, entropy REAL, edge_density REAL, water_ratio REAL, nature_ratio REAL, dark_ratio REAL,
 tags_json TEXT, source_kind TEXT);
CREATE TABLE town_minimap_colors(zone_tag TEXT, floor INTEGER, color INTEGER, tile_count INTEGER,
 PRIMARY KEY(zone_tag, floor, color));
CREATE TABLE structural_patterns(id INTEGER PRIMARY KEY, kind TEXT, name TEXT, floors INTEGER, width INTEGER,
 height INTEGER, metrics_json TEXT, source TEXT, confidence REAL);
CREATE TABLE town_semantic_features(id INTEGER PRIMARY KEY, town_id INTEGER REFERENCES towns, town_name TEXT,
 floor INTEGER, role_counts_json TEXT, feature_counts_json TEXT, footprint_count INTEGER);
CREATE TABLE town_structures(id INTEGER PRIMARY KEY, town_id INTEGER REFERENCES towns, town_name TEXT, kind TEXT,
 floors INTEGER, min_floor INTEGER, max_floor INTEGER, width INTEGER, height INTEGER, tile_count INTEGER,
 confidence REAL);
CREATE TABLE reference_maps(id INTEGER PRIMARY KEY, name TEXT UNIQUE, source TEXT, source_sha256 TEXT,
 bytes INTEGER, tile_count INTEGER, width INTEGER, height INTEGER, min_floor INTEGER, max_floor INTEGER,
 town_name TEXT, town_x INTEGER, town_y INTEGER, town_z INTEGER, profile_json TEXT NOT NULL);
CREATE TABLE reference_material_usage(reference_id INTEGER REFERENCES reference_maps, item_id INTEGER,
 usage_count INTEGER, per_tile REAL, categories_json TEXT, brushes_json TEXT,
 PRIMARY KEY(reference_id, item_id));
CREATE TABLE reference_floor_profiles(reference_id INTEGER REFERENCES reference_maps, floor INTEGER,
 tile_count INTEGER, width INTEGER, height INTEGER, item_density REAL, ground_diversity INTEGER,
 profile_json TEXT, PRIMARY KEY(reference_id, floor));
CREATE TABLE reference_archetypes(name TEXT PRIMARY KEY, source_count INTEGER, metrics_json TEXT,
 generation_rules_json TEXT);
CREATE TABLE reference_brush_usage(reference_id INTEGER REFERENCES reference_maps, kind TEXT, name TEXT,
 usage_count INTEGER, PRIMARY KEY(reference_id, kind, name));
CREATE TABLE reference_ground_transitions(reference_id INTEGER REFERENCES reference_maps, ground_a INTEGER,
 ground_b INTEGER, edge_count INTEGER, PRIMARY KEY(reference_id, ground_a, ground_b));
CREATE TABLE reference_source_archives(id INTEGER PRIMARY KEY, reference_id INTEGER REFERENCES reference_maps,
 artifact_kind TEXT, filename TEXT, sha256 TEXT, original_bytes INTEGER, compression TEXT,
 access_scope TEXT CHECK(access_scope = 'analysis_only'), payload BLOB NOT NULL,
 UNIQUE(reference_id, artifact_kind, filename));
CREATE TABLE reference_scan_reports(reference_id INTEGER PRIMARY KEY REFERENCES reference_maps,
 scanner_version INTEGER, used_floors_json TEXT, report_json TEXT NOT NULL);
CREATE TABLE reference_floor_material_usage(reference_id INTEGER REFERENCES reference_maps, floor INTEGER,
 item_id INTEGER, usage_count INTEGER, per_tile REAL, categories_json TEXT, brushes_json TEXT,
 PRIMARY KEY(reference_id, floor, item_id));
CREATE TABLE reference_border_mixes(reference_id INTEGER REFERENCES reference_maps, floor INTEGER,
 ground_id INTEGER, border_id INTEGER, usage_count INTEGER,
 PRIMARY KEY(reference_id, floor, ground_id, border_id));
CREATE TABLE reference_minimap_colors(reference_id INTEGER REFERENCES reference_maps, floor INTEGER,
 color INTEGER, red INTEGER, green INTEGER, blue INTEGER, tile_count INTEGER, tile_ratio REAL,
 PRIMARY KEY(reference_id, floor, color));
CREATE TABLE reference_minimap_color_materials(reference_id INTEGER REFERENCES reference_maps, floor INTEGER,
 color INTEGER, item_id INTEGER, selection_role TEXT CHECK(selection_role IN ('top_item', 'ground')),
 tile_count INTEGER, PRIMARY KEY(reference_id, floor, color, item_id, selection_role));
CREATE TABLE world_town_scan_reports(town_id INTEGER PRIMARY KEY REFERENCES towns, town_name TEXT,
 scanner_version INTEGER, world_sha256 TEXT, radius INTEGER, floors_json TEXT, report_json TEXT NOT NULL);
CREATE TABLE world_town_floor_material_usage(town_id INTEGER REFERENCES towns, floor INTEGER, item_id INTEGER,
 usage_count INTEGER, per_tile REAL, categories_json TEXT, brushes_json TEXT,
 PRIMARY KEY(town_id, floor, item_id));
CREATE TABLE world_town_scanned_structures(id INTEGER PRIMARY KEY, town_id INTEGER REFERENCES towns,
 town_name TEXT, kind TEXT, min_floor INTEGER, max_floor INTEGER, width INTEGER, height INTEGER,
 evidence_count INTEGER, confidence REAL, details_json TEXT);
CREATE TABLE quest_script_files(id INTEGER PRIMARY KEY, relative_path TEXT UNIQUE, scope TEXT,
 package_name TEXT, language TEXT, sha256 TEXT, bytes INTEGER, constructors_json TEXT, callbacks_json TEXT,
 api_calls_json TEXT, dependencies_json TEXT, actors_json TEXT, metrics_json TEXT);
CREATE TABLE quest_script_archives(file_id INTEGER PRIMARY KEY REFERENCES quest_script_files,
 compression TEXT, access_scope TEXT CHECK(access_scope = 'analysis_only'), payload BLOB NOT NULL);
CREATE TABLE quest_identifiers(id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES quest_script_files,
 identifier_kind TEXT, identifier_value TEXT);
CREATE TABLE quest_storage_transitions(id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES quest_script_files,
 storage_ref TEXT, operation TEXT, value_expr TEXT);
CREATE TABLE quest_rewards(id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES quest_script_files,
 reward_kind TEXT, operation TEXT, item_expr TEXT, amount_expr TEXT);
CREATE TABLE quest_movements(id INTEGER PRIMARY KEY, file_id INTEGER REFERENCES quest_script_files,
 movement_kind TEXT, expression TEXT);
CREATE TABLE quest_packages(name TEXT PRIMARY KEY, scope TEXT, script_count INTEGER, language TEXT,
 summary_json TEXT NOT NULL, grammar_json TEXT NOT NULL);
CREATE TABLE editor_runtime_observations(domain TEXT NOT NULL, rule_key TEXT PRIMARY KEY,
 behavior_json TEXT NOT NULL, provenance TEXT NOT NULL, confidence REAL NOT NULL);
CREATE TABLE rme_algorithm_sources(source_file TEXT PRIMARY KEY, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL,
 provenance TEXT NOT NULL);
CREATE TABLE rme_neighbor_bits(system TEXT NOT NULL, bit INTEGER NOT NULL, direction TEXT NOT NULL,
 dx INTEGER NOT NULL, dy INTEGER NOT NULL, dz INTEGER NOT NULL,
 PRIMARY KEY(system, bit));
CREATE TABLE rme_neighbor_lookup(system TEXT NOT NULL, mask INTEGER NOT NULL, mask_binary TEXT NOT NULL,
 input_expression TEXT NOT NULL, output_expression TEXT NOT NULL, decoded_json TEXT NOT NULL,
 source_file TEXT NOT NULL, PRIMARY KEY(system, mask));
CREATE TABLE rme_operation_grammar(domain TEXT NOT NULL, rule_key TEXT PRIMARY KEY, grammar_json TEXT NOT NULL,
 provenance TEXT NOT NULL, confidence REAL NOT NULL);
CREATE TABLE rme_knowledge_coverage(category TEXT PRIMARY KEY, row_count INTEGER NOT NULL,
 certified INTEGER NOT NULL CHECK(certified IN (0,1)), source TEXT NOT NULL);
CREATE TABLE rme_menu_entries(sequence INTEGER PRIMARY KEY, entry_path TEXT UNIQUE NOT NULL,
 parent_path TEXT NOT NULL, depth INTEGER NOT NULL, ordinal INTEGER NOT NULL, entry_kind TEXT NOT NULL,
 raw_name TEXT NOT NULL, display_name TEXT NOT NULL, action TEXT NOT NULL DEFAULT '',
 hotkey TEXT NOT NULL DEFAULT '', help TEXT NOT NULL DEFAULT '', special TEXT NOT NULL DEFAULT '',
 source_file TEXT NOT NULL);
CREATE TABLE rme_action_handlers(action TEXT PRIMARY KEY, kind TEXT NOT NULL, handler TEXT NOT NULL,
 visible_in_menu INTEGER NOT NULL CHECK(visible_in_menu IN (0,1)), source_file TEXT NOT NULL);
CREATE INDEX idx_items_name ON items(name);
CREATE INDEX idx_roles_role ON item_roles(role);
CREATE INDEX idx_brushes_type ON brushes(type);
CREATE INDEX idx_town_observations ON town_floor_observations(zone_tag, floor);
CREATE INDEX idx_patterns_kind ON structural_patterns(kind);
CREATE INDEX idx_town_structures ON town_structures(town_name, kind);
CREATE INDEX idx_material_nodes_tag ON material_xml_nodes(tag);
CREATE INDEX idx_reference_material_item ON reference_material_usage(item_id);
CREATE INDEX idx_reference_floor ON reference_floor_profiles(floor);
CREATE INDEX idx_reference_brush ON reference_brush_usage(kind, name);
CREATE INDEX idx_reference_transition ON reference_ground_transitions(ground_a, ground_b);
CREATE INDEX idx_reference_floor_material ON reference_floor_material_usage(floor, item_id);
CREATE INDEX idx_reference_border_mix ON reference_border_mixes(floor, ground_id, border_id);
CREATE INDEX idx_reference_minimap_color ON reference_minimap_colors(color, floor);
CREATE INDEX idx_reference_color_material ON reference_minimap_color_materials(color, item_id, floor);
CREATE INDEX idx_world_town_floor_material ON world_town_floor_material_usage(town_id, floor, item_id);
CREATE INDEX idx_world_town_structure_kind ON world_town_scanned_structures(town_name, kind);
CREATE INDEX idx_quest_script_package ON quest_script_files(package_name, scope);
CREATE INDEX idx_quest_identifiers ON quest_identifiers(identifier_kind, identifier_value);
CREATE INDEX idx_quest_storages ON quest_storage_transitions(storage_ref, operation);
CREATE INDEX idx_quest_rewards ON quest_rewards(reward_kind, item_expr);
CREATE INDEX idx_quest_movements ON quest_movements(movement_kind);
CREATE INDEX idx_editor_runtime_domain ON editor_runtime_observations(domain);
CREATE INDEX idx_rme_neighbor_lookup_system ON rme_neighbor_lookup(system, mask);
CREATE INDEX idx_rme_operation_domain ON rme_operation_grammar(domain);
CREATE INDEX idx_rme_menu_parent ON rme_menu_entries(parent_path, ordinal);
"""


_PLANNER_MATERIAL_VIEWS = """
CREATE VIEW planner_ground_brushes AS
SELECT b.*, bi.item_id, bi.chance, bi.sort_order,
       gbb.border_set_id, gbb.border_role, gbb.align, gbb.target_mode, gbb.target_brush_name
FROM rme_brushes b
LEFT JOIN rme_brush_items bi ON bi.brush_id = b.id
LEFT JOIN rme_ground_brush_borders gbb ON gbb.brush_id = b.id
WHERE b.type = 'ground';
CREATE VIEW planner_wall_parts AS
SELECT b.name AS brush_name, b.look_id, wp.part_type, wpi.item_id, wpi.chance,
       wpd.item_id AS door_item_id, wpd.door_type, wpd.is_open
FROM rme_brushes b
JOIN rme_wall_parts wp ON wp.brush_id = b.id
LEFT JOIN rme_wall_part_items wpi ON wpi.wall_part_id = wp.id
LEFT JOIN rme_wall_part_doors wpd ON wpd.wall_part_id = wp.id
WHERE b.type = 'wall';
CREATE VIEW planner_tileset_catalog AS
SELECT t.name AS tileset, ts.section_type, e.entry_kind, e.brush_name, e.item_id,
       e.from_item_id, e.to_item_id, e.after_brush_name, e.sort_order
FROM rme_tilesets t
JOIN rme_tileset_sections ts ON ts.tileset_id = t.id
JOIN rme_tileset_brush_entries e ON e.tileset_section_id = ts.id;
"""
