"""
Appearance-backed tile renderer for WG-20U-A.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap

from .appearance_render_model import RenderedTile
from .ingame_render_mode import IngameRenderMode
from .render_cache import RenderCache
from .rme_draw_order import RMEDrawOrderEngine, RMEStackItem
from .rme_visual_compat import rme_stack_from_items
from .sprites import SpriteTileRenderer


class AppearanceTileRenderer:
    """Renders AppearanceRenderModel tiles using fallback pixmap visuals."""

    def __init__(self, cache: RenderCache | None = None) -> None:
        self.cache = cache or RenderCache()
        self.sprite_renderer = SpriteTileRenderer()
        self.draw_order = RMEDrawOrderEngine()
        self.ingame_mode = IngameRenderMode()
        self.use_ingame_mode = False
        self.tiles_rendered = 0
        self.fallback_render_count = 0

    def render_pixmap(self, tile: RenderedTile, tile_size: int) -> QPixmap:
        selection_context = (
            self.ingame_mode.sprite_context_for_tile(tile) if self.use_ingame_mode else None
        )
        sprite_pixmap = self.sprite_renderer.render_pixmap(
            tile,
            tile_size,
            selection_context=selection_context,
        )
        if sprite_pixmap is not None:
            if self.use_ingame_mode:
                return self.ingame_mode.apply_post_effects(sprite_pixmap, tile)
            return sprite_pixmap

        key = self.cache.make_key(
            tile.model.appearance_id,
            tile.floor,
            tile.role,
            tile.brush,
            self._cache_animation_frame(tile),
        )
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        pixmap = QPixmap(tile_size, tile_size)
        if tile.model.render_status != "SPRITE_BACKED":
            pixmap.fill(Qt.GlobalColor.transparent)
        else:
            pixmap.fill(QColor(tile.model.fallback_color))
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor("#0F1115"), 1))
        painter.drawRect(0, 0, tile_size - 1, tile_size - 1)
        if tile.model.render_status != "SPRITE_BACKED":
            self.fallback_render_count += 1
            painter.setPen(QPen(QColor("#E05252"), 2))
            painter.drawLine(0, 0, tile_size - 1, tile_size - 1)
            painter.drawLine(0, tile_size - 1, tile_size - 1, 0)
        else:
            painter.setPen(QPen(QColor("#FFFFFF"), 1))
            label = str(tile.model.appearance_id)[-3:]
            painter.drawText(
                QRect(0, 0, tile_size, tile_size),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )
        painter.end()
        if self.use_ingame_mode:
            pixmap = self.ingame_mode.apply_post_effects(pixmap, tile)
        return self.cache.set(key, pixmap)

    def render_stack_pixmap(self, tiles: list[RenderedTile], tile_size: int) -> QPixmap:
        resolved = []
        cursor_x = cursor_y = 0
        min_x = min_y = 0
        max_x = max_y = tile_size
        for tile in self.ordered_stack(tiles):
            sprite = self.render_pixmap(tile, tile_size)
            visual = self.ingame_mode.visual_for_tile(tile) if self.use_ingame_mode else None
            offset_x = visual.draw_offset_x if visual else 0
            offset_y = visual.draw_offset_y if visual else 0
            draw_x = cursor_x - max(0, sprite.width() - tile_size) - offset_x
            draw_y = cursor_y - max(0, sprite.height() - tile_size) - offset_y
            resolved.append((sprite, draw_x, draw_y))
            min_x = min(min_x, draw_x)
            min_y = min(min_y, draw_y)
            max_x = max(max_x, draw_x + sprite.width())
            max_y = max(max_y, draw_y + sprite.height())
            if visual:
                cursor_x -= visual.elevation
                cursor_y -= visual.elevation

        pixmap = QPixmap(max_x - min_x, max_y - min_y)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        for sprite, draw_x, draw_y in resolved:
            painter.drawPixmap(draw_x - min_x, draw_y - min_y, sprite)
        painter.end()
        return pixmap

    def ordered_stack(self, tiles: list[RenderedTile]) -> list[RenderedTile]:
        source_items = [
            RMEStackItem(
                item_id=tile.model.appearance_id,
                appearance_id=tile.model.appearance_id,
                role=tile.role,
                name=tile.model.name,
                source_index=index,
            )
            for index, tile in enumerate(tiles)
        ]
        ordered = rme_stack_from_items(source_items).render_items()
        lookup = {(item.appearance_id, item.source_index): index for index, item in enumerate(ordered)}
        return [
            tile
            for _index, tile in sorted(
                enumerate(tiles),
                key=lambda indexed: lookup[(indexed[1].model.appearance_id, indexed[0])],
            )
        ]

    def paint_tile(
        self,
        painter: QPainter,
        tile: RenderedTile,
        rect: QRect,
    ) -> None:
        pixmap = self.render_pixmap(tile, rect.width())
        target_x = rect.x() - max(0, pixmap.width() - rect.width())
        target_y = rect.y() - max(0, pixmap.height() - rect.height())
        if self.use_ingame_mode:
            visual = self.ingame_mode.visual_for_tile(tile)
            target_x -= visual.draw_offset_x
            target_y -= visual.draw_offset_y
        painter.drawPixmap(target_x, target_y, pixmap)
        self.tiles_rendered += 1

    def set_ingame_mode(self, enabled: bool) -> None:
        self.use_ingame_mode = bool(enabled)

    def set_animation_tick(self, elapsed_ms: int) -> None:
        self.ingame_mode.set_animation_tick(elapsed_ms)

    def ingame_audit(self) -> dict[str, object]:
        return {
            **self.ingame_mode.audit(),
            "enabled": self.use_ingame_mode,
        }

    def _cache_animation_frame(self, tile: RenderedTile) -> int:
        if not self.use_ingame_mode:
            return 0
        visual = self.ingame_mode.visual_for_tile(tile)
        return 10000 + visual.animation_frame
