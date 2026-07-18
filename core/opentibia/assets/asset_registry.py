"""Single source of truth for official OpenTibia assets in RME AI Studio."""

from __future__ import annotations

import os
import sys
import json
from pathlib import Path

from .appearance_loader import AppearanceLoader
from .asset_database import AssetHealth, AssetSourcePaths, OpenTibiaAsset, OpenTibiaBrush
from .brush_loader import BrushLoader
from .material_loader import BrushMaterialLoader, ItemDefinitionLoader
from .tileset_loader import TilesetLoader


class AssetLoadError(RuntimeError):
    pass


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def bundled_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return repository_root()


def resolve_asset_sources(root: str | Path | None = None) -> AssetSourcePaths:
    override = os.environ.get("RME_AI_ASSET_ROOT")
    base = Path(override).resolve() if override else Path(root).resolve() if root else bundled_root()
    canary_root = base / "projects" / "canary-extracted" / "canary-map-editor-v4.0-windows"
    return AssetSourcePaths(
        appearances_dat=base / "assets" / "catalog-content.json",
        canary_root=canary_root,
        items_xml=canary_root / "data" / "items" / "items.xml",
        materials_root=canary_root / "data" / "materials",
        tilesets_root=canary_root / "data" / "materials" / "tilesets",
        brushs_root=canary_root / "data" / "materials" / "brushs",
        rme_brush_icons_root=canary_root / "brushes",
    )


class AssetRegistry:
    def __init__(self, root: str | Path | None = None) -> None:
        self.sources = resolve_asset_sources(root)
        self.assets: dict[int, OpenTibiaAsset] = {}
        self.brush_materials: dict[str, OpenTibiaBrush] = {}
        self.brushes: list[OpenTibiaBrush] = []
        self.tilesets: dict[str, set[str]] = {}
        self.appearance_info: dict[str, object] = {}
        self.appearance_item_catalog: dict[str, dict[str, object]] = {}
        self.appearance_render_catalog: dict[str, dict[str, object]] = {}
        self.health = AssetHealth()

    def load(self) -> "AssetRegistry":
        for source in [
            self.sources.appearances_dat,
            self.sources.items_xml,
            self.sources.tilesets_root,
            self.sources.brushs_root,
        ]:
            if not source.exists():
                self.health.missing_sources.append(str(source))
        if self.health.missing_sources:
            raise AssetLoadError("OpenTibia assets could not be loaded. missing file: " + "; ".join(self.health.missing_sources))

        try:
            self.appearance_info = AppearanceLoader(self.sources.appearances_dat).load()
            self.appearance_item_catalog = self._load_root_json("APPEARANCE_ITEM_CATALOG.json")
            self.appearance_render_catalog = self._load_root_json("APPEARANCE_RENDER_CATALOG.json")
            self.assets = ItemDefinitionLoader(self.sources.items_xml).load()
            brush_loader = BrushMaterialLoader(self.sources.brushs_root)
            self.brush_materials = brush_loader.load()
            self.health.unsupported_sources.extend(brush_loader.unsupported_sources)
            tileset_loader = TilesetLoader(self.sources.tilesets_root)
            self.tilesets = tileset_loader.load()
            self.health.unsupported_sources.extend(tileset_loader.unsupported_sources)
        except (FileNotFoundError, ValueError) as exc:
            raise AssetLoadError(f"OpenTibia assets could not be loaded. {exc}") from exc

        self._merge_materials()
        self._attach_appearance_data()
        self.brushes = BrushLoader(list(self.assets.values())).load()
        self._build_health()
        return self

    def _merge_materials(self) -> None:
        for brush in self.brush_materials.values():
            member_ids = brush.item_ids or ((brush.item_id,) if brush.item_id is not None else ())
            if not member_ids:
                continue
            tileset = self._tileset_for_brush(brush.name)
            for member_id in member_ids:
                existing = self.assets.get(member_id)
                merged = OpenTibiaAsset(
                    asset_id=member_id,
                    client_id=existing.client_id if existing else None,
                    name=existing.name if existing else brush.name,
                    category=brush.category,
                    brush=brush.name,
                    tileset=tileset,
                    source_file=brush.source_file,
                    flags=brush.flags + (existing.flags if existing else ()),
                )
                self.assets[member_id] = merged

    def _attach_appearance_data(self) -> None:
        enriched: dict[int, OpenTibiaAsset] = {}
        for asset_id, asset in self.assets.items():
            appearance_id = self._appearance_id_for_asset(asset)
            render = self.appearance_render_catalog.get(str(appearance_id)) if appearance_id is not None else None
            sprite_ids = tuple(int(sprite) for sprite in (render or {}).get("sprite_ids", []) if int(sprite) > 0)
            if sprite_ids:
                render_status = "SPRITE_BACKED"
            elif appearance_id is not None:
                render_status = "APPEARANCE_ONLY"
            else:
                render_status = "UNRESOLVED"
            enriched[asset_id] = OpenTibiaAsset(
                asset_id=asset.asset_id,
                client_id=appearance_id or asset.client_id,
                name=asset.name,
                category=asset.category,
                brush=asset.brush,
                tileset=asset.tileset,
                source_file=asset.source_file,
                flags=asset.flags,
                appearance_id=appearance_id,
                sprite_ids=sprite_ids,
                render_status=render_status,
            )
        self.assets = enriched

    def _appearance_id_for_asset(self, asset: OpenTibiaAsset) -> int | None:
        item = self.appearance_item_catalog.get(str(asset.asset_id), {})
        for key in ("appearance_id", "client_id", "lookid", "id"):
            value = item.get(key)
            if value is not None and str(value).isdigit() and str(value) in self.appearance_render_catalog:
                return int(value)
        for brush in item.get("brushes", []) or []:
            if not isinstance(brush, dict):
                continue
            lookid = brush.get("lookid")
            if lookid is not None and str(lookid).isdigit() and str(lookid) in self.appearance_render_catalog:
                return int(lookid)
        if str(asset.asset_id) in self.appearance_render_catalog:
            return int(asset.asset_id)
        return None

    def _tileset_for_brush(self, brush_name: str) -> str:
        key = brush_name.lower()
        for tileset, brushes in self.tilesets.items():
            if key in brushes:
                return tileset
        return "Materials"

    def _build_health(self) -> None:
        categories = {asset.category for asset in self.assets.values()}
        self.health.asset_count = len(self.assets)
        self.health.category_count = len(categories)
        self.health.brush_count = len(self.brush_materials) + len(self.brushes)
        self.health.tileset_count = len(self.tilesets)
        self.health.appearance_asset_count = sum(1 for asset in self.assets.values() if asset.appearance_id is not None)
        self.health.sprite_backed_asset_count = sum(1 for asset in self.assets.values() if asset.sprite_ids)
        self.health.catalog_sprite_bundle_count = int(self.appearance_info.get("sprite_bundle_count", 0) or 0)
        self.health.catalog_sprite_file_count = int(self.appearance_info.get("sprite_file_count", 0) or 0)
        self.health.loaded_sources = [
            str(self.sources.appearances_dat),
            str(self.sources.items_xml),
            str(self.sources.tilesets_root),
            str(self.sources.brushs_root),
        ]
        if self.appearance_info:
            source = self.appearance_info.get("source")
            if source:
                self.health.loaded_sources.append(str(source))

    def categories(self) -> list[str]:
        required_order = [
            "Terrain",
            "Grounds",
            "Nature",
            "Mountains",
            "Water",
            "Roads",
            "Borders",
            "Walls",
            "Buildings",
            "Houses",
            "Decoration",
            "Depot",
            "Furniture",
            "Containers",
            "Effects",
            "Raw Items",
        ]
        available = {asset.category for asset in self.assets.values()}
        if "Grounds" in available:
            available.add("Terrain")
        if self.search("border"):
            available.add("Borders")
        return [category for category in required_order if category in available] + sorted(available - set(required_order))

    def assets_by_category(self, category: str) -> list[OpenTibiaAsset]:
        if category == "Terrain":
            category = "Grounds"
        if category == "Borders":
            return sorted(
                (asset for asset in self.assets.values() if asset.category == "Borders" or "border" in asset.name.lower()),
                key=lambda item: (item.name, item.asset_id),
            )
        return sorted((asset for asset in self.assets.values() if asset.category == category), key=lambda item: (item.name, item.asset_id))

    def search(self, text: str, category: str | None = None) -> list[OpenTibiaAsset]:
        needle = text.lower()
        assets = self.assets_by_category(category) if category else self.assets.values()
        return sorted(
            (asset for asset in assets if needle in asset.name.lower() or needle in str(asset.asset_id)),
            key=lambda item: (item.name, item.asset_id),
        )

    def asset(self, asset_id: int) -> OpenTibiaAsset | None:
        return self.assets.get(asset_id)

    def health_report(self) -> dict[str, object]:
        return {
            "asset_count": self.health.asset_count,
            "category_count": self.health.category_count,
            "brush_count": self.health.brush_count,
            "tileset_count": self.health.tileset_count,
            "appearance_asset_count": self.health.appearance_asset_count,
            "sprite_backed_asset_count": self.health.sprite_backed_asset_count,
            "catalog_sprite_bundle_count": self.health.catalog_sprite_bundle_count,
            "catalog_sprite_file_count": self.health.catalog_sprite_file_count,
            "loaded_sources": list(dict.fromkeys(self.health.loaded_sources)),
            "missing_sources": self.health.missing_sources,
            "unsupported_sources": self.health.unsupported_sources,
            "warnings": self.health.warnings,
            "appearance": self.appearance_info,
        }

    def sprite_backed_assets_by_category(self, category: str) -> list[OpenTibiaAsset]:
        return [asset for asset in self.assets_by_category(category) if asset.render_status == "SPRITE_BACKED"]

    def necro_required_assets(self) -> dict[str, bool]:
        checks = {
            "Venore walls": ("venore", "wall"),
            "Venore floors": ("venore",),
            "Wood": ("wood",),
            "Stone": ("stone",),
            "Grass": ("grass",),
            "Swamp": ("swamp",),
            "Nature": ("tree",),
            "Trees": ("tree",),
            "Roads": ("road",),
            "Depot": ("depot",),
            "Shops": ("shop",),
            "Water": ("water",),
            "Bridges": ("bridge",),
            "Decoration": ("statue",),
        }
        names = " ".join(asset.name.lower() for asset in self.assets.values())
        return {label: all(token in names for token in tokens) for label, tokens in checks.items()}

    def _load_root_json(self, name: str) -> dict[str, dict[str, object]]:
        path = self.sources.canary_root.parents[2] / name
        if not path.exists():
            self.health.warnings.append(f"missing appearance catalog: {path}")
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
