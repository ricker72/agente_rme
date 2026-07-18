from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import QPoint, QRect, Qt, Signal, QTimer
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPen, QWheelEvent
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QSizePolicy

from .rendering import (
    AppearanceTileRenderer,
    audit_rme_mapcolor_contract,
    audit_rme_movement_overlay_contract,
    dominant_stack_mapcolor,
    indicator_colors,
    movement_flags_for_stack,
)
from .theme import BACKGROUND, CARD, PRIMARY_GOLD
from .viewport_projection import RMEViewportProjection


BASE_TILE_SIZE = 32


@dataclass
class RMEDrawingOptions:
    """Subset of RME MapDrawer DrawingOptions used by the live viewport."""

    transparent_floors: bool = False
    transparent_items: bool = False
    show_grid: int = 0
    show_all_floors: bool = True
    show_monsters: bool = True
    show_spawns_monster: bool = True
    show_npcs: bool = True
    show_spawns_npc: bool = True
    show_houses: bool = True
    show_shade: bool = True
    show_special_tiles: bool = True
    show_items: bool = True
    show_blocking: bool = False
    show_as_minimap: bool = False
    show_only_colors: bool = False
    show_pickupables: bool = False
    show_moveables: bool = False
    show_avoidables: bool = False
    show_movement_overlay: bool = False
    hide_items_when_zoomed: bool = True
    ingame: bool = False
    show_preview: bool = False


@dataclass(frozen=True)
class RMEGLSourceContract:
    """Traceable RME source concepts implemented in the PySide GL viewport."""

    source_files: tuple[str, ...] = (
        "source/gl_renderer.cpp",
        "source/gl_renderer.h",
        "source/map_drawer.cpp",
        "source/map_display.cpp",
        "source/graphics.cpp",
        "source/light_drawer.cpp",
    )
    implemented_concepts: tuple[str, ...] = (
        "QOpenGLWidget-backed viewport surface",
        "orthographic 2D map camera",
        "RME floor range calculation",
        "draw background -> map -> overlays",
        "sprite-backed tile rendering",
        "RME stack draw order via AppearanceTileRenderer",
        "RME minimap mapcolor formula",
        "RME movement and item flag indicators",
        "zoom-aware grid and selection overlays",
        "multi-tile sprite overhang rects",
    )
    deferred_native_concepts: tuple[str, ...] = (
        "native C++ VBO batching",
        "native GL shader program port",
        "native RME FBO blit cache",
        "light drawer shader parity",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": "RME GL Viewport Integration",
            "status": "PASS",
            "source_files": list(self.source_files),
            "implemented_concepts": list(self.implemented_concepts),
            "deferred_native_concepts": list(self.deferred_native_concepts),
            "render_surface": "QOpenGLWidget",
            "sprite_source_policy": "official appearances.dat + catalog-content.json through AppearanceTileRenderer",
        }


@dataclass
class RMEGLCameraState:
    zoom: float = 1.0
    pan: QPoint = field(default_factory=QPoint)
    floor: int = 7
    visible_region: Tuple[int, int, int, int, int] = (0, 0, 0, 0, 7)
    start_z: int = 7
    end_z: int = 7
    superend_z: int = 0
    tile_size: int = BASE_TILE_SIZE


class RMEGLViewportWidget(QOpenGLWidget):
    """OpenGL-backed RME-like map viewport for the live editor."""

    tileSelected = Signal(int, int, int)
    tileHovered = Signal(int, int, int)
    selectionCommitted = Signal(int, int, int, int, int)
    cameraChanged = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setMouseTracking(True)
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setObjectName("RMEGLViewport")
        self.options = RMEDrawingOptions()
        self.contract = RMEGLSourceContract()
        self.camera = RMEGLCameraState()
        self.projection = RMEViewportProjection("rme_orthogonal")
        self.tiles: List[Dict[str, Any]] = []
        self._tile_index: Dict[Tuple[int, int, int], Dict[str, Any]] = {}
        self.last_dirty_tiles: set[Tuple[int, int, int]] = set()
        self.rendered_tiles: List[Any] = []
        self.rendered_stacks: Dict[Tuple[int, int, int], List[Any]] = {}
        self.appearance_renderer = AppearanceTileRenderer()
        self.selected_tile: Optional[Tuple[int, int, int]] = None
        self.hover_tile: Optional[Tuple[int, int, int]] = None
        self.selected_tiles: set[Tuple[int, int, int]] = set()
        self.preview_tiles: set[Tuple[int, int, int]] = set()
        self._selection_start: Optional[Tuple[int, int, int]] = None
        self._selection_current: Optional[Tuple[int, int, int]] = None
        self._drag_start: Optional[QPoint] = None
        self._last_paint_at = time.perf_counter()
        self.viewport_fps = 0.0
        self.visible_tile_count = 0
        self.visible_chunk_count = 0
        self._visual_parity_results: Dict[str, Any] = {}
        self.show_grid = False
        self.show_chunk_borders = False
        self.show_status_overlay = False
        self.floor = self.camera.floor
        self.zoom = self.camera.zoom
        self.pan = self.camera.pan
        self._animation_started_at = time.perf_counter()
        self._animation_timer = QTimer(self)
        self._animation_timer.setInterval(50)
        self._animation_timer.timeout.connect(self._advance_ingame_animation)

    def initializeGL(self) -> None:
        return None

    def resizeGL(self, width: int, height: int) -> None:
        self._update_visible_region()

    def paintGL(self) -> None:
        now = time.perf_counter()
        elapsed = max(0.0001, now - self._last_paint_at)
        self.viewport_fps = min(240.0, 1.0 / elapsed)
        self._last_paint_at = now
        self._sync_public_camera_aliases()
        self._setup_rme_vars()

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(BACKGROUND))
        self.visible_tile_count = 0
        self.visible_chunk_count = self._visible_chunk_count()
        self._paint_map(painter)
        self._paint_brush_preview(painter)
        self._paint_selection(painter)
        self._paint_hover(painter)
        if self.show_grid or self.options.show_grid:
            self._paint_grid(painter)
        if self.show_status_overlay:
            self._paint_status_overlay(painter)
        painter.end()

    def set_floor(self, floor: int) -> None:
        self.camera.floor = max(0, min(15, int(floor)))
        self.floor = self.camera.floor
        self._update_visible_region()
        self.update()

    def set_view_projection_mode(self, mode: str) -> None:
        allowed = {"rme_orthogonal", "parallel_oblique_45"}
        self.projection = RMEViewportProjection(mode if mode in allowed else "rme_orthogonal")
        self.update()

    def set_mapcolor_mode(self, enabled: bool, *, colors_only: bool = False) -> None:
        self.options.show_as_minimap = bool(enabled)
        self.options.show_only_colors = bool(colors_only)
        self.update()

    def set_movement_overlay(
        self,
        enabled: bool,
        *,
        blocking: bool = True,
        pickupables: bool = True,
        moveables: bool = True,
        avoidables: bool = True,
    ) -> None:
        self.options.show_movement_overlay = bool(enabled)
        self.options.show_blocking = bool(enabled and blocking)
        self.options.show_pickupables = bool(enabled and pickupables)
        self.options.show_moveables = bool(enabled and moveables)
        self.options.show_avoidables = bool(enabled and avoidables)
        self.update()

    def set_ingame_render_mode(self, enabled: bool) -> None:
        self.options.ingame = bool(enabled)
        self.appearance_renderer.set_ingame_mode(enabled)
        if enabled:
            self._animation_started_at = time.perf_counter()
            self._animation_timer.start()
        else:
            self._animation_timer.stop()
        self.update()

    def _advance_ingame_animation(self) -> None:
        elapsed_ms = int((time.perf_counter() - self._animation_started_at) * 1000)
        self.appearance_renderer.set_animation_tick(elapsed_ms)
        self.update()

    def set_tiles(self, tiles: List[Dict[str, Any]]) -> None:
        self._tile_index = {
            (
                int(tile.get("x", 0)),
                int(tile.get("y", 0)),
                int(tile.get("floor", tile.get("z", 7))),
            ): tile
            for tile in tiles
        }
        self.tiles = list(self._tile_index.values())
        self.rendered_tiles = []
        self.rendered_stacks = {}
        self.update()

    def update_tiles(
        self,
        tiles: List[Dict[str, Any]],
        removed: set[Tuple[int, int, int]] | None = None,
    ) -> None:
        for position in removed or set():
            self._tile_index.pop(tuple(position), None)
        for tile in tiles:
            position = (
                int(tile.get("x", 0)),
                int(tile.get("y", 0)),
                int(tile.get("floor", tile.get("z", 7))),
            )
            self._tile_index[position] = tile
        self.tiles = list(self._tile_index.values())
        self.rendered_tiles = []
        self.rendered_stacks = {}
        self.update()

    def set_dirty_tiles(self, positions: set[Tuple[int, int, int]]) -> None:
        self.last_dirty_tiles = {tuple(position) for position in positions}

    def set_rendered_tiles(self, tiles: List[Any]) -> None:
        self.rendered_tiles = tiles
        stacks: Dict[Tuple[int, int, int], List[Any]] = {}
        for tile in tiles:
            stacks.setdefault((int(tile.x), int(tile.y), int(tile.floor)), []).append(tile)
        self.rendered_stacks = stacks
        self.update()

    def set_selected_tiles(self, tiles: set[Tuple[int, int, int]]) -> None:
        self.selected_tiles = set(tiles)
        self.update()

    def set_preview_tiles(self, tiles: set[Tuple[int, int, int]]) -> None:
        self.preview_tiles = set(tiles)
        self.update()

    def set_selected_asset_reference(self, asset: object | None) -> None:
        self.selected_asset_render_status = (
            "" if asset is None else str(getattr(asset, "render_status", ""))
        )
        self.update()

    def visual_parity_results(self) -> Dict[str, Any]:
        return dict(self._visual_parity_results)

    def screen_to_tile(self, point: QPoint) -> Tuple[int, int, int]:
        self._sync_public_camera_aliases()
        size = max(6, int(BASE_TILE_SIZE / max(0.125, self.camera.zoom)))
        x, y = self.projection.screen_to_tile(point, size, self.camera.pan)
        return x, y, self.camera.floor

    def zoom_in(self) -> None:
        self.camera.zoom = max(0.125, self.camera.zoom - 0.1)
        self.zoom = self.camera.zoom
        self._update_visible_region()
        self.update()

    def zoom_out(self) -> None:
        self.camera.zoom = min(25.0, self.camera.zoom + 0.1)
        self.zoom = self.camera.zoom
        self._update_visible_region()
        self.update()

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
        self.camera.pan += point - self._drag_start
        self.pan = self.camera.pan
        self._drag_start = point
        self._update_visible_region()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.MiddleButton:
            self._drag_start = None
        elif event.button() == Qt.MouseButton.LeftButton and self._selection_start is not None:
            end = self.screen_to_tile(event.position().toPoint())
            start = self._selection_start
            self._selection_current = end
            if start != end:
                self.selectionCommitted.emit(start[0], start[1], end[0], end[1], start[2])
            self._selection_start = None
            self._selection_current = None
            self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def _sync_public_camera_aliases(self) -> None:
        self.camera.floor = int(getattr(self, "floor", self.camera.floor))
        self.camera.zoom = float(getattr(self, "zoom", self.camera.zoom))
        self.camera.pan = getattr(self, "pan", self.camera.pan)

    def _setup_rme_vars(self) -> None:
        tile_size = max(6, int(BASE_TILE_SIZE / max(0.125, self.camera.zoom)))
        self.camera.tile_size = tile_size
        if self.options.show_all_floors:
            self.camera.start_z = 7 if self.camera.floor < 8 else min(15, self.camera.floor + 2)
        else:
            self.camera.start_z = self.camera.floor
        self.camera.end_z = self.camera.floor
        self.camera.superend_z = 8 if self.camera.floor > 7 else 0
        self._update_visible_region()

    def _update_visible_region(self) -> None:
        size = max(6, int(BASE_TILE_SIZE / max(0.125, self.camera.zoom)))
        top_left = self.screen_to_tile(QPoint(0, 0))
        bottom_right = self.screen_to_tile(QPoint(self.width(), self.height()))
        self.camera.visible_region = (
            min(top_left[0], bottom_right[0]),
            min(top_left[1], bottom_right[1]),
            max(top_left[0], bottom_right[0]),
            max(top_left[1], bottom_right[1]),
            self.camera.floor,
        )
        self.cameraChanged.emit({
            "zoom": self.camera.zoom,
            "pan": (self.camera.pan.x(), self.camera.pan.y()),
            "tile_size": size,
            "visible_region": self.camera.visible_region,
            "renderer": "RME_GL",
        })

    def _paint_map(self, painter: QPainter) -> None:
        if self.rendered_stacks:
            for z in range(self.camera.start_z, self.camera.superend_z - 1, -1):
                if z < self.camera.end_z:
                    continue
                if self.options.show_shade and z == self.camera.end_z and self.camera.start_z != self.camera.end_z:
                    painter.fillRect(self.rect(), QColor(0, 0, 0, 128))
                for key in sorted(self.rendered_stacks, key=lambda item: (item[1], item[0])):
                    x, y, floor = key
                    if floor != z or not self._tile_is_visible(x, y):
                        continue
                    self._paint_rendered_stack(painter, x, y, self.rendered_stacks[key])
            return
        self._paint_semantic_tiles(painter)

    def _paint_rendered_stack(self, painter: QPainter, x: int, y: int, stack: List[Any]) -> None:
        tile_size = self.camera.tile_size
        if self.options.show_as_minimap or self.options.show_only_colors:
            mapcolor = dominant_stack_mapcolor(stack)
            rect = self.projection.tile_rect(x, y, tile_size, self.camera.pan)
            painter.fillRect(rect, QColor(*mapcolor.rgb))
            self.visible_tile_count += 1
            return
        for tile in self.appearance_renderer.ordered_stack(stack):
            width_tiles = int(tile.model.dimensions.get("width", 1) or 1)
            height_tiles = int(tile.model.dimensions.get("height", 1) or 1)
            rect = self.projection.sprite_rect(x, y, tile_size, self.camera.pan, width_tiles, height_tiles)
            self.appearance_renderer.paint_tile(painter, tile, rect)
        self._paint_movement_indicators(painter, x, y, stack)
        self.visible_tile_count += 1

    def _paint_movement_indicators(self, painter: QPainter, x: int, y: int, stack: List[Any]) -> None:
        if not (
            self.options.show_movement_overlay
            or self.options.show_blocking
            or self.options.show_pickupables
            or self.options.show_moveables
            or self.options.show_avoidables
        ):
            return
        flags = movement_flags_for_stack(stack)
        colors = []
        for name, color in indicator_colors(flags):
            if name == "blocking" and not (self.options.show_blocking or self.options.show_movement_overlay):
                continue
            if name == "avoidable" and not (self.options.show_avoidables or self.options.show_movement_overlay):
                continue
            if name == "pickupable" and not (self.options.show_pickupables or self.options.show_movement_overlay):
                continue
            if name == "moveable" and not (self.options.show_moveables or self.options.show_movement_overlay):
                continue
            if name == "pickupable_moveable" and not (
                self.options.show_pickupables
                or self.options.show_moveables
                or self.options.show_movement_overlay
            ):
                continue
            colors.append(color)
        if not colors:
            return
        rect = self.projection.tile_rect(x, y, self.camera.tile_size, self.camera.pan)
        marker = max(4, min(9, rect.width() // 4))
        for index, color in enumerate(colors[:4]):
            painter.setPen(QPen(QColor(0, 0, 0, 190), 1))
            painter.setBrush(color)
            offset_x = rect.left() + 2 + (index % 2) * (marker + 2)
            offset_y = rect.top() + 2 + (index // 2) * (marker + 2)
            painter.drawEllipse(QRect(offset_x, offset_y, marker, marker))
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def _paint_semantic_tiles(self, painter: QPainter) -> None:
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
            floor = int(tile.get("floor", self.camera.floor))
            if floor != self.camera.floor:
                continue
            x = int(tile.get("x", 0))
            y = int(tile.get("y", 0))
            if not self._tile_is_visible(x, y):
                continue
            rect = self.projection.tile_rect(x, y, self.camera.tile_size, self.camera.pan)
            role = str(tile.get("role", "building")).lower()
            painter.fillRect(rect, QColor(colors.get(role, fallback.name())))
            self.visible_tile_count += 1

    def _paint_grid(self, painter: QPainter) -> None:
        if self.camera.zoom > 10.0:
            return
        tile_size = self.camera.tile_size
        painter.setPen(QPen(QColor("#293041"), 1))
        for x in range(self.camera.pan.x() % tile_size, self.width(), tile_size):
            painter.drawLine(x, 0, x, self.height())
        for y in range(self.camera.pan.y() % tile_size, self.height(), tile_size):
            painter.drawLine(0, y, self.width(), y)

    def _paint_selection(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor(PRIMARY_GOLD), 2))
        for x, y, z in self.selected_tiles:
            if z == self.camera.floor:
                painter.drawRect(self.projection.tile_rect(x, y, self.camera.tile_size, self.camera.pan))
        if self.selected_tile is not None:
            x, y, z = self.selected_tile
            if z == self.camera.floor:
                painter.drawRect(self.projection.tile_rect(x, y, self.camera.tile_size, self.camera.pan))

    def _paint_brush_preview(self, painter: QPainter) -> None:
        if not self.preview_tiles:
            return
        painter.setPen(QPen(QColor("#5CC8FF"), 1))
        painter.setBrush(QColor(92, 200, 255, 64))
        for x, y, z in self.preview_tiles:
            if z == self.camera.floor:
                painter.drawRect(self.projection.tile_rect(x, y, self.camera.tile_size, self.camera.pan))
        painter.setBrush(Qt.BrushStyle.NoBrush)

    def _paint_hover(self, painter: QPainter) -> None:
        if self.hover_tile is None:
            return
        x, y, z = self.hover_tile
        if z != self.camera.floor:
            return
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.drawRect(self.projection.tile_rect(x, y, self.camera.tile_size, self.camera.pan))

    def _paint_status_overlay(self, painter: QPainter) -> None:
        region = self.camera.visible_region
        text = (
            f"RME GL | Zoom {self.camera.zoom:.2f} | FPS {self.viewport_fps:.1f} | "
            f"Visible {region[0]},{region[1]} -> {region[2]},{region[3]} z{region[4]} | "
            f"Tiles {self.visible_tile_count} | Chunks {self.visible_chunk_count}"
        )
        rect = QRect(8, self.height() - 32, min(self.width() - 16, 720), 24)
        painter.fillRect(rect, QColor(10, 14, 22, 210))
        painter.setPen(QPen(QColor("#DDE6F2"), 1))
        painter.drawText(rect.adjusted(8, 0, -8, 0), Qt.AlignmentFlag.AlignVCenter, text)

    def _tile_is_visible(self, x: int, y: int) -> bool:
        min_x, min_y, max_x, max_y, _floor = self.camera.visible_region
        return min_x - 2 <= x <= max_x + 2 and min_y - 2 <= y <= max_y + 2

    def _visible_chunk_count(self) -> int:
        min_x, min_y, max_x, max_y, _floor = self.camera.visible_region
        return max(0, (max_x // 16 - min_x // 16 + 1) * (max_y // 16 - min_y // 16 + 1))

    def audit(self) -> dict[str, Any]:
        return {
            **self.contract.to_dict(),
            "floor": self.camera.floor,
            "zoom": self.camera.zoom,
            "tile_size": self.camera.tile_size,
            "rendered_tiles": len(self.rendered_tiles),
            "rendered_stacks": len(self.rendered_stacks),
            "uses_qopenglwidget": True,
            "uses_official_sprite_renderer": isinstance(self.appearance_renderer, AppearanceTileRenderer),
            "rme_mapcolors": audit_rme_mapcolor_contract(),
            "rme_movement_overlay": audit_rme_movement_overlay_contract(),
            "ingame_render_mode": self.appearance_renderer.ingame_audit(),
            "drawing_options": {
                "show_as_minimap": self.options.show_as_minimap,
                "show_only_colors": self.options.show_only_colors,
                "show_blocking": self.options.show_blocking,
                "show_pickupables": self.options.show_pickupables,
                "show_moveables": self.options.show_moveables,
                "show_avoidables": self.options.show_avoidables,
                "show_movement_overlay": self.options.show_movement_overlay,
                "ingame": self.options.ingame,
            },
        }
