"""Compile exact RME brush mathematics into queryable Planner knowledge."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


_DIRECTIONS = {
    "ground_border": (
        (1, "northwest", -1, -1), (2, "north", 0, -1),
        (4, "northeast", 1, -1), (8, "west", -1, 0),
        (16, "east", 1, 0), (32, "southwest", -1, 1),
        (64, "south", 0, 1), (128, "southeast", 1, 1),
    ),
    "wall": (
        (1, "north", 0, -1), (2, "west", -1, 0),
        (4, "east", 1, 0), (8, "south", 0, 1),
    ),
}

_PIPELINES: tuple[tuple[str, str, dict[str, Any]], ...] = (
    ("ground_brush", "atomic_ground_autoborder", {
        "steps": ["choose weighted ground member", "replace semantic ground family", "inspect 8-neighborhood",
                  "group neighbors by GroundBrush identity", "resolve inner/outer/optional border blocks",
                  "sort border clusters by z-order", "decode mask through 256-state lookup",
                  "apply specific-case delete/replace actions", "invalidate all changed neighbors"],
        "invariants": ["all variants of one brush are equivalent", "border pieces are derived, never planned directly",
                       "ground and borders commit or roll back together"],
    }),
    ("mountain_brush", "ground_border_mountain", {
        "source_contract": ["brushs/grounds.xml", "GroundBrush", "BorderBrush"],
        "steps": ["classify only type=ground mountain families", "choose the official weighted ground member",
                  "preserve ordered drag centers", "materialize the complete ground footprint",
                  "resolve inner, outer and optional border IDs from the source brush",
                  "orient the final silhouette from the complete neighborhood", "commit one transaction"],
        "invariants": ["mountain terrain is not a WallBrush",
                       "a DoodadBrush whose label mentions mountain remains a doodad",
                       "palette lookid is never substituted for a ground member",
                       "ground and mountain borders share one undo entry"],
    }),
    ("wall_brush", "connected_wall_orientation", {
        "steps": ["inspect N/W/E/S", "accept same or friend WallBrush unless wall_hate_me",
                  "build 4-bit mask", "select full or half 16-state lookup", "preserve door/window semantic type",
                  "reroll weighted item for resolved alignment", "realign wall decoration", "invalidate neighbors"],
        "invariants": ["orientation is topology-derived", "doors and windows inherit wall alignment",
                       "existing connected walls are reprocessed after each gesture"],
    }),
    ("doodad_brush", "weighted_single_composite", {
        "steps": ["select alternative", "compute single plus composite total chance", "weighted choice",
                  "apply composite offsets x/y/z as one gesture", "respect draggable/on_blocking/on_duplicate",
                  "commit or roll back complete composite"],
        "invariants": ["composite relative offsets stay intact", "AI chooses brush, engine chooses alternative"],
    }),
    ("doodad_brush", "nested_composite_stack_normalization", {
        "source_contract": ["DoodadBrush::loadAlternative", "composite/tile/item XML nesting"],
        "steps": ["walk every composite tile in source order", "flatten each nested item tuple recursively",
                  "reject booleans, non-positive IDs and non-SPRITE_BACKED members",
                  "preserve the original item order inside every relative tile stack"],
        "invariants": ["a one-item XML stack such as (1951,) becomes item 1951, never tuple (1951,)",
                       "validation happens before materialization", "invalid alternatives fail closed"],
    }),
    ("table_brush", "connected_table_orientation", {
        "steps": ["inspect same TableBrush neighbors", "build neighborhood mask", "lookup table alignment",
                  "weighted item selection for north/south/east/west end, horizontal, vertical or alone"],
        "invariants": ["table parts are not raw decorations", "neighbor changes trigger reorientation"],
    }),
    ("carpet_brush", "carpet_autoborder", {
        "steps": ["place center carpet", "inspect 8-neighborhood", "decode 256-state carpet lookup",
                  "choose weighted alignment item", "fall back to center when alignment is absent"],
        "invariants": ["center and edge pieces belong to one CarpetBrush family"],
    }),
    ("door_brush", "wall_embedded_door", {
        "steps": ["locate host wall and alignment", "resolve requested door semantic type",
                  "select matching closed/open item", "preserve action/unique identifiers when replacing"],
        "door_types": ["archway", "normal", "locked", "quest", "magic", "window", "hatch_window"],
    }),
    ("tile_postprocess", "rme_commit_order", {
        "steps": ["ground borders", "walls and wall decorations", "tables", "carpets", "complex metadata",
                  "draw-order normalization", "visual dirty-region invalidation", "roundtrip validation"],
        "transaction": "BatchAction/copy-on-write; any stage failure restores every touched tile",
    }),
    ("rendering", "item_stack_projection", {
        "source_contract": ["MapDrawer::BlitItem", "GameSprite::getIndex"],
        "sprite_index": "((((frame % phases) * pattern_z + z) * pattern_y + y) * pattern_x + x) * layers + layer",
        "map_item_layer": 0,
        "screen_anchor": ["screen_x = draw_x - draw_offset_x", "screen_y = draw_y - draw_offset_y"],
        "stack_elevation": ["draw_x -= draw_height", "draw_y -= draw_height", "applies to following stack item"],
        "invariants": ["never scale a multi-size sprite into one 32x32 tile", "never overlay every layer for ordinary map items"],
    }),
    ("rendering", "visible_floor_projection", {
        "surface": {"condition": "current_floor <= 7", "start_z": 7, "end_z": "current_floor"},
        "underground": {"condition": "current_floor > 7", "start_z": "min(15,current_floor+2)", "end_z": "current_floor"},
        "iteration": "descending z; current floor is drawn last",
        "projection": ["screen_x += (z-current_floor)*32", "screen_y += (z-current_floor)*32"],
        "defaults": {"show_all_floors": True, "show_grid": False},
    }),
    ("materials", "tileset_section_semantics", {
        "pages": ["terrain", "doodad", "items", "raw", "monsters", "npcs"],
        "direct_item": "create RAWBrush in the containing page while preserving XML order",
        "combined_sections": ["terrain_and_raw", "doodad_and_raw", "items_and_raw"],
        "combined_behavior": "register the same entry in its primary page and RAW",
        "brush_reference": "resolve by exact material brush name; do not infer an item from the label",
    }),
    ("ui", "rme_menu_shortcut_contract", {
        "top_menus": ["File", "Edit", "Map", "Select", "View", "Window", "Floor", "AI Studio", "About"],
        "palette_shortcuts": {"terrain": "T", "doodad": "D", "item": "I", "house": "H", "monster": "C", "npc": "N", "waypoint": "W", "zone": "Z", "raw": "R"},
        "navigation": {"go_to": "Ctrl+G", "official_floor_hotkeys": None,
                       "successor_floor_extension": {"up": ["+", "PageUp"], "down": ["-", "PageDown"]}},
        "view": {"grid": "Shift+G", "all_floors": "Ctrl+W", "fullscreen": "F11"},
    }),
    ("ui", "field_context_brush_resolution", {
        "source_contract": ["MapCanvas::CreatePopupMenu", "MapCanvas::OnSelectRAWBrush",
                            "MapCanvas::OnSelectGroundBrush", "g_gui.SelectBrush"],
        "item_actions": ["RAW", "DoodadBrush", "DoorBrush", "WallBrush", "CarpetBrush", "TableBrush"],
        "tile_actions": ["GroundBrush", "HouseBrush"],
        "steps": ["select the clicked field", "inspect the top item and tile ground",
                  "resolve the owning material brush by exact membership",
                  "switch to the brush's real palette and tileset",
                  "activate the same brush in the transactional editor"],
        "invariants": ["RAW selects the exact item", "GroundBrush selects the semantic ground family",
                       "doors resolve through their host WallBrush grammar",
                       "the visible palette and active engine brush never diverge"],
    }),
    ("ui", "atomic_drag_paint_gesture", {
        "source_contract": ["MapCanvas mouse down/move/up", "BatchAction", "ActionQueue"],
        "steps": ["freeze the active brush at mouse down", "accumulate unique footprint tiles while dragging",
                  "show an incremental placement preview", "validate the complete footprint",
                  "commit one neighbor-aware transaction on mouse up", "redraw only dirty chunks"],
        "batchable_families": ["GroundBrush", "RAWBrush", "TableBrush", "CarpetBrush",
                               "DoodadBrush", "WallBrush", "MountainBrush"],
        "center_sensitive_families": ["DoodadBrush", "WallBrush", "semantic tools"],
        "mountain_stroke": "ordered centers become one GroundBrush footprint; orientation is derived once by the final BorderBrush neighborhood",
        "invariants": ["one undo entry per batchable drag gesture",
                       "failed post-processing restores the complete gesture",
                       "center-sensitive strokes preserve ordered centers inside one copy-on-write transaction"],
    }),
    ("ui", "modal_item_properties", {
        "source_contract": ["MapCanvas::OnProperties", "PropertiesWindow", "ACTION_CHANGE_PROPERTIES"],
        "steps": ["require one selected field", "deep-copy the selected tile or item",
                  "open a parented modal dialog without changing dock geometry",
                  "validate all attributes", "commit one change-properties action only on OK",
                  "discard the copy on Cancel"],
        "invariants": ["opening Properties never resizes the viewport", "Cancel is mutation-free",
                       "tile metadata and complex item attributes commit atomically"],
    }),
    ("rendering", "retained_chunk_navigation", {
        "steps": ["coalesce scroll and resize events", "retain already rendered pixmaps during camera motion",
                  "load newly visible chunks", "replace changed tile pixmaps",
                  "prune stale visual items only after replacement is available"],
        "grid_off": "empty tiles use the scene background; never allocate persistent dark tile rectangles",
        "invariants": ["undo removes stale pixmaps immediately", "camera motion never exposes mutation artifacts",
                       "one scrollbar movement does not trigger duplicate synchronous chunk scans"],
    }),
    ("runtime", "asynchronous_ai_proposal_boundary", {
        "steps": ["freeze prompt and provider mode", "allow one active request",
                  "run Planner/model orchestration outside the Qt thread",
                  "return through queued signals", "restore controls on success or failure"],
        "failure_policy": "provider, timeout and parsing failures are reported in AI Studio and never terminate Qt",
        "invariants": ["viewport remains interactive during inference", "no proposal applies without approval",
                       "stale completion tokens cannot replace a newer request"],
    }),
    ("runtime", "progressive_certified_core_initialization", {
        "stages": ["validate official assets", "show editor shell", "start certified core worker",
                   "connect Planner database server", "initialize knowledge services", "atomically publish ready core"],
        "ui_during_warmup": ["menus visible", "official palettes readable", "viewport responsive",
                             "document mutation disabled", "status exposes loading state"],
        "failure_policy": "fail closed; keep the UI alive and expose the blocker; never silently downgrade",
        "threading": "database and Planner initialization run outside the Qt main thread",
        "observability": ["begin event", "ready/error event", "elapsed milliseconds", "status phase"],
    }),
    ("otbm", "single_pass_transaction_roundtrip", {
        "steps": ["index source tile areas once", "apply copy-on-write node patches",
                  "audit the complete temporary file", "scan patched output once",
                  "compare headers and complete descendant item order for every target",
                  "atomically replace destination"],
        "complexity": "O(source bytes + patched tiles), never O(source bytes * patched tiles)",
        "invariants": ["unknown untouched payloads stay byte-identical",
                       "ground, flags, house identity and nested stack order must roundtrip",
                       "failed validation never replaces the destination"],
    }),
    ("otbm", "canonical_loaded_tile_stack", {
        "source_contract": ["IOMapOTBM::loadMap", "Tile::addLoadedItem", "Tile::update"],
        "steps": ["read serialized ground and child items in file order",
                  "replace an earlier ground when a later ground candidate is loaded",
                  "insert always-on-bottom items by top order",
                  "preserve insertion order for remaining objects",
                  "serialize generated maps from the normalized in-memory stack"],
        "invariants": ["reference OTBM files may legally require load normalization",
                       "new generated files are emitted canonical and deterministic",
                       "QA evaluates Canary's loaded tile state, not a stricter invented format"],
    }),
    ("learning", "validated_experience_policy_gate", {
        "inputs": ["human-promoted positive rules", "human-promoted negative constraints"],
        "allowlisted_effects": ["nature density", "connectivity QA", "vertical connectivity QA",
                                "official AutoBorder", "wall alignment", "material safety",
                                "sprite-backed visual QA", "Similarity Guard", "no teleports"],
        "invariants": ["minimum confidence 0.65", "never accept learned raw item IDs",
                       "never accept learned source coordinates", "models do not place tiles directly"],
    }),
    ("planner", "compact_objective_scope", {
        "triggers": ["small river", "small lake", "small beach", "small island", "nature test area"],
        "steps": ["classify objective scope before Scene Graph construction",
                  "build original compact land, water and nature geometry",
                  "apply only relevant reference grammar", "materialize with official brushes",
                  "run compact density, material safety and AutoBorder QA"],
        "invariants": ["a compact nature request never inherits NECRO city or hunt regions",
                       "reference knowledge changes proportions and density, not source geometry"],
    }),
    ("otbm", "generated_map_navigation_bundle", {
        "steps": ["serialize canonical map attributes", "declare matching house/monster/npc/zone filenames",
                  "write valid empty sidecars when gameplay metadata is absent",
                  "size the header to contain all generated coordinates with a practical navigation margin",
                  "declare one navigation town/temple anchor near the generated area"],
        "invariants": ["all sidecar names match the OTBM stem", "Canary opens without missing-sidecar dialogs",
                       "small maps do not open hundreds of tiles away from their content"],
    }),
)


class RMETechnicalKnowledgeCompiler:
    """Extract symbolic lookup tables and certified operational grammar from RME."""

    _OWNED_TABLES = (
        "rme_knowledge_coverage",
        "rme_action_handlers",
        "rme_menu_entries",
        "rme_operation_grammar",
        "rme_neighbor_lookup",
        "rme_neighbor_bits",
        "rme_algorithm_sources",
    )

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.source_dir = (
            self.root / "projects" / "canary-extracted" /
            "canary-map-editor-v4.0-windows" / "source"
        )
        self.data_dir = self.source_dir.parent / "data"

    def populate(self, db: sqlite3.Connection) -> None:
        """Atomically rebuild the exact knowledge derived from RME sources.

        These tables are projections of immutable source files, not append-only
        observations. Rebuilding them makes repeated startup, migration and
        recovery runs deterministic while a savepoint preserves the previous
        certified snapshot if parsing fails.
        """
        enums_path = self.source_dir / "brush_enums.h"
        tables_path = self.source_dir / "brush_tables.cpp"
        enums = self._parse_enums(enums_path.read_text(encoding="utf-8", errors="replace"))
        db.execute("SAVEPOINT rme_technical_knowledge_rebuild")
        try:
            self._clear_owned_tables(db)
            self._insert_sources(
                db,
                enums_path,
                tables_path,
                self.source_dir / "map_drawer.cpp",
                self.source_dir / "graphics.cpp",
                self.source_dir / "tileset.cpp",
                self.source_dir / "main_menubar.cpp",
                self.source_dir / "main_menubar.h",
                self.source_dir / "main_toolbar.cpp",
                self.source_dir / "palette_common.cpp",
                self.source_dir / "palette_window.cpp",
                self.source_dir / "palette_house.cpp",
                self.source_dir / "palette_monster.cpp",
                self.source_dir / "palette_npc.cpp",
                self.source_dir / "palette_waypoints.cpp",
                self.source_dir / "palette_zones.cpp",
                self.data_dir / "menubar.xml",
            )
            self._insert_directions(db)
            self._insert_lookups(db, tables_path, enums)
            self._insert_pipelines(db)
            self._insert_menu_contract(db)
            self._insert_coverage(db)
        except Exception:
            db.execute("ROLLBACK TO SAVEPOINT rme_technical_knowledge_rebuild")
            db.execute("RELEASE SAVEPOINT rme_technical_knowledge_rebuild")
            raise
        db.execute("RELEASE SAVEPOINT rme_technical_knowledge_rebuild")

    @classmethod
    def _clear_owned_tables(cls, db: sqlite3.Connection) -> None:
        for table in cls._OWNED_TABLES:
            db.execute(f"DELETE FROM {table}")

    def _insert_menu_contract(self, db: sqlite3.Connection) -> None:
        xml_path = self.data_dir / "menubar.xml"
        cpp_path = self.source_dir / "main_menubar.cpp"
        root = ET.parse(xml_path).getroot()
        sequence = 0
        visible_actions: set[str] = set()

        def walk(parent: ET.Element, parent_path: str, depth: int) -> None:
            nonlocal sequence
            for ordinal, node in enumerate(parent):
                kind = node.tag.casefold()
                raw_name = node.attrib.get("name", "")
                display_name = raw_name.replace("$", "").strip()
                component = display_name or f"{kind}-{ordinal}"
                entry_path = f"{parent_path}/{ordinal}:{component}" if parent_path else f"{ordinal}:{component}"
                action = node.attrib.get("action", "")
                if action:
                    visible_actions.add(action)
                db.execute(
                    "INSERT INTO rme_menu_entries(sequence,entry_path,parent_path,depth,ordinal,entry_kind,"
                    "raw_name,display_name,action,hotkey,help,special,source_file) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        sequence, entry_path, parent_path, depth, ordinal, kind, raw_name, display_name,
                        action, node.attrib.get("hotkey", ""), node.attrib.get("help", ""),
                        node.attrib.get("special", ""), str(xml_path),
                    ),
                )
                sequence += 1
                if kind == "menu":
                    walk(node, entry_path, depth + 1)

        walk(root, "", 0)
        cpp = cpp_path.read_text(encoding="utf-8", errors="replace")
        handlers = re.findall(
            r"(?m)^\s*MAKE_ACTION\(\s*([A-Z][A-Z0-9_]*)\s*,\s*([^,]+)\s*,\s*([A-Za-z0-9_]+)\s*\);",
            cpp,
        )
        db.executemany(
            "INSERT OR REPLACE INTO rme_action_handlers(action,kind,handler,visible_in_menu,source_file) "
            "VALUES (?,?,?,?,?)",
            (
                (action, kind.strip(), handler, int(action in visible_actions), str(cpp_path))
                for action, kind, handler in handlers
            ),
        )

    @staticmethod
    def _parse_enums(text: str) -> dict[str, int]:
        values: dict[str, int] = {}
        current = -1
        for raw in text.splitlines():
            line = raw.split("//", 1)[0].strip().rstrip(",")
            match = re.fullmatch(r"([A-Z][A-Z0-9_]*)\s*(?:=\s*(\d+))?", line)
            if not match:
                continue
            current = int(match.group(2)) if match.group(2) is not None else current + 1
            values[match.group(1)] = current
        return values

    def _insert_sources(self, db: sqlite3.Connection, *paths: Path) -> None:
        for path in paths:
            data = path.read_bytes()
            db.execute(
                "INSERT OR REPLACE INTO rme_algorithm_sources(source_file,sha256,bytes,provenance) VALUES (?,?,?,?)",
                (str(path), hashlib.sha256(data).hexdigest(), len(data), "official Canary/RME source"),
            )

    @staticmethod
    def _insert_directions(db: sqlite3.Connection) -> None:
        for system, entries in _DIRECTIONS.items():
            db.executemany(
                "INSERT OR REPLACE INTO rme_neighbor_bits(system,bit,direction,dx,dy,dz) VALUES (?,?,?,?,?,0)",
                ((system, bit, name, dx, dy) for bit, name, dx, dy in entries),
            )

    def _insert_lookups(self, db: sqlite3.Connection, path: Path, enums: dict[str, int]) -> None:
        text = path.read_text(encoding="utf-8", errors="replace")
        pattern = re.compile(
            r"(?P<table>(?:GroundBrush::border_types|WallBrush::full_border_types|"
            r"WallBrush::half_border_types|TableBrush::table_types|CarpetBrush::carpet_types))"
            r"\[(?P<input>[^\]]+)\](?:\s*//\s*(?P<bits>[01]+))?\s*=\s*(?P<output>[^;]+);",
            re.MULTILINE,
        )
        aliases = {
            "GroundBrush::border_types": "ground_border",
            "WallBrush::full_border_types": "wall_full",
            "WallBrush::half_border_types": "wall_half",
            "TableBrush::table_types": "table",
            "CarpetBrush::carpet_types": "carpet",
        }
        rows = []
        for match in pattern.finditer(text):
            input_expression = " ".join(match.group("input").split())
            mask = 0
            for symbol in (part.strip() for part in input_expression.split("|")):
                mask |= int(symbol) if symbol.isdigit() else int(enums[symbol])
            width = 4 if match.group("table").startswith("WallBrush") else 8
            output = " ".join(match.group("output").split())
            decoded = []
            for term in (part.strip() for part in output.split("|")):
                item = re.fullmatch(r"([A-Z][A-Z0-9_]*)(?:\s*<<\s*(\d+))?", term)
                if not item:
                    decoded.append({"expression": term})
                    continue
                shift = int(item.group(2) or 0)
                decoded.append({
                    "symbol": item.group(1), "enum_value": enums.get(item.group(1)),
                    "shift": shift, "output_slot": shift // 8,
                })
            rows.append((
                aliases[match.group("table")], mask, format(mask, f"0{width}b"),
                input_expression, output, json.dumps(decoded, sort_keys=True), str(path),
            ))
        db.executemany(
            "INSERT OR REPLACE INTO rme_neighbor_lookup(system,mask,mask_binary,input_expression,output_expression,"
            "decoded_json,source_file) VALUES (?,?,?,?,?,?,?)", rows,
        )

    @staticmethod
    def _insert_pipelines(db: sqlite3.Connection) -> None:
        db.executemany(
            "INSERT OR REPLACE INTO rme_operation_grammar(domain,rule_key,grammar_json,provenance,confidence) "
            "VALUES (?,?,?,'official Canary/RME source + certified live behavior',1.0)",
            ((domain, key, json.dumps(value, sort_keys=True)) for domain, key, value in _PIPELINES),
        )

    @staticmethod
    def _insert_coverage(db: sqlite3.Connection) -> None:
        queries = {
            "brushes": "SELECT COUNT(*) FROM rme_brushes",
            "ground_borders": "SELECT COUNT(*) FROM rme_ground_brush_borders",
            "border_pieces": "SELECT COUNT(*) FROM rme_border_set_items",
            "wall_parts": "SELECT COUNT(*) FROM rme_wall_parts",
            "wall_doors_windows": "SELECT COUNT(*) FROM rme_wall_part_doors",
            "doodad_singles": "SELECT COUNT(*) FROM rme_doodad_single_items",
            "doodad_composites": "SELECT COUNT(*) FROM rme_doodad_composites",
            "doodad_composite_tiles": "SELECT COUNT(*) FROM rme_doodad_composite_tiles",
            "table_nodes": "SELECT COUNT(*) FROM rme_table_nodes",
            "carpet_nodes": "SELECT COUNT(*) FROM rme_carpet_nodes",
            "tilesets": "SELECT COUNT(*) FROM rme_tilesets",
            "tileset_entries": "SELECT COUNT(*) FROM rme_tileset_brush_entries",
            "menu_entries": "SELECT COUNT(*) FROM rme_menu_entries",
            "menu_action_handlers": "SELECT COUNT(*) FROM rme_action_handlers",
        }
        for key, query in queries.items():
            db.execute(
                "INSERT OR REPLACE INTO rme_knowledge_coverage(category,row_count,certified,source) VALUES (?,?,1,?)",
                (key, int(db.execute(query).fetchone()[0]), "Canary materials.db"),
            )


__all__ = ["RMETechnicalKnowledgeCompiler"]
