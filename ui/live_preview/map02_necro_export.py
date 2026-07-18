"""MAP-02 NECRO export path from persisted editor state to OTBM artifacts."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from core.world_generator.otbm_world.fingerprint import sha256_fingerprint
from core.world_generator.otbm_world.model import OtbmItem, OtbmTile, OtbmWorldModel
from core.world_generator.otbm_world.roundtrip import read_otbm_summary
from core.world_generator.otbm_world.serializer import serialize_world
from core.world_generator.otbm_world.validator import validate_serialized_world

from .app_paths import validate_user_project_path
from .map_brushes import VALID_ITEM_IDS, VALID_TERRAIN_IDS


SUPPORTED_TILE_METADATA = {"action_id", "description", "house_id", "text", "tile_flags", "unique_id"}
SUPPORTED_EXPORT_FIELDS = {
    "x",
    "y",
    "z",
    "ground_id",
    "item_id",
    "items",
    "metadata",
    "zone",
    "region",
    "role",
    "brush",
}


@dataclass(frozen=True)
class NecroExportTile:
    x: int
    y: int
    z: int
    ground_id: int | None
    item_ids: tuple[int, ...]
    metadata: dict[str, Any] = field(default_factory=dict)
    zone: str = ""
    region: str = ""
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class NecroExportModel:
    project_id: str
    source_files: dict[str, str]
    tiles: tuple[NecroExportTile, ...]
    bookmarks: tuple[dict[str, Any], ...]
    warnings: tuple[str, ...]

    @property
    def tile_count(self) -> int:
        return len(self.tiles)

    @property
    def item_count(self) -> int:
        return sum(len(tile.item_ids) + (1 if tile.ground_id and tile.ground_id > 0 else 0) for tile in self.tiles)

    @property
    def dimensions(self) -> dict[str, int]:
        if not self.tiles:
            return {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0, "width": 0, "height": 0}
        xs = [tile.x for tile in self.tiles]
        ys = [tile.y for tile in self.tiles]
        return {
            "min_x": min(xs),
            "min_y": min(ys),
            "max_x": max(xs),
            "max_y": max(ys),
            "width": max(xs) + 1,
            "height": max(ys) + 1,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": "NECRO_EXPORT_MODEL",
            "project_id": self.project_id,
            "source_files": self.source_files,
            "tile_count": self.tile_count,
            "item_count": self.item_count,
            "dimensions": self.dimensions,
            "tiles": [asdict(tile) for tile in self.tiles],
            "bookmarks": list(self.bookmarks),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class ExportPrecheck:
    ready: bool
    errors: tuple[dict[str, Any], ...]
    warnings: tuple[dict[str, Any], ...]
    tile_count: int
    item_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact": "NECRO_EXPORT_PRECHECK",
            "ready": self.ready,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "tile_count": self.tile_count,
            "item_count": self.item_count,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


class NecroMap02Exporter:
    """Consumes persisted NECRO state and emits MAP-02 export artifacts."""

    def __init__(self, workspace_root: Path | str = ".", *, project_root: Path | str | None = None) -> None:
        self.workspace_root = Path(workspace_root)
        if project_root is not None:
            self.project_root = validate_user_project_path(project_root)
        elif self.workspace_root.name.upper() == "NECRO":
            self.project_root = validate_user_project_path(self.workspace_root)
        elif self.workspace_root.name.lower() == "projects":
            self.project_root = validate_user_project_path(self.workspace_root / "NECRO")
        else:
            self.project_root = validate_user_project_path(self.workspace_root / "projects" / "NECRO")
        self.export_root = self.project_root / "exports"
        self.metadata_path = self.project_root / "project_metadata.json"
        self.manifest_path = self.project_root / "world_manifest.json"
        self.engine_state_path = self.project_root / "world" / "necro_map_state.json"
        self.workspace_state_path = self.project_root / "project_state.json"

    def run(self) -> dict[str, Any]:
        started = time.perf_counter()
        self.export_root.mkdir(parents=True, exist_ok=True)
        model = self.build_export_model()
        precheck = self.precheck(model)
        self.write_export_model(model)
        self.write_precheck(precheck)

        otbm_path = self.export_root / "necro.otbm"
        roundtrip_report = {"status": "PENDING", "reason": "export precheck failed"}
        binary_written = False
        serializer_available = True
        fingerprint = ""
        validation_errors: list[str] = []

        if precheck.ready:
            world = self.to_otbm_world(model)
            binary, _node_tree = serialize_world(world)
            validation = validate_serialized_world(world, binary)
            validation_errors = list(validation.errors)
            if validation.valid:
                otbm_path.write_bytes(binary)
                binary_written = True
                fingerprint = sha256_fingerprint(binary)
                roundtrip = read_otbm_summary(binary)
                roundtrip_report = {
                    "status": "PASS" if roundtrip.valid else "FAIL",
                    "valid": roundtrip.valid,
                    "tile_count": roundtrip.tile_count,
                    "item_count": roundtrip.item_count,
                    "fingerprint": roundtrip.fingerprint,
                    "errors": list(roundtrip.errors),
                    "matches_export_model": {
                        "tile_count": roundtrip.tile_count == model.tile_count,
                        "item_count": roundtrip.item_count == model.item_count,
                    },
                }
            else:
                roundtrip_report = {
                    "status": "BLOCKED",
                    "reason": "serialized OTBM validation failed",
                    "errors": validation_errors,
                }
        else:
            if otbm_path.exists():
                otbm_path.unlink()

        self.write_roundtrip_report(roundtrip_report)
        self.write_export_log(
            model=model,
            precheck=precheck,
            binary_written=binary_written,
            serializer_available=serializer_available,
            fingerprint=fingerprint,
            validation_errors=validation_errors,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
        )
        if not binary_written:
            self.write_blocked_report(serializer_available, precheck, validation_errors)

        status = {
            "artifact": "MAP-02_NECRO_EXPORT_STATUS",
            "status": "EXECUTION_VERIFIED" if binary_written else "EXPORT_BLOCKED_BY_PRECHECK_OR_SERIALIZER",
            "certification": "NONE",
            "otbm_exported": binary_written,
            "serializer_available": serializer_available,
            "export_path": str(otbm_path) if binary_written else "",
            "tile_count": model.tile_count,
            "item_count": model.item_count,
            "precheck_ready": precheck.ready,
            "error_count": len(precheck.errors),
            "warning_count": len(precheck.warnings),
            "fingerprint": fingerprint,
            "roundtrip": roundtrip_report,
        }
        (self.export_root / "NECRO_EXPORT_STATUS.json").write_text(
            json.dumps(status, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return status

    def build_export_model(self) -> NecroExportModel:
        engine_state = self._load_json(self.engine_state_path, default={})
        workspace_state = self._load_json(self.workspace_state_path, default={})
        metadata = self._load_json(self.metadata_path, default={})
        manifest = self._load_json(self.manifest_path, default={})
        project_id = str(metadata.get("project_id") or engine_state.get("project_id") or manifest.get("project_id") or "PROJECT-01-NECRO")

        source_tiles = self._select_source_tiles(engine_state, workspace_state)
        warnings: list[str] = []
        export_tiles = []
        for tile in source_tiles:
            adapted, tile_warnings = self._adapt_tile(tile)
            warnings.extend(tile_warnings)
            export_tiles.append(adapted)

        bookmarks = []
        for name, coord in sorted((engine_state.get("bookmarks") or {}).items()):
            if isinstance(coord, dict):
                bookmarks.append({"name": name, "x": int(coord["x"]), "y": int(coord["y"]), "z": int(coord.get("z", 7))})

        return NecroExportModel(
            project_id=project_id,
            source_files={
                "project_metadata": str(self.metadata_path),
                "world_manifest": str(self.manifest_path),
                "engine_state": str(self.engine_state_path),
                "workspace_state": str(self.workspace_state_path),
            },
            tiles=tuple(sorted(export_tiles, key=lambda item: (item.z, item.x, item.y))),
            bookmarks=tuple(bookmarks),
            warnings=tuple(warnings),
        )

    def precheck(self, model: NecroExportModel) -> ExportPrecheck:
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        seen: set[tuple[int, int, int]] = set()
        if not model.tiles:
            errors.append({"type": "empty_export_state", "message": "No NECRO tiles available for export"})
        for tile in model.tiles:
            location = [tile.x, tile.y, tile.z]
            key = (tile.x, tile.y, tile.z)
            if key in seen:
                errors.append({"type": "duplicate_tile", "location": location, "message": "Duplicate tile coordinate"})
            seen.add(key)
            if not (0 <= tile.x <= 0xFFFF and 0 <= tile.y <= 0xFFFF):
                errors.append({"type": "invalid_coordinates", "location": location, "message": "Coordinates outside OTBM range"})
            if not (0 <= tile.z <= 15):
                errors.append({"type": "invalid_floor", "location": location, "message": "Floor z outside OpenTibia range 0-15"})
            if tile.ground_id is None:
                warnings.append({"type": "missing_ground", "location": location, "message": "Tile has no ground id"})
            elif tile.ground_id not in VALID_TERRAIN_IDS:
                errors.append({"type": "invalid_ground_id", "location": location, "ground_id": tile.ground_id})
            elif tile.ground_id == 0:
                warnings.append({"type": "missing_ground", "location": location, "message": "Ground id 0 is editor-empty ground and is not serialized as an OTBM item"})
            duplicate_items = sorted({item for item in tile.item_ids if tile.item_ids.count(item) > 1})
            if duplicate_items:
                errors.append({"type": "duplicate_item", "location": location, "item_ids": duplicate_items})
            for item_id in tile.item_ids:
                if item_id not in VALID_ITEM_IDS:
                    errors.append({"type": "invalid_item_id", "location": location, "item_id": item_id})
            for warning in tile.warnings:
                warnings.append({"type": "unsupported_metadata", "location": location, "message": warning})
        return ExportPrecheck(
            ready=not errors and bool(model.tiles),
            errors=tuple(errors),
            warnings=tuple(warnings),
            tile_count=model.tile_count,
            item_count=model.item_count,
        )

    def to_otbm_world(self, model: NecroExportModel) -> OtbmWorldModel:
        tiles = []
        for tile in model.tiles:
            items: list[OtbmItem] = []
            if tile.ground_id and tile.ground_id > 0:
                items.append(OtbmItem(item_id=tile.ground_id, layer="ground", source_id=f"ground:{tile.x},{tile.y},{tile.z}"))
            for index, item_id in enumerate(tile.item_ids):
                items.append(OtbmItem(item_id=item_id, layer="item", source_id=f"item:{tile.x},{tile.y},{tile.z}:{index}"))
            attrs = {key: value for key, value in tile.metadata.items() if key in SUPPORTED_TILE_METADATA}
            tiles.append(OtbmTile(x=tile.x, y=tile.y, z=tile.z, items=tuple(items), attributes=attrs))
        dimensions = model.dimensions
        return OtbmWorldModel(
            width=max(1, dimensions["width"]),
            height=max(1, dimensions["height"]),
            tiles=tuple(tiles),
            metadata={
                "artifact": "NECRO_OTBM_WORLD_MODEL",
                "project_id": model.project_id,
                "source": "PROJECT-01 NECRO MAP-02",
                "certification": "NONE",
            },
            waypoints=model.bookmarks,
        )

    def write_export_model(self, model: NecroExportModel) -> Path:
        self.export_root.mkdir(parents=True, exist_ok=True)
        path = self.export_root / "NECRO_EXPORT_MODEL.json"
        path.write_text(json.dumps(model.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def write_precheck(self, precheck: ExportPrecheck) -> Path:
        self.export_root.mkdir(parents=True, exist_ok=True)
        path = self.export_root / "NECRO_EXPORT_PRECHECK.json"
        path.write_text(json.dumps(precheck.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def write_roundtrip_report(self, roundtrip: dict[str, Any]) -> Path:
        path = self.export_root / "NECRO_ROUNDTRIP_REPORT.md"
        lines = [
            "# NECRO MAP-02 Roundtrip Report",
            "",
            f"Status: {roundtrip.get('status', 'PENDING')}",
            f"Validation: {'available' if roundtrip.get('status') in {'PASS', 'FAIL'} else 'pending'}",
            "",
            "```json",
            json.dumps(roundtrip, indent=2, sort_keys=True),
            "```",
            "",
        ]
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def write_export_log(
        self,
        model: NecroExportModel,
        precheck: ExportPrecheck,
        binary_written: bool,
        serializer_available: bool,
        fingerprint: str,
        validation_errors: Iterable[str],
        elapsed_ms: float,
    ) -> Path:
        path = self.export_root / "NECRO_EXPORT_LOG.txt"
        lines = [
            "MAP-02 NECRO EXPORT LOG",
            f"timestamp={time.strftime('%Y-%m-%dT%H:%M:%S')}",
            "certification=NONE",
            f"serializer_available={serializer_available}",
            f"precheck_ready={precheck.ready}",
            f"tile_count={model.tile_count}",
            f"item_count={model.item_count}",
            f"otbm_exported={binary_written}",
            f"fingerprint={fingerprint}",
            f"elapsed_ms={elapsed_ms}",
            f"errors={len(precheck.errors)}",
            f"warnings={len(precheck.warnings)}",
        ]
        for error in precheck.errors:
            lines.append(f"ERROR {json.dumps(error, sort_keys=True)}")
        for warning in precheck.warnings:
            lines.append(f"WARNING {json.dumps(warning, sort_keys=True)}")
        for error in validation_errors:
            lines.append(f"SERIALIZATION_ERROR {error}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def write_blocked_report(self, serializer_available: bool, precheck: ExportPrecheck, validation_errors: Iterable[str]) -> Path:
        path = self.export_root / "NECRO_OTBM_EXPORT_BLOCKED.md"
        reason = "precheck failed" if precheck.errors else "serialized OTBM validation failed"
        if not serializer_available:
            reason = "Real OTBM binary serialization is not available in the current codebase."
        lines = [
            "# NECRO OTBM Export Blocked",
            "",
            "Certification: NONE",
            f"Reason: {reason}",
            "",
            "Real OTBM binary serialization is not available in the current codebase." if not serializer_available else "Real OTBM binary serialization is available, but export did not pass all gates.",
            "",
            f"Precheck errors: {len(precheck.errors)}",
            f"Precheck warnings: {len(precheck.warnings)}",
        ]
        for error in precheck.errors:
            lines.append(f"- ERROR: {error}")
        for error in validation_errors:
            lines.append(f"- SERIALIZATION_ERROR: {error}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def _select_source_tiles(self, engine_state: dict[str, Any], workspace_state: dict[str, Any]) -> list[dict[str, Any]]:
        engine_tiles = [tile for tile in engine_state.get("tiles", []) if isinstance(tile, dict)]
        if engine_tiles:
            return engine_tiles
        return [tile for tile in workspace_state.get("tiles", []) if self._tile_has_export_content(tile)]

    def _adapt_tile(self, tile: dict[str, Any]) -> tuple[NecroExportTile, list[str]]:
        metadata = dict(tile.get("metadata") or {})
        warnings = []
        for key in sorted(set(tile) - SUPPORTED_EXPORT_FIELDS):
            warnings.append(f"Unsupported tile field ignored: {key}")
        for key in sorted(metadata):
            if key not in SUPPORTED_TILE_METADATA and key not in {"zone", "spawn"}:
                warnings.append(f"Unsupported metadata ignored: {key}")
        zone = str(tile.get("zone") or metadata.get("zone") or "")
        region = str(tile.get("region") or metadata.get("region") or "")
        item_ids = tuple(int(item) for item in tile.get("items", []) if item is not None)
        return (
            NecroExportTile(
                x=int(tile["x"]),
                y=int(tile["y"]),
                z=int(tile.get("z", 7)),
                ground_id=None if tile.get("ground_id") is None else int(tile.get("ground_id")),
                item_ids=item_ids,
                metadata=metadata,
                zone=zone,
                region=region,
                warnings=tuple(warnings),
            ),
            warnings,
        )

    def _tile_has_export_content(self, tile: Any) -> bool:
        if not isinstance(tile, dict):
            return False
        return bool(tile.get("items") or tile.get("metadata") or tile.get("ground_id") not in (None, 0))

    def _load_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))


def run_map02_necro_export(workspace_root: Path | str = ".") -> dict[str, Any]:
    return NecroMap02Exporter(workspace_root).run()
