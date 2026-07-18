"""
Central RME-like world viewport for WG-20U.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import time

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QWheelEvent
from PySide6.QtWidgets import QSizePolicy, QWidget

from .theme import BACKGROUND, CARD, PRIMARY_GOLD
from .viewport_projection import RMEViewportProjection

BASE_TILE_SIZE = 32


class ViewportWidget(QWidget):
    """Tile viewport with zoom, pan, grid, floor rendering, and selection."""

    tileSelected = Signal(int, int, int)
    tileHovered = Signal(int, int, int)
    selectionCommitted = Signal(int, int, int, int, int)
    cameraChanged = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setMouseTracking(True)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.floor = 7
        self.zoom = 1.0
        self.pan = QPoint(0, 0)
        self.show_grid = False
        self.view_projection_mode = "rme_orthogonal"
        self.projection = RMEViewportProjection(self.view_projection_mode)
        self.show_chunk_borders = False
        self.show_status_overlay = False
        self.visible_region: Tuple[int, int, int, int, int] = (0, 0, 0, 0, self.floor)
        self.visible_tile_count = 0
        self.visible_chunk_count = 0
        self.viewport_fps = 0.0
        self._last_paint_at = time.perf_counter()
        self.selected_tile: Optional[Tuple[int, int, int]] = None
        self.hover_tile: Optional[Tuple[int, int, int]] = None
        self.selected_tiles: set[Tuple[int, int, int]] = set()
        self.preview_tiles: set[Tuple[int, int, int]] = set()
        self._selection_start: Optional[Tuple[int, int, int]] = None
        self._selection_current: Optional[Tuple[int, int, int]] = None
        self.tiles: List[Dict[str, Any]] = []
        self.rendered_tiles: List[Any] = []
        self.appearance_renderer: Optional[Any] = None
        self.sprite_render_models: List[Dict[str, Any]] = []
        self.selected_asset_pixmap: Optional[Any] = None
        self.selected_asset_render_status = ""
        self._drag_start: Optional[QPoint] = None
        self._visual_parity_results: Dict[str, Any] = {}
        self.visual_parity_validator: Optional[Any] = None
        self.brush_consumer: Optional[Any] = None
        self.wall_consumer: Optional[Any] = None
        self.render_adapter: Optional[Any] = None
        self._rendering_tools_loaded = False

    def _ensure_rendering_tools(self) -> None:
        if self._rendering_tools_loaded:
            return
        from .intelligence_correlation.brush_intelligence_consumer import (
            BrushIntelligenceConsumer,
        )
        from .intelligence_correlation.wall_intelligence_consumer import (
            WallIntelligenceConsumer,
        )
        from .rendering import AppearanceTileRenderer
        from .rendering.semantic_tile_render_adapter import SemanticTileRenderAdapter
        from .visual_parity import VisualParityValidator

        self.appearance_renderer = AppearanceTileRenderer()
        self.visual_parity_validator = VisualParityValidator()

        # WG-20U-C-R: Intelligence consumers bridge brush/wall rules to render pipeline.
        self.brush_consumer = BrushIntelligenceConsumer().load()
        self.wall_consumer = WallIntelligenceConsumer().load()
        self.render_adapter = SemanticTileRenderAdapter()
        self.render_adapter.set_brush_appearance_map(
            self.brush_consumer._brush_to_appearance
        )
        self.render_adapter.set_join_overrides(self.wall_consumer.get_join_overrides())
        self._rendering_tools_loaded = True

    def set_floor(self, floor: int) -> None:
        self.floor = max(0, min(15, floor))
        self.update()

    def set_view_projection_mode(self, mode: str) -> None:
        allowed = {"rme_orthogonal", "parallel_oblique_45"}
        self.view_projection_mode = mode if mode in allowed else "rme_orthogonal"
        self.projection = RMEViewportProjection(self.view_projection_mode)
        self._update_visible_region()
        self.update()

    def set_tiles(self, tiles: List[Dict[str, Any]]) -> None:
        self.tiles = tiles
        self.rendered_tiles = []
        if any(tile.get("validate_visual_parity") for tile in tiles):
            self._update_visual_parity()
        else:
            self._visual_parity_results = {}
        self.update()

    def set_selected_tiles(self, tiles: set[Tuple[int, int, int]]) -> None:
        self.selected_tiles = set(tiles)
        self.update()

    def set_preview_tiles(self, tiles: set[Tuple[int, int, int]]) -> None:
        self.preview_tiles = set(tiles)
        self.update()

    def set_rendered_tiles(self, tiles: List[Any]) -> None:
        self.rendered_tiles = tiles
        self._ensure_rendering_tools()
        self.sprite_render_models = [
            self.appearance_renderer.sprite_renderer.build_model(tile).to_dict()
            for tile in tiles
        ]
        self._update_visual_parity()
        self.update()

    def set_selected_asset_reference(self, asset: object | None) -> None:
        if asset is None:
            self.selected_asset_pixmap = None
            self.selected_asset_render_status = ""
            self.update()
            return
        if getattr(asset, "render_status", None) != "SPRITE_BACKED":
            self.selected_asset_pixmap = None
            self.selected_asset_render_status = "REJECTED_NO_REAL_SPRITE"
            self.update()
            return
        try:
            from core.rendering.appearance_loader import AppearanceLoader
            from core.rendering.sprite_cache import SpriteCache
            from core.rendering.sprite_materializer import SpriteMaterializer
            from core.rendering.sprite_resolver import SpriteResolver

            loader = AppearanceLoader().load()
            pixel_sources = (
                loader.report.companion_pixel_sources
                if loader.report is not None
                else ()
            )
            resolver = SpriteResolver(loader)
            cache = SpriteCache(SpriteMaterializer(pixel_sources))
            resolved = resolver.resolve_asset(asset)
            pixmap, material = cache.thumbnail(resolved, size=32)
            self.selected_asset_pixmap = pixmap
            self.selected_asset_render_status = material.status
        except Exception as exc:
            self.selected_asset_pixmap = None
            self.selected_asset_render_status = (
                f"UNSUPPORTED_FORMAT:{type(exc).__name__}"
            )
        self.update()

    def _update_visual_parity(self) -> None:
        source_tiles = self.rendered_tiles if self.rendered_tiles else self.tiles
        if not source_tiles:
            self._visual_parity_results = {}
            return
        self._ensure_rendering_tools()

        def to_dict(tile):
            if isinstance(tile, dict):
                return tile
            return tile.to_dict()

        dict_tiles = [to_dict(t) for t in source_tiles]

        def build_neighbors_map(tiles: list) -> dict:
            neighbors = {}
            for tile in tiles:
                x, y, z = tile.get("x"), tile.get("y"), tile.get("floor", 7)
                key = f"{x},{y},{z}"
                neighbors[key] = {
                    "north": next(
                        (
                            t
                            for t in tiles
                            if t.get("x") == x
                            and t.get("y") == y - 1
                            and t.get("floor", 7) == z
                        ),
                        {},
                    ),
                    "south": next(
                        (
                            t
                            for t in tiles
                            if t.get("x") == x
                            and t.get("y") == y + 1
                            and t.get("floor", 7) == z
                        ),
                        {},
                    ),
                    "east": next(
                        (
                            t
                            for t in tiles
                            if t.get("x") == x + 1
                            and t.get("y") == y
                            and t.get("floor", 7) == z
                        ),
                        {},
                    ),
                    "west": next(
                        (
                            t
                            for t in tiles
                            if t.get("x") == x - 1
                            and t.get("y") == y
                            and t.get("floor", 7) == z
                        ),
                        {},
                    ),
                }
            return neighbors

        neighbors_map = build_neighbors_map(dict_tiles)
        try:
            validation_result = self.visual_parity_validator.validate(
                dict_tiles, neighbors_map
            )
            self._visual_parity_results = validation_result

            # Apply wall join information to tiles for proper rendering
            self._apply_wall_joins_to_tiles(dict_tiles, neighbors_map)

            # WG-20U-C-R: Apply brush intelligence to tile appearance data
            self._apply_brush_intelligence(dict_tiles)
        except Exception:
            self._visual_parity_results = {}

    def _apply_wall_joins_to_tiles(
        self, tiles: List[Dict[str, Any]], neighbors_map: Dict[str, Any]
    ) -> None:
        """Apply wall join information to tile rendering data."""
        for tile in tiles:
            key = f"{tile.get('x', 0)},{tile.get('y', 0)},{tile.get('floor', 7)}"
            neighbors = neighbors_map.get(key, {})

            if str(tile.get("role", "")).upper() == "WALL":
                result = self.visual_parity_validator.wall_engine.preview(
                    tile, neighbors
                )
                join_type = result.get("join_type", "single")
                tile["join_type"] = join_type
                # Apply wall join appearance override
                self._apply_wall_join_appearance(tile)

    def _apply_wall_join_appearance(self, tile: Dict[str, Any]) -> None:
        """Apply wall join appearance override from intelligence consumer."""
        brush = str(tile.get("brush", "")).lower()
        join_type = tile.get("join_type", "")
        if brush and join_type:
            appearance_id = self.wall_consumer.resolve_wall_appearance(brush, join_type)
            if appearance_id > 0:
                tile["appearance_id"] = appearance_id

    def _apply_brush_intelligence(self, tiles: List[Dict[str, Any]]) -> None:
        """Apply brush intelligence to set correct appearance IDs."""
        for tile in tiles:
            brush = str(tile.get("brush", "")).lower()
            if brush and not tile.get("appearance_id"):
                role = (
                    self.brush_consumer.get_brush_role(brush)
                    or str(tile.get("role", "")).upper()
                )
                appearance_id = self.brush_consumer.resolve_brush_appearance(
                    brush, role
                )
                if appearance_id > 0:
                    tile["appearance_id"] = appearance_id
                tile["role"] = role or tile.get("role", "GROUND")

    def zoom_in(self) -> None:
        self.zoom = min(4.0, self.zoom + 0.1)
        self._update_visible_region()
        self.update()

    def zoom_out(self) -> None:
        self.zoom = max(0.25, self.zoom - 0.1)
        self._update_visible_region()
        self.update()

    def screen_to_tile(self, point: QPoint) -> Tuple[int, int, int]:
        size = max(6, int(BASE_TILE_SIZE * self.zoom))
        x, y = self.projection.screen_to_tile(point, size, self.pan)
        return x, y, self.floor

    def _update_visible_region(self) -> None:
        size = max(6, int(BASE_TILE_SIZE * self.zoom))
        top_left = self.screen_to_tile(QPoint(0, 0))
        bottom_right = self.screen_to_tile(QPoint(self.width(), self.height()))
        self.visible_region = (
            min(top_left[0], bottom_right[0]),
            min(top_left[1], bottom_right[1]),
            max(top_left[0], bottom_right[0]),
            max(top_left[1], bottom_right[1]),
            self.floor,
        )
        self.cameraChanged.emit(
            {
                "zoom": self.zoom,
                "pan": (self.pan.x(), self.pan.y()),
                "tile_size": size,
                "visible_region": self.visible_region,
            }
        )

    def paintEvent(self, event: object) -> None:
        now = time.perf_counter()
        elapsed = max(0.0001, now - self._last_paint_at)
        self.viewport_fps = min(240.0, 1.0 / elapsed)
        self._last_paint_at = now
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(BACKGROUND))
        tile_size = max(6, int(BASE_TILE_SIZE * self.zoom))
        self._update_visible_region()
        self.visible_tile_count = 0
        self.visible_chunk_count = self._visible_chunk_count()
        self._paint_tiles(painter, tile_size)
        self._paint_visual_parity(painter, tile_size)
        if self.show_chunk_borders:
            self._paint_chunk_borders(painter, tile_size)
        if self.show_grid:
            self._paint_grid(painter, tile_size)
        self._paint_brush_preview(painter, tile_size)
        self._paint_hover(painter, tile_size)
        self._paint_selection(painter, tile_size)
        if self.show_status_overlay:
            self._paint_status_overlay(painter)

    def resizeEvent(self, event: object) -> None:
        self.update()
        super().resizeEvent(event)
        self._update_visible_region()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            tile = self.screen_to_tile(event.position().toPoint())
            self.selected_tile = tile
            self._selection_start = tile
            self._selection_current = tile
            self.tileSelected.emit(*tile)
            self.update()
        elif event.button() == Qt.MouseButton.MiddleButton:
            self._drag_start = event.position().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        tile = self.screen_to_tile(event.position().toPoint())
        if tile != self.hover_tile:
            self.hover_tile = tile
            self.tileHovered.emit(*tile)
        if self._drag_start is None:
            if self._selection_start is not None:
                self._selection_current = tile
                self.update()
            return
        point = event.position().toPoint()
        self.pan += point - self._drag_start
        self._drag_start = point
        self._update_visible_region()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._drag_start = None
        elif (
            event.button() == Qt.MouseButton.LeftButton
            and self._selection_start is not None
        ):
            end = self.screen_to_tile(event.position().toPoint())
            start = self._selection_start
            self._selection_current = end
            if start != end:
                self.selectionCommitted.emit(
                    start[0], start[1], end[0], end[1], start[2]
                )
            self._selection_start = None
            self._selection_current = None
            self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def _paint_grid(self, painter: QPainter, tile_size: int) -> None:
        painter.setPen(QPen(QColor("#293041"), 1))
        for x in range(self.pan.x() % tile_size, self.width(), tile_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(self.pan.y() % tile_size, self.height(), tile_size):
            painter.drawLine(0, y, self.width(), y)

    def _paint_chunk_borders(self, painter: QPainter, tile_size: int) -> None:
        chunk = tile_size * 16
        painter.setPen(QPen(QColor("#3B465F"), 2))
        for x in range(self.pan.x() % chunk, self.width(), chunk):
            painter.drawLine(x, 0, x, self.height())
        for y in range(self.pan.y() % chunk, self.height(), chunk):
            painter.drawLine(0, y, self.width(), y)

    def _paint_tiles(self, painter: QPainter, tile_size: int) -> None:
        if self.rendered_tiles:
            self._paint_rendered_tiles(painter, tile_size)
            return
        colors = {
            "water": "#235B7A",
            "road": "#6A5B45",
            "building": "#77603F",
            "nature": "#2E6B4F",
            "temple": PRIMARY_GOLD,
            "depot": "#7B87C9",
            "quest": "#8D5FBF",
            "boss": "#A84040",
            "npc": "#48A0A8",
            "spawn": "#9B4B4B",
        }
        fallback = QColor(CARD)
        for tile in self.tiles:
            if tile.get("floor", self.floor) != self.floor:
                continue
            if not self._tile_is_visible(int(tile.get("x", 0)), int(tile.get("y", 0))):
                continue
            rect = self.projection.tile_rect(int(tile.get("x", 0)), int(tile.get("y", 0)), tile_size, self.pan)
            role = str(tile.get("role", "building")).lower()
            painter.fillRect(
                rect,
                QColor(colors.get(role, fallback.name())),
            )
            self.visible_tile_count += 1

    def _paint_rendered_tiles(self, painter: QPainter, tile_size: int) -> None:
        self._ensure_rendering_tools()
        for tile in self.rendered_tiles:
            if tile.floor != self.floor:
                continue
            if not self._tile_is_visible(tile.x, tile.y):
                continue
            width_tiles = int(tile.model.dimensions.get("width", 1) or 1)
            height_tiles = int(tile.model.dimensions.get("height", 1) or 1)
            rect = self.projection.sprite_rect(tile.x, tile.y, tile_size, self.pan, width_tiles, height_tiles)
            self.appearance_renderer.paint_tile(painter, tile, rect)
            if tile.invalid:
                painter.setPen(QPen(QColor("#E05252"), 2))
                painter.drawRect(rect)
            elif tile.brush:
                painter.setPen(QPen(QColor("#D4AF37"), 1))
                painter.drawLine(
                    rect.left(), rect.bottom(), rect.right(), rect.bottom()
                )
            if tile.trace_id:
                painter.setPen(QPen(QColor("#5CC8FF"), 1))
                painter.drawPoint(rect.right() - 2, rect.top() + 2)
            self.visible_tile_count += 1

    def _tile_is_visible(self, x: int, y: int) -> bool:
        min_x, min_y, max_x, max_y, _floor = self.visible_region
        return min_x - 1 <= x <= max_x + 1 and min_y - 1 <= y <= max_y + 1

    def _visible_chunk_count(self) -> int:
        min_x, min_y, max_x, max_y, _floor = self.visible_region
        chunk_min_x = min_x // 16
        chunk_max_x = max_x // 16
        chunk_min_y = min_y // 16
        chunk_max_y = max_y // 16
        return max(0, (chunk_max_x - chunk_min_x + 1) * (chunk_max_y - chunk_min_y + 1))

    def _paint_visual_parity(self, painter: QPainter, tile_size: int) -> None:
        corrections = self._visual_parity_results.get("corrections", [])
        if not corrections:
            return
        painter.setPen(QPen(QColor("#5CC8FF"), 1))
        for correction in corrections[:200]:
            trace = correction.get("trace", {})
            for affected in trace.get("affected_tiles", []):
                if affected.get("floor", self.floor) != self.floor:
                    continue
                x = self.projection.tile_to_screen(int(affected.get("x", 0)), int(affected.get("y", 0)), tile_size, self.pan).x()
                y = self.projection.tile_to_screen(int(affected.get("x", 0)), int(affected.get("y", 0)), tile_size, self.pan).y()
                painter.drawRect(
                    QRect(x + 2, y + 2, max(1, tile_size - 4), max(1, tile_size - 4))
                )

    def visual_parity_results(self) -> Dict[str, Any]:
        return dict(self._visual_parity_results)

    def _paint_selection(self, painter: QPainter, tile_size: int) -> None:
        painter.setPen(QPen(QColor(PRIMARY_GOLD), 2))
        for x, y, z in self.selected_tiles:
            if z == self.floor:
                painter.drawRect(
                    self.projection.tile_rect(x, y, tile_size, self.pan)
                )
        if self.selected_tile is not None:
            x, y, z = self.selected_tile
            if z == self.floor:
                painter.drawRect(
                    self.projection.tile_rect(x, y, tile_size, self.pan)
                )
        if self._selection_start is not None and self._selection_current is not None:
            sx, sy, sz = self._selection_start
            ex, ey, ez = self._selection_current
            if sz == self.floor and ez == self.floor:
                min_x, max_x = sorted((sx, ex))
                min_y, max_y = sorted((sy, ey))
                painter.setPen(QPen(QColor("#5CC8FF"), 2))
                painter.drawRect(
                    QRect(
                        self.projection.tile_to_screen(min_x, min_y, tile_size, self.pan).x(),
                        self.projection.tile_to_screen(min_x, min_y, tile_size, self.pan).y(),
                        (max_x - min_x + 1) * tile_size,
                        (max_y - min_y + 1) * tile_size,
                    )
                )

    def _paint_brush_preview(self, painter: QPainter, tile_size: int) -> None:
        if not self.preview_tiles:
            return
        painter.setPen(QPen(QColor("#5CC8FF"), 1))
        painter.setBrush(QColor(92, 200, 255, 64))
        for x, y, z in self.preview_tiles:
            if z == self.floor:
                painter.drawRect(
                    self.projection.tile_rect(x, y, tile_size, self.pan)
                )
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def _paint_hover(self, painter: QPainter, tile_size: int) -> None:
        if self.hover_tile is None:
            return
        x, y, z = self.hover_tile
        if z != self.floor:
            return
        rect = self.projection.tile_rect(x, y, tile_size, self.pan)
        if self.selected_asset_pixmap is not None:
            painter.setOpacity(0.72)
            painter.drawPixmap(rect, self.selected_asset_pixmap)
            painter.setOpacity(1.0)
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.drawRect(rect)

    def _paint_status_overlay(self, painter: QPainter) -> None:
        region = self.visible_region
        text = (
            f"Zoom {self.zoom:.2f} | FPS {self.viewport_fps:.1f} | "
            f"Visible {region[0]},{region[1]} -> {region[2]},{region[3]} z{region[4]} | "
            f"Tiles {self.visible_tile_count} | Chunks {self.visible_chunk_count}"
        )
        rect = QRect(8, self.height() - 32, min(self.width() - 16, 620), 24)
        painter.fillRect(rect, QColor(10, 14, 22, 210))
        painter.setPen(QPen(QColor("#DDE6F2"), 1))
        painter.drawText(
            rect.adjusted(8, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter, text
        )
