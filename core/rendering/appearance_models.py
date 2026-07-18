"""Data models for PMX-03 official appearance rendering."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AppearanceRecord:
    appearance_id: int
    sprite_ids: tuple[int, ...] = ()
    width: int = 1
    height: int = 1
    layers: int = 1
    pattern_width: int = 1
    pattern_height: int = 1
    pattern_depth: int = 1
    animation_frames: int = 1
    source_offset: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AppearanceParseReport:
    source_path: str
    file_size: int
    sha256: str
    header_hex: str
    status: str
    record_count: int
    sprite_reference_count: int
    companion_pixel_sources: tuple[str, ...] = ()
    unsupported_fields: tuple[str, ...] = ()
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResolvedSprite:
    item_id: int
    client_id: int | None
    appearance_id: int | None
    sprite_ids: tuple[int, ...] = ()
    status: str = "UNRESOLVED"
    reason: str = ""
    name: str = ""
    category: str = ""
    source: str = ""

    @property
    def primary_sprite_id(self) -> int | None:
        return self.sprite_ids[0] if self.sprite_ids else None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MaterializedSprite:
    resolved: ResolvedSprite
    status: str
    size: int
    cache_key: tuple[int | str | None, int | str | None, int, int]
    pixel_source: str = ""
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
