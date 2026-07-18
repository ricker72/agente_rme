"""Shared data models for the OpenTibia asset registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class OpenTibiaAsset:
    asset_id: int
    client_id: int | None
    name: str
    category: str
    brush: str
    tileset: str
    source_file: str
    flags: tuple[str, ...] = ()
    appearance_id: int | None = None
    sprite_ids: tuple[int, ...] = ()
    render_status: str = "UNRESOLVED"


@dataclass(frozen=True)
class OpenTibiaBrush:
    name: str
    brush_type: str
    item_id: int | None
    category: str
    source_file: str
    flags: tuple[str, ...] = ()
    item_ids: tuple[int, ...] = ()
    look_id: int | None = None
    server_look_id: int | None = None
    grammar: dict[str, object] = field(default_factory=dict)


@dataclass
class AssetHealth:
    asset_count: int = 0
    category_count: int = 0
    brush_count: int = 0
    tileset_count: int = 0
    appearance_asset_count: int = 0
    sprite_backed_asset_count: int = 0
    catalog_sprite_bundle_count: int = 0
    catalog_sprite_file_count: int = 0
    loaded_sources: list[str] = field(default_factory=list)
    missing_sources: list[str] = field(default_factory=list)
    unsupported_sources: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AssetSourcePaths:
    appearances_dat: Path
    canary_root: Path
    items_xml: Path
    materials_root: Path
    tilesets_root: Path
    brushs_root: Path
    rme_brush_icons_root: Path
