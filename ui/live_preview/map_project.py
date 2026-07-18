"""
NECRO project bootstrap and JSON editor-state persistence for MAP-01.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

from core.safe_io import atomic_write_json, atomic_write_text, read_json_bounded

from .mapping_engine import MapTile, OpenTibiaMappingEngine, TileCoord


@dataclass(frozen=True)
class MapProject:
    project_id: str
    name: str
    root: Path
    metadata_path: Path
    manifest_path: Path
    state_path: Path


class MapProjectManager:
    """Creates and persists the PROJECT-01 NECRO Safe Mode map workspace."""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = Path(workspace_root)
        self.projects_root = self.workspace_root / "projects"
        self.recent_projects_path = self.projects_root / "recent_projects.json"

    def create_necro_project(self) -> MapProject:
        project = self._project("NECRO")
        project.root.mkdir(parents=True, exist_ok=True)
        (project.root / "world").mkdir(exist_ok=True)
        (project.root / "exports").mkdir(exist_ok=True)
        metadata = {
            "project_id": project.project_id,
            "name": "PROJECT-01 NECRO",
            "type": "OpenTibia",
            "safe_mode": True,
            "otbm_export": "PENDING_REAL_EXPORTER",
            "created_or_updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        manifest = {
            "project_id": project.project_id,
            "world_name": "NECRO",
            "format": "MAP-01_EDITOR_STATE",
            "otbm_path": None,
            "state_path": str(project.state_path),
            "required_loop": [
                "navigate",
                "select",
                "paint_terrain",
                "place_item",
                "inspect",
                "save",
                "reload",
                "export_readiness",
            ],
        }
        self._write_json_if_changed(project.metadata_path, metadata)
        self._write_json_if_changed(project.manifest_path, manifest)
        if not project.state_path.exists():
            self.save_state(project, OpenTibiaMappingEngine(), {"zoom": 1.0, "pan": [0, 0], "floor": 7})
        self.register_recent(project)
        return project

    def save_state(self, project: MapProject, engine: OpenTibiaMappingEngine, viewport: Dict[str, Any]) -> None:
        state = {
            "project_id": project.project_id,
            "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "tiles": [self._tile_to_dict(tile) for tile in engine.tiles.values()],
            "selection": [list(key) for key in sorted(engine.selection)],
            "bookmarks": {name: asdict(coord) for name, coord in engine.bookmarks.items()},
            "recent_locations": [asdict(coord) for coord in engine.recent_locations],
            "cursor": asdict(engine.cursor),
            "viewport": viewport,
            "undo_depth": len(engine.undo_stack),
            "redo_depth": len(engine.redo_stack),
        }
        atomic_write_json(project.state_path, state)

    def load_state(self, project: MapProject) -> OpenTibiaMappingEngine:
        data = read_json_bounded(project.state_path, default={})
        engine = OpenTibiaMappingEngine()
        for item in data.get("tiles", []):
            tile = self._tile_from_dict(item)
            engine.tiles[tile.coord.key()] = tile
        engine.selection = {tuple(key) for key in data.get("selection", [])}  # type: ignore[arg-type]
        engine.bookmarks = {
            name: TileCoord(int(coord["x"]), int(coord["y"]), int(coord.get("z", 7)))
            for name, coord in data.get("bookmarks", {}).items()
        }
        engine.recent_locations = [
            TileCoord(int(coord["x"]), int(coord["y"]), int(coord.get("z", 7)))
            for coord in data.get("recent_locations", [])
        ]
        cursor = data.get("cursor", {"x": 0, "y": 0, "z": 7})
        engine.cursor = TileCoord(int(cursor["x"]), int(cursor["y"]), int(cursor.get("z", 7)))
        engine.synchronize_editor_map()
        return engine

    def load_viewport_state(self, project: MapProject) -> Dict[str, Any]:
        data = read_json_bounded(project.state_path, default={})
        return dict(data.get("viewport", {}))

    def register_recent(self, project: MapProject) -> None:
        self.projects_root.mkdir(parents=True, exist_ok=True)
        recent = []
        if self.recent_projects_path.exists():
            recent = read_json_bounded(self.recent_projects_path, default=[])
        entry = {"project_id": project.project_id, "name": project.name, "path": str(project.root)}
        recent = [item for item in recent if item.get("project_id") != project.project_id]
        recent.insert(0, entry)
        atomic_write_json(self.recent_projects_path, recent[:10])

    def _project(self, slug: str) -> MapProject:
        root = self.projects_root / slug
        return MapProject(
            project_id="PROJECT-01-NECRO",
            name="PROJECT-01 NECRO",
            root=root,
            metadata_path=root / "project_metadata.json",
            manifest_path=root / "world_manifest.json",
            state_path=root / "world" / "necro_map_state.json",
        )

    def _write_json_if_changed(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(payload, indent=2)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            atomic_write_text(path, text)

    def _tile_to_dict(self, tile: MapTile) -> Dict[str, Any]:
        return {
            "x": tile.coord.x,
            "y": tile.coord.y,
            "z": tile.coord.z,
            "role": tile.role,
            "brush": tile.brush,
            "ground_id": tile.ground_id,
            "item_id": tile.item_id,
            "items": list(tile.items),
            "zone": tile.zone,
            "zones": sorted(tile.zones),
            "house_id": tile.house_id,
            "spawn_monsters": list(tile.spawn_monsters),
            "spawn_npcs": list(tile.spawn_npcs),
            "waypoint": tile.waypoint,
            "region": tile.region,
            "metadata": dict(tile.metadata),
        }

    def _tile_from_dict(self, data: Dict[str, Any]) -> MapTile:
        return MapTile(
            coord=TileCoord(int(data["x"]), int(data["y"]), int(data.get("z", 7))),
            role=str(data.get("role", "ground")),
            brush=str(data.get("brush", "terrain")),
            ground_id=data.get("ground_id"),
            item_id=data.get("item_id"),
            items=[int(item) for item in data.get("items", [])],
            zone=str(data.get("zone", "")),
            zones={str(zone) for zone in data.get("zones", [])},
            house_id=(
                int(data["house_id"])
                if data.get("house_id") is not None
                else None
            ),
            spawn_monsters=[str(name) for name in data.get("spawn_monsters", [])],
            spawn_npcs=[str(name) for name in data.get("spawn_npcs", [])],
            waypoint=(str(data["waypoint"]) if data.get("waypoint") else None),
            region=str(data.get("region", "")),
            metadata={str(key): str(value) for key, value in data.get("metadata", {}).items()},
        )
