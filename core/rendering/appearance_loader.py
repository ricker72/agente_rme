"""PMX-03 appearance loader backed by official OpenTibia sources."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

from .appearance_models import AppearanceParseReport, AppearanceRecord


class AppearanceLoader:
    """Loads appearance metadata without claiming unsupported pixel decoding."""

    def __init__(
        self,
        appearances_path: str | Path | None = None,
        workspace_root: str | Path = ".",
    ) -> None:
        self.workspace_root = self._runtime_root(Path(workspace_root))
        self.catalog_path = self.workspace_root / "assets" / "catalog-content.json"
        self.catalog_entries: list[dict[str, Any]] = []
        self.appearances_path = (
            self._resolve_appearances_path()
            if appearances_path is None
            else self._absolute_path(Path(appearances_path))
        )
        self.records: dict[int, AppearanceRecord] = {}
        self.report: AppearanceParseReport | None = None

    def load(self) -> "AppearanceLoader":
        try:
            self.catalog_entries = self._load_catalog()
            self.appearances_path = self._resolve_appearances_path()
            raw = self.appearances_path.read_bytes()
            expected_hash = self._hash_from_name(self.appearances_path.name)
            actual_hash = hashlib.sha256(raw).hexdigest()
            if expected_hash and actual_hash != expected_hash:
                raise ValueError(
                    f"catalog hash mismatch for {self.appearances_path.name}: {actual_hash}"
                )
            render_catalog = self._load_json("APPEARANCE_RENDER_CATALOG.json")
            self.records = {
                int(key): self._record_from_catalog(int(key), value)
                for key, value in render_catalog.items()
                if str(key).isdigit()
            }
            sprite_count = sum(len(record.sprite_ids) for record in self.records.values())
            pixel_sources = self._find_companion_pixel_sources()
            status = "APPEARANCE_PARSE_PARTIAL"
            unsupported = (
                "appearances.dat protobuf field semantics are not fully decoded",
                "pixel sprite data is not embedded in the parsed records",
            )
            if not self.records:
                status = "UNSUPPORTED_FORMAT"
                unsupported = ("APPEARANCE_RENDER_CATALOG.json unavailable or empty",)
            self.report = AppearanceParseReport(
                source_path=str(self.appearances_path.resolve()),
                file_size=len(raw),
                sha256=actual_hash,
                header_hex=raw[:32].hex(),
                status=status,
                record_count=len(self.records),
                sprite_reference_count=sprite_count,
                companion_pixel_sources=tuple(str(path) for path in pixel_sources),
                unsupported_fields=unsupported,
            )
        except Exception as exc:
            self.records = {}
            self.report = AppearanceParseReport(
                source_path=str(self.appearances_path),
                file_size=0,
                sha256="",
                header_hex="",
                status="UNSUPPORTED_FORMAT",
                record_count=0,
                sprite_reference_count=0,
                unsupported_fields=("appearance file could not be loaded",),
                error=f"{type(exc).__name__}: {exc}",
            )
        return self

    def record(self, appearance_id: int) -> AppearanceRecord | None:
        return self.records.get(int(appearance_id))

    def to_report(self) -> dict[str, Any]:
        if self.report is None:
            self.load()
        return self.report.to_dict() if self.report is not None else {}

    def _record_from_catalog(self, appearance_id: int, data: dict[str, Any]) -> AppearanceRecord:
        return AppearanceRecord(
            appearance_id=appearance_id,
            sprite_ids=tuple(int(sprite) for sprite in data.get("sprite_ids", []) if int(sprite) > 0),
            width=max(1, int(data.get("width", 1) or 1)),
            height=max(1, int(data.get("height", 1) or 1)),
            layers=max(1, int(data.get("layers", 1) or 1)),
            pattern_width=max(1, int(data.get("pattern_width", 1) or 1)),
            pattern_height=max(1, int(data.get("pattern_height", 1) or 1)),
            pattern_depth=max(1, int(data.get("pattern_depth", 1) or 1)),
            animation_frames=max(1, int(data.get("animation_frames", 1) or 1)),
            source_offset=int(data["offset"]) if "offset" in data else None,
        )

    def _load_json(self, name: str) -> dict[str, Any]:
        path = self.workspace_root / name
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def _find_companion_pixel_sources(self) -> list[Path]:
        matches: list[Path] = []
        for entry in self.catalog_entries or self._load_catalog():
            if entry.get("type") != "sprite":
                continue
            file_name = str(entry.get("file", ""))
            path = self.catalog_path.parent / file_name
            if path.exists():
                matches.append(path)
        roots = [self.appearances_path.parent]
        for root in roots:
            if not root.exists():
                continue
            for pattern in ("*.spr", "*.bmp", "*.png", "*.bmp.lzma"):
                matches.extend(root.glob(pattern))
        return sorted({path.resolve() for path in matches})

    def _resolve_appearances_path(self) -> Path:
        catalog = self._load_catalog()
        for entry in catalog:
            if entry.get("type") == "appearances":
                candidate = self.catalog_path.parent / str(entry.get("file", ""))
                if candidate.exists():
                    return candidate
                raise FileNotFoundError(f"catalog appearances file is missing: {candidate}")
        raise FileNotFoundError(f"catalog appearances entry is missing: {self.catalog_path}")

    def _load_catalog(self) -> list[dict[str, Any]]:
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"missing catalog-content.json: {self.catalog_path}")
        data = json.loads(self.catalog_path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"invalid catalog-content.json: {self.catalog_path}")
        return [entry for entry in data if isinstance(entry, dict)]

    def _absolute_path(self, path: Path) -> Path:
        return path if path.is_absolute() else self.workspace_root / path

    def _runtime_root(self, workspace_root: Path) -> Path:
        if getattr(sys, "frozen", False):
            return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        return workspace_root

    def _hash_from_name(self, name: str) -> str:
        match = re.match(r"appearances-([0-9a-f]{64})\.dat$", name)
        return match.group(1) if match else ""
