"""PMX-03R1 sprite pixel source discovery and classification."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rme_rendering.asset_paths import resolve_client_asset_root


PIXEL_EXTENSIONS = {".spr", ".bmp", ".png", ".lzma"}
METADATA_EXTENSIONS = {".dat", ".otfi", ".json", ".xml", ".otb"}


@dataclass(frozen=True)
class SpritePixelSourceCandidate:
    path: str
    size: int
    extension: str
    purpose: str
    classification: str
    readable: bool
    referenced_by_canary: bool
    bundled_by_pyinstaller: bool
    contains_pixel_data: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SpriteSheetCatalogEntry:
    first_sprite_id: int
    last_sprite_id: int
    sprite_type: int
    file: str
    path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SpritePixelSourceDiscovery:
    """Finds and classifies local files related to sprite pixels."""

    def __init__(self, workspace_root: str | Path = ".") -> None:
        if getattr(sys, "frozen", False):
            self.workspace_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        else:
            self.workspace_root = Path(workspace_root)
        self.assets_root = resolve_client_asset_root(self.workspace_root)
        self._catalog_cache: list[dict[str, Any]] | None = None
        self.canary_root = (
            self.workspace_root
            / "projects"
            / "canary-extracted"
            / "canary-map-editor-v4.0-windows"
        )

    def discover(self) -> list[SpritePixelSourceCandidate]:
        paths = self._candidate_paths()
        return [self._classify(path) for path in paths]

    def catalog_entries(self) -> list[SpriteSheetCatalogEntry]:
        catalog = self.assets_root / "catalog-content.json"
        if not catalog.exists():
            return []
        try:
            data = json.loads(catalog.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        entries = []
        for obj in data:
            if obj.get("type") != "sprite":
                continue
            file_name = str(obj.get("file", ""))
            entries.append(
                SpriteSheetCatalogEntry(
                    first_sprite_id=int(obj.get("firstspriteid", 0) or 0),
                    last_sprite_id=int(obj.get("lastspriteid", 0) or 0),
                    sprite_type=int(obj.get("spritetype", 0) or 0),
                    file=file_name,
                    path=str((catalog.parent / file_name).resolve()),
                )
            )
        return entries

    def best_pixel_source_state(self) -> str:
        candidates = self.discover()
        if any(candidate.classification == "PIXEL_SOURCE_CONFIRMED" for candidate in candidates):
            return "PIXEL_SOURCE_CONFIRMED"
        if any(candidate.classification == "PIXEL_SOURCE_CANDIDATE" for candidate in candidates):
            return "PIXEL_SOURCE_CANDIDATE"
        return "PIXEL_SOURCE_MISSING"

    def _candidate_paths(self) -> list[Path]:
        names = {
            "catalog-content.json",
            "Tibia.spr",
            "Tibia.dat",
            "client.otb",
            "items.otb",
            "appearances.dat",
        }
        roots = [
            self.assets_root,
            self.canary_root,
            self.workspace_root / "projects" / "world",
        ]
        paths: dict[str, Path] = {}
        catalog = self.assets_root / "catalog-content.json"
        if catalog.exists():
            paths[str(catalog.resolve())] = catalog
            for entry in self._catalog_data(catalog):
                file_name = str(entry.get("file", ""))
                if file_name:
                    path = catalog.parent / file_name
                    if path.exists():
                        paths[str(path.resolve())] = path
        for root in roots:
            if not root.exists():
                continue
            for path in root.glob("*"):
                if not path.is_file():
                    continue
                name = path.name.lower()
                suffix = path.suffix.lower()
                if (
                    path.name in names
                    or suffix in PIXEL_EXTENSIONS
                    or suffix in METADATA_EXTENSIONS
                    or "sprite" in name
                    or "catalog" in name
                    or "thing" in name
                    or "appearance" in name
                ):
                    paths[str(path.resolve())] = path
        return sorted(paths.values(), key=lambda item: str(item).lower())

    def _classify(self, path: Path) -> SpritePixelSourceCandidate:
        suffix = path.suffix.lower()
        readable = self._readable(path)
        referenced = self._referenced_by_canary(path)
        bundled = self._bundled_by_pyinstaller(path)
        purpose = self._purpose(path)
        contains_pixels = False
        classification = "UNKNOWN"
        notes = ""

        if path.name == "catalog-content.json":
            classification = "PIXEL_SOURCE_CANDIDATE"
            notes = "Canary SpriteAppearances::loadCatalogContent expects this catalog to point at sprite sheet files."
        elif suffix == ".spr":
            classification = "PIXEL_SOURCE_CONFIRMED"
            contains_pixels = True
            notes = "Legacy Tibia.spr pixel archive."
        elif path.name.endswith(".bmp.lzma"):
            classification = "PIXEL_SOURCE_CONFIRMED" if referenced else "PIXEL_SOURCE_CANDIDATE"
            contains_pixels = True
            notes = "Catalog-referenced Canary compressed BMP sprite sheet."
        elif suffix in {".bmp", ".png"}:
            lower = str(path).lower().replace("/", "\\")
            if (
                "\\brushes\\" in lower
                or "\\icons\\" in lower
                or "\\assets\\images\\" in lower
                or lower.startswith("assets\\images\\")
            ):
                classification = "METADATA_ONLY"
                notes = "Editor UI/brush icon; not an item sprite sheet."
            else:
                classification = "PIXEL_SOURCE_CANDIDATE"
                contains_pixels = True
        elif path.name == "appearances.dat":
            classification = "METADATA_ONLY"
            notes = "Official appearance metadata; sprite IDs only, not decoded pixels."
        elif suffix in METADATA_EXTENSIONS:
            classification = "METADATA_ONLY"
        else:
            classification = "UNKNOWN"

        return SpritePixelSourceCandidate(
            path=str(path),
            size=path.stat().st_size if path.exists() else 0,
            extension=suffix,
            purpose=purpose,
            classification=classification,
            readable=readable,
            referenced_by_canary=referenced,
            bundled_by_pyinstaller=bundled,
            contains_pixel_data=contains_pixels,
            notes=notes,
        )

    def _purpose(self, path: Path) -> str:
        lower = str(path).lower()
        if path.name == "catalog-content.json":
            return "modern sprite sheet catalog"
        if path.name == "Tibia.spr":
            return "legacy sprite pixel archive"
        if path.name == "Tibia.dat":
            return "legacy metadata file"
        if path.name == "appearances.dat":
            return "official appearance metadata"
        if "\\brushes\\" in lower or "\\icons\\" in lower:
            return "editor UI/brush icon"
        if "\\materials\\" in lower:
            return "RME materials metadata"
        if "\\items\\" in lower:
            return "item metadata"
        return "candidate asset"

    def _readable(self, path: Path) -> bool:
        try:
            with path.open("rb") as handle:
                handle.read(1)
            return True
        except OSError:
            return False

    def _referenced_by_canary(self, path: Path) -> bool:
        if path.name in {"catalog-content.json", "Tibia.spr", "Tibia.dat", "appearances.dat"}:
            return True
        catalog = self.workspace_root / "assets" / "catalog-content.json"
        if catalog.exists() and path.parent.resolve() == catalog.parent.resolve():
            return any(
                isinstance(entry, dict) and entry.get("file") == path.name
                for entry in self._catalog_data(catalog)
            )
        return "\\brushes\\" in str(path).lower() or "\\icons\\" in str(path).lower()

    def _bundled_by_pyinstaller(self, path: Path) -> bool:
        normalized = str(path).replace("\\", "/")
        return "/assets/" in normalized or "/projects/canary-extracted/" in normalized

    def _catalog_data(self, catalog: Path) -> list[dict[str, Any]]:
        if self._catalog_cache is not None:
            return self._catalog_cache
        try:
            data = json.loads(catalog.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        self._catalog_cache = [entry for entry in data if isinstance(entry, dict)]
        return self._catalog_cache
