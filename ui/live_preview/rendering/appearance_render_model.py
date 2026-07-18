"""
Appearance render model for WG-20U-A.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class AppearanceRenderModel:
    """Renderable appearance metadata derived from authoritative catalogs."""

    appearance_id: int
    name: str
    category: str
    semantic_role: str
    sprite_ids: List[int] = field(default_factory=list)
    dimensions: Dict[str, int] = field(default_factory=dict)
    layers: int = 1
    animation_frames: int = 1
    flags: Dict[str, Any] = field(default_factory=dict)
    render_metadata: Dict[str, Any] = field(default_factory=dict)
    fallback_color: str = "#1D2330"
    render_status: str = "APPEARANCE_BACKED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RenderedTile:
    """Tile plus its resolved appearance and trace metadata."""

    x: int
    y: int
    floor: int
    role: str
    brush: str
    model: AppearanceRenderModel
    trace_id: Optional[str] = None
    event_id: Optional[str] = None
    source_module: Optional[str] = None
    source_dataset: Optional[str] = None
    fallback_used: bool = False
    invalid: bool = False
    subtype: int = 0
    count: int = 1
    direction: int | str | None = None
    variant: int | None = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["appearance"] = self.model.to_dict()
        data.pop("model", None)
        data["appearance_id"] = self.model.appearance_id
        data["appearance_name"] = self.model.name
        data["category"] = self.model.category
        data["semantic_role"] = self.model.semantic_role
        data["sprite_ids"] = self.model.sprite_ids
        data["flags"] = self.model.flags
        data["render_metadata"] = self.model.render_metadata
        data["render_status"] = self.model.render_status
        return data
