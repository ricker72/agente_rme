from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AgentProbe:
    path: str
    symbols: tuple[str, ...]


@dataclass(frozen=True)
class SourceSystem:
    key: str
    priority: str
    source_files: tuple[str, ...]
    probes: tuple[AgentProbe, ...]
    weakness_if_incomplete: str
    acceptance: tuple[str, ...]
    depends_on: tuple[str, ...] = ()


SOURCE_SYSTEMS: tuple[SourceSystem, ...] = (
    SourceSystem(
        "map_spatial_storage",
        "P0",
        ("basemap.cpp", "basemap.h", "map_region.cpp", "map_region.h", "map.cpp", "map.h"),
        (AgentProbe("core/editor/rme_map_model.py", ("RMEMapSpatialIndex", "RME_LEAF_SIZE = 4", "TileLocationState", "leaves_in_rect", "visible_clients", "requested")),),
        "Flat tile dictionaries cannot scale, request visible regions or maintain spawn/waypoint location counters like RME.",
        ("4x4 leaf lookup", "16 floors", "region iteration", "location counters", "visibility/request state"),
    ),
    SourceSystem(
        "actions_transactions_selection",
        "P0",
        ("action.cpp", "action.h", "editor.cpp", "editor.h", "selection.cpp", "selection.h"),
        (
            AgentProbe("core/editor/action_queue.py", ("BatchAction", "EditTransaction", "atomic_commit_ready", "memory_limit", "undo", "redo")),
            AgentProbe("ui/live_preview/map_selection.py", ("Selection", "selection_safe_action", "external_selection_mode")),
        ),
        "AI repairs can fragment undo history and selection mutations are not guaranteed to be one atomic editor operation.",
        ("batch commit/rollback", "undo/redo", "memory bounded history", "selection-safe actions", "dirty refresh list"),
        ("map_spatial_storage",),
    ),
    SourceSystem(
        "item_types_attributes_complex_items",
        "P0",
        ("items.cpp", "items.h", "item.cpp", "item.h", "item_attributes.cpp", "item_attributes.h", "complexitem.cpp", "complexitem.h"),
        (
            AgentProbe("core/editor/item_type_flags.py", ("always_on_bottom", "always_on_top_order", "is_ground", "is_border", "is_wall", "is_container", "is_teleport", "is_depot")),
            AgentProbe("core/editor/complex_items.py", ("EditableItem", "unique_id", "action_id", "children", "TeleportDestination", "house_door_id", "depot_id")),
            AgentProbe("core/world_generator/otbm_world/attributes.py", ("ATTR_TELE_DEST", "ATTR_HOUSE_DOOR_ID", "ATTR_DEPOT_ID", "ATTR_COUNT", "ATTR_CHARGES")),
            AgentProbe("core/world_generator/otbm_world/item_encoder.py", ("children", "item_to_node")),
            AgentProbe("core/opentibia/assets/appearance_dat_flags.py", ("unpass", "unmove", "automap_color", "light_level", "elevation")),
        ),
        "Exact item flags, typed attributes and recursive complex-item payloads must stay aligned with Canary OTBM widths.",
        ("exact OTB flags", "attributes roundtrip", "containers", "teleports", "doors/depots", "unique/action IDs"),
    ),
    SourceSystem(
        "materials_tilesets_palettes",
        "P0",
        ("materials.cpp", "materials.h", "brush_database.cpp", "brush_database.h", "tileset.cpp", "tileset.h", "palette_window.cpp", "palette_brushlist.cpp"),
        (
            AgentProbe("core/editor/material_catalog.py", ("RMEMaterialCatalog", "brush", "reload", "tileset_categories")),
            AgentProbe("ui/live_preview/rme_palette_model.py", ("Palette", "tileset", "filter")),
        ),
        "The agent can resolve brushes but does not yet reproduce every tileset category, duplicate rule and material reload behavior.",
        ("all official brush XML loaded", "tileset hierarchy", "palette filters", "sprite-backed-only entries", "reload diagnostics"),
        ("item_types_attributes_complex_items",),
    ),
    SourceSystem(
        "brush_engine_postprocess",
        "P0",
        ("brush.cpp", "brush.h", "ground_brush.cpp", "wall_brush.cpp", "table_brush.cpp", "carpet_brush.cpp", "doodad_brush.cpp", "raw_brush.cpp", "brush_tables.cpp", "brush_enums.h"),
        (
            AgentProbe("core/world_generator/rme_brush_engine.py", ("GroundBrush", "DoodadBrush", "WallBrush", "table_brushes", "carpet_brushes", "wall_decoration_brushes", "AutoBorder", "apply_walls", "erase_brush", "multitile_composite")),
            AgentProbe("core/editor/brush_postprocessor.py", ("real_brush_engine_connected", "ground_variants", "borderize", "optional_borderize", "rme_brush_postprocess")),
            AgentProbe("core/editor/brush_engine_certifier.py", ("RMEBrushEngineCertifier", "canary_parity_fixtures", "erase_postprocess")),
        ),
        "Brush parity must remain backed by executable Canary fixtures and real neighbor mutations.",
        ("exact border masks", "wall/table/carpet neighbor rewrites", "doodad composites", "eraser behavior", "postprocess emitted as one batch action"),
        ("actions_transactions_selection", "materials_tilesets_palettes"),
    ),
    SourceSystem(
        "otbm_otmm_io",
        "P0",
        ("iomap.cpp", "iomap.h", "iomap_otbm.cpp", "iomap_otbm.h", "iomap_otmm.cpp", "iomap_otmm.h", "filehandle.cpp", "filehandle.h"),
        (
            AgentProbe("core/otbm/otbm_importer.py", ("OTBM", "tile", "unknown_attributes")),
            AgentProbe("core/editor/otbm_roundtrip_validator.py", ("OTBMRoundtripValidator", "validate", "size_ratio")),
            AgentProbe("core/world_generator/otbm_world/compiler.py", ("compile", "tile", "sidecar")),
        ),
        "Roundtrip exists, but full preservation of unknown attributes, sidecars and all node variants remains the principal export risk.",
        ("lossless load-save", "compact tile areas", "all item attributes", "house/spawn/zone sidecars", "size parity gate"),
        ("map_spatial_storage", "item_types_attributes_complex_items"),
    ),
    SourceSystem(
        "graphics_render_light",
        "P0",
        ("graphics.cpp", "graphics.h", "gl_renderer.cpp", "gl_renderer.h", "map_drawer.cpp", "map_drawer.h", "light_drawer.cpp", "light_drawer.h", "sprite_appearances.cpp", "sprite_appearances.h"),
        (
            AgentProbe("ui/live_preview/rme_gl_viewport.py", ("QOpenGLWidget", "orthographic", "AppearanceTileRenderer", "floor_occlusion", "multi_tile_footprint")),
            AgentProbe("ui/live_preview/rendering/sprites/sprite_index_resolver.py", ("SpriteIndexResolver", "RME_GAME_SPRITE_INDEX", "pattern_z", "layer")),
            AgentProbe("ui/live_preview/rendering/ingame_render_mode.py", ("light_level", "elevation", "sprite_animation_timing", "light_compositor")),
        ),
        "Sprite selection is real, while native shader batching, per-pixel light composition, floor occlusion and multi-tile footprint parity remain partial.",
        ("official pixels only", "exact stack order", "multi-floor occlusion", "multi-tile footprints", "light blending", "Canary screenshot diff"),
        ("item_types_attributes_complex_items",),
    ),
    SourceSystem(
        "houses_towns",
        "P1",
        ("house.cpp", "house.h", "house_brush.cpp", "house_brush.h", "house_exit_brush.cpp", "house_exit_brush.h", "town.cpp", "town.h"),
        (AgentProbe("core/editor/gameplay_p1.py", ("HouseDefinition", "add_house", "exit", "house_id", "town_id", "move_house_exit", "house_sidecar")),),
        "House assignment exists but town ownership, exit relocation actions and sidecar fidelity need stronger parity.",
        ("house tile ownership", "one exit per house", "town linkage", "PZ semantics", "XML/OTBM roundtrip"),
        ("actions_transactions_selection", "otbm_otmm_io"),
    ),
    SourceSystem(
        "spawns_creatures_npcs",
        "P1",
        ("spawn_monster.cpp", "spawn_monster.h", "spawn_npc.cpp", "spawn_npc.h", "monster.cpp", "monsters.cpp", "npc.cpp", "npcs.cpp", "monster_brush.cpp", "npc_brush.cpp"),
        (AgentProbe("core/editor/gameplay_p1.py", ("SpawnDefinition", "CreatureCatalog", "spawn_monsters", "spawn_npcs", "radius_location_counts", "overlap_detection", "spawn_xml_sidecar", "spawn_time_validation")),),
        "Definitions are present, but RME TileLocation radius counters, overlap lookup and complete XML creature metadata are incomplete.",
        ("radius counters", "overlap detection", "valid creature names", "spawn time", "XML sidecars", "palette appearances"),
        ("map_spatial_storage", "otbm_otmm_io"),
    ),
    SourceSystem(
        "zones_waypoints_minimap",
        "P1",
        ("zones.cpp", "zones.h", "zone_brush.cpp", "waypoints.cpp", "waypoints.h", "waypoint_brush.cpp", "iominimap.cpp", "iominimap.h", "minimap_window.cpp"),
        (
            AgentProbe("core/editor/gameplay_p1.py", ("ZoneDefinition", "WaypointDefinition", "add_zone", "add_waypoint", "deleted_zone_cleanup", "waypoint_sidecar")),
            AgentProbe("ui/live_preview/rendering/rme_mapcolors.py", ("rme_minimap_color_to_rgb", "automap_color")),
            AgentProbe("core/world_generator/rme_minimap_exporter.py", ("satellite_export", "floor_range")),
        ),
        "Basic zone/waypoint data exists; deleted-zone cleanup, location counters and exact minimap/satellite export are partial.",
        ("zone lifecycle", "waypoint counters", "mapcolors", "floor PNG export", "sidecar roundtrip"),
        ("map_spatial_storage", "otbm_otmm_io"),
    ),
    SourceSystem(
        "copy_import_bitmap",
        "P2",
        ("copybuffer.cpp", "copybuffer.h", "bitmap_to_map_converter.cpp", "bitmap_to_map_converter.h", "bitmap_to_map_window.cpp"),
        (AgentProbe("core/editor/advanced_tools_p2p3.py", ("CopyBufferTool", "BitmapToMapTool", "skip_existing", "merge", "paste_preview", "house_id_remap", "nearest_material_color")),),
        "Chunk copy works, but selection borders, paste preview, house ID remapping and image color-distance matching are incomplete.",
        ("relative copy", "paste preview", "house remap", "spawn/waypoint merge", "nearest material color"),
        ("actions_transactions_selection",),
    ),
    SourceSystem(
        "find_replace_properties",
        "P2",
        ("find_item_window.cpp", "replace_items_window.cpp", "properties_window.cpp", "container_properties_window.cpp", "add_item_window.cpp"),
        (AgentProbe("core/editor/advanced_tools_p2p3.py", ("FindReplaceTool", "set_tile_properties", "replace_item", "nested_container", "unique_id", "action_id", "teleport_destination")),),
        "Find/replace covers IDs and names but not nested containers, action/unique IDs, text, destination, depot and door attributes.",
        ("nested search", "all item attributes", "typed property validation", "atomic replace", "visual repair integration"),
        ("item_types_attributes_complex_items", "actions_transactions_selection"),
    ),
    SourceSystem(
        "lua_automation",
        "P3",
        ("lua_parser.h",),
        (AgentProbe("core/editor/advanced_tools_p2p3.py", ("LuaLikeEditorAPI", "get_tile", "set_stack", "add_item", "sandbox", "resource_limit", "error_rollback")),),
        "The local extracted source lacks the previously expected lua_api_* files; the agent exposes only a Python-like compatibility surface.",
        ("sandbox", "map/tile/item/brush APIs", "one script transaction", "resource limits", "error rollback"),
        ("actions_transactions_selection", "brush_engine_postprocess"),
    ),
    SourceSystem(
        "live_edit_network",
        "P3",
        ("live_action.cpp", "live_client.cpp", "live_server.cpp", "live_socket.cpp", "live_packets.h", "net_connection.cpp"),
        (AgentProbe("core/editor/advanced_tools_p2p3.py", ("LiveEditSession", "paint_stack", "replace_item", "cursor", "packet_codec", "network_transport", "node_request", "conflict_policy")),),
        "Current live editing is an in-process event queue, not RME packet framing, authentication, node requests or conflict handling.",
        ("packet codec", "network transport", "remote actions", "cursor sync", "region requests", "conflict policy"),
        ("map_spatial_storage", "actions_transactions_selection"),
    ),
)


class RMESourceGapScanner:
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)
        self.source_root = self.root / "projects/canary-extracted/canary-map-editor-v4.0-windows/source"

    def scan(self) -> dict[str, Any]:
        systems = self._dependency_order([self._scan_system(system) for system in SOURCE_SYSTEMS])
        return {
            "stage": "RME Official Source Gap Scan",
            "status": "PASS" if all(item["status"] == "IMPLEMENTED" for item in systems) else "PARTIAL",
            "official_source_files": len(list(self.source_root.glob("*.*"))),
            "systems_scanned": len(systems),
            "implemented": sum(item["status"] == "IMPLEMENTED" for item in systems),
            "partial": sum(item["status"] == "PARTIAL" for item in systems),
            "missing": sum(item["status"] == "MISSING" for item in systems),
            "implementation_plan": [item["key"] for item in systems if item["status"] != "IMPLEMENTED"],
            "systems": systems,
        }

    def _dependency_order(self, systems: list[dict[str, Any]]) -> list[dict[str, Any]]:
        priority = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        declaration_order = {system.key: index for index, system in enumerate(SOURCE_SYSTEMS)}
        remaining = {str(system["key"]): system for system in systems}
        ordered: list[dict[str, Any]] = []
        completed: set[str] = set()
        while remaining:
            ready = [
                system
                for system in remaining.values()
                if set(system["depends_on"]).issubset(completed)
            ]
            if not ready:
                ready = list(remaining.values())
            ready.sort(
                key=lambda item: (
                    priority.get(str(item["priority"]), 99),
                    declaration_order.get(str(item["key"]), 999),
                )
            )
            selected = ready[0]
            key = str(selected["key"])
            ordered.append(selected)
            completed.add(key)
            remaining.pop(key)
        return ordered

    def write(self, output_dir: str | Path = "exports") -> dict[str, Any]:
        report = self.scan()
        destination = self.root / output_dir
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "RME_OFFICIAL_SOURCE_GAP_SCAN.json").write_text(
            json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
        )
        (destination / "RME_OFFICIAL_SOURCE_IMPLEMENTATION_PLAN.md").write_text(
            self._markdown(report), encoding="utf-8"
        )
        return report

    def _scan_system(self, system: SourceSystem) -> dict[str, Any]:
        source = [self._file_result(self.source_root / name, ()) for name in system.source_files]
        probes = [self._file_result(self.root / probe.path, probe.symbols) for probe in system.probes]
        required = sum(len(probe.symbols) for probe in system.probes)
        found = sum(len(result["symbols_found"]) for result in probes)
        ratio = round(found / required, 4) if required else 0.0
        if found == 0:
            status = "MISSING"
        elif found == required and all(result["exists"] for result in probes):
            status = "IMPLEMENTED"
        else:
            status = "PARTIAL"
        return {
            "key": system.key,
            "priority": system.priority,
            "status": status,
            "coverage_ratio": ratio,
            "official_sources": source,
            "agent_probes": probes,
            "weakness": system.weakness_if_incomplete,
            "acceptance": list(system.acceptance),
            "depends_on": list(system.depends_on),
        }

    def _file_result(self, path: Path, symbols: tuple[str, ...]) -> dict[str, Any]:
        exists = path.exists()
        text = path.read_text(encoding="utf-8", errors="ignore") if exists else ""
        return {
            "path": str(path.relative_to(self.root)) if path.is_relative_to(self.root) else str(path),
            "exists": exists,
            "symbols_found": [symbol for symbol in symbols if symbol in text],
            "symbols_missing": [symbol for symbol in symbols if symbol not in text],
        }

    def _markdown(self, report: dict[str, Any]) -> str:
        lines = [
            "# RME Official Source Implementation Plan",
            "",
            f"Systems scanned: {report['systems_scanned']}. Status: {report['status']}.",
            "",
        ]
        implemented = [system for system in report["systems"] if system["status"] == "IMPLEMENTED"]
        lines.extend(
            [
                "## Completed Baseline",
                "",
                *[f"- [{system['priority']}] {system['key']}" for system in implemented],
                "",
                "## Remaining Implementation Steps",
                "",
            ]
        )
        step = 1
        for system in report["systems"]:
            if system["status"] == "IMPLEMENTED":
                continue
            lines.extend(
                [
                    f"## {step}. [{system['priority']}] {system['key']}",
                    "",
                    f"Current status: {system['status']} ({system['coverage_ratio']:.0%}).",
                    "",
                    system["weakness"],
                    "",
                    "Acceptance criteria:",
                    "",
                    *[f"- {criterion}" for criterion in system["acceptance"]],
                    "",
                    f"Dependencies: {', '.join(system['depends_on']) or 'none'}.",
                    "",
                ]
            )
            step += 1
        return "\n".join(lines)


if __name__ == "__main__":
    result = RMESourceGapScanner().write()
    print(json.dumps({key: result[key] for key in ("status", "systems_scanned", "implemented", "partial", "missing")}, indent=2))
