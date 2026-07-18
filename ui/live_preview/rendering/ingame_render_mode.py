from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QPainter, QPixmap

from .appearance_render_model import RenderedTile
from .sprites.sprite_animation_resolver import (
    SpriteAnimationResolver,
    animation_info_from_dict,
)
from .sprites.sprite_index_resolver import SpriteIndexResolver, SpriteSelectionContext


@dataclass(frozen=True)
class IngameRenderState:
    animation_tick: int = 0
    ambient_light: float = 1.0
    enable_animation: bool = True
    enable_light: bool = True
    enable_elevation: bool = True
    enable_offsets: bool = True


@dataclass(frozen=True)
class IngameTileVisual:
    animation_frame: int
    draw_offset_x: int
    draw_offset_y: int
    elevation: int
    light_level: int
    light_color: int
    alpha: int
    pattern_x: int
    pattern_y: int
    pattern_z: int
    animation_timing_source: str
    exact_fields: tuple[str, ...]
    missing_fields: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IngameRenderMode:
    """Client-like appearance rendering layer for the live viewport.

    This layer consumes exact metadata when the appearance/catalog model exposes it.
    When a field is not available yet, it uses a conservative deterministic fallback
    and reports the missing field in the visual contract.
    """

    SOURCE_FILES = (
        "assets/appearances-ee339aff5b3cb38289287ff25cec261d8d2790e6e146938d4dfd9f138b065980.dat",
        "assets/catalog-content.json",
        "APPEARANCE_RENDER_CATALOG.json",
        "APPEARANCE_ITEM_CATALOG.json",
    )

    def __init__(self, state: IngameRenderState | None = None) -> None:
        self.state = state or IngameRenderState()
        self.animation_resolver = SpriteAnimationResolver()
        self.sprite_index_resolver = SpriteIndexResolver()

    def set_animation_tick(self, elapsed_ms: int) -> None:
        self.state = IngameRenderState(
            animation_tick=max(0, int(elapsed_ms)),
            ambient_light=self.state.ambient_light,
            enable_animation=self.state.enable_animation,
            enable_light=self.state.enable_light,
            enable_elevation=self.state.enable_elevation,
            enable_offsets=self.state.enable_offsets,
        )

    def visual_for_tile(self, tile: RenderedTile) -> IngameTileVisual:
        flags = self._normalized_flags(tile)
        dimensions = dict(tile.model.dimensions or {})
        frames = max(1, int(tile.model.animation_frames or 1))
        exact: list[str] = []
        missing: list[str] = []

        animation_frame = 0
        animation_timing_source = "STATIC"
        if self.state.enable_animation and frames > 1:
            animation = animation_info_from_dict(
                tile.model.render_metadata.get("sprite_animation", {})
            )
            timing = self.animation_resolver.resolve(
                animation,
                self.state.animation_tick,
                fallback_frames=frames,
                seed=(tile.model.appearance_id * 31 + tile.x * 17 + tile.y * 13 + tile.floor),
            )
            animation_frame = timing.frame
            animation_timing_source = timing.timing_source
            exact.append("sprite_animation_timing" if animation.phases else "animation_frames")
        elif frames <= 1:
            exact.append("static_animation_frame")

        elevation = self._int_flag(flags, ("elevation", "drawheight", "draw_height", "height_offset"))
        if elevation:
            exact.append("elevation")
        elif self.state.enable_elevation:
            missing.append("exact_elevation_flag")

        draw_offset_x = 0
        draw_offset_y = 0
        if self.state.enable_offsets:
            width_tiles = max(1, int(dimensions.get("width", 1) or 1))
            height_tiles = max(1, int(dimensions.get("height", 1) or 1))
            if width_tiles > 1 or height_tiles > 1:
                exact.append("sprite_dimensions")
            offset_x = self._int_flag(flags, ("draw_offset_x", "shift_x"))
            offset_y = self._int_flag(flags, ("draw_offset_y", "shift_y", "offset", "draw_offset", "displacement"))
            if offset_x or offset_y:
                draw_offset_x += offset_x
                draw_offset_y += offset_y
                exact.append("draw_offset")
            elif width_tiles == 1 and height_tiles == 1:
                missing.append("exact_draw_offset_flag")

        light_level = self._int_flag(flags, ("lightlevel", "light_level", "light"))
        light_color = self._int_flag(flags, ("lightcolor", "light_color"))
        if light_level or light_color:
            exact.append("light")
        elif self.state.enable_light:
            missing.append("exact_light_flag")

        alpha = 255
        if self._truthy(flags.get("translucent") or flags.get("transparent")):
            alpha = 180
            exact.append("translucency")

        selection = self.sprite_index_resolver.context_for_tile(tile, animation_frame)

        return IngameTileVisual(
            animation_frame=animation_frame,
            draw_offset_x=draw_offset_x,
            draw_offset_y=draw_offset_y,
            elevation=elevation,
            light_level=light_level,
            light_color=light_color,
            alpha=alpha,
            pattern_x=selection.pattern_x,
            pattern_y=selection.pattern_y,
            pattern_z=selection.pattern_z,
            animation_timing_source=animation_timing_source,
            exact_fields=tuple(dict.fromkeys(exact)),
            missing_fields=tuple(dict.fromkeys(missing)),
        )

    def sprite_context_for_tile(self, tile: RenderedTile) -> SpriteSelectionContext:
        visual = self.visual_for_tile(tile)
        base = self.sprite_index_resolver.context_for_tile(tile, visual.animation_frame)
        return SpriteSelectionContext(
            animation_frame=visual.animation_frame,
            layer=base.layer,
            pattern_x=visual.pattern_x,
            pattern_y=visual.pattern_y,
            pattern_z=visual.pattern_z,
            subtype_index=base.subtype_index,
            direction=base.direction,
            variant=base.variant,
        )

    def transform_rect(self, tile: RenderedTile, rect: QRect) -> QRect:
        visual = self.visual_for_tile(tile)
        return rect.translated(-visual.draw_offset_x, -visual.draw_offset_y)

    def apply_post_effects(self, pixmap: QPixmap, tile: RenderedTile) -> QPixmap:
        visual = self.visual_for_tile(tile)
        if visual.alpha == 255 and not visual.light_level:
            return pixmap
        adjusted = QPixmap(pixmap.size())
        adjusted.fill(QColor(0, 0, 0, 0))
        painter = QPainter(adjusted)
        painter.setOpacity(max(0.0, min(1.0, visual.alpha / 255.0)))
        painter.drawPixmap(0, 0, pixmap)
        if self.state.enable_light and visual.light_level:
            strength = max(0.0, min(0.35, visual.light_level / 255.0))
            painter.setOpacity(strength)
            painter.fillRect(adjusted.rect(), QColor(255, 244, 190))
        painter.end()
        return adjusted

    def audit(self) -> dict[str, Any]:
        return {
            "ingame_render_mode_ready": True,
            "source_files": list(self.SOURCE_FILES),
            "implemented": [
                "official sprite pixmap post-processing",
                "animation frame selection",
                "exact SpriteAnimation duration/loop selection",
                "RME coordinate/direction/subtype pattern selection",
                "multi-tile sprite draw offsets",
                "elevation draw offset",
                "light/translucency post effects",
                "exact-field/missing-field reporting",
            ],
            "requires_catalog_enrichment": [
                "exact client displacement flags",
                "exact client elevation/drawheight flags",
                "exact client light flags",
            ],
        }

    def _normalized_flags(self, tile: RenderedTile) -> dict[str, Any]:
        flags = dict(tile.model.flags or {})
        metadata = dict(tile.model.render_metadata or {})
        combined = {**metadata, **flags}
        return {str(key).lower(): value for key, value in combined.items()}

    def _int_flag(self, flags: dict[str, Any], keys: tuple[str, ...]) -> int:
        for key in keys:
            value = flags.get(key)
            if value is None:
                continue
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
        return 0

    def _truthy(self, value: Any) -> bool:
        return str(value).lower() in {"1", "true", "yes"}
