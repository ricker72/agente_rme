"""
PMX-04R1 — Rendering pipeline that orchestrates the complete rendering process.
paintEvent() → Renderer → ChunkRenderer → TileRenderer → StackRenderer → OverlayRenderer
No direct sprite drawing inside paintEvent().
"""

from __future__ import annotations

import time

from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QPainter

from .camera import Camera
from .chunk_renderer import ChunkRenderer
from .dirty_region_manager import DirtyRegionManager
from .overlay_renderer import OverlayConfig, OverlayRenderer


class FPSCounter:
    """Simple FPS counter with frame timing."""

    def __init__(self) -> None:
        self._frame_count: int = 0
        self._fps_timer: float = time.perf_counter()
        self._fps: float = 0.0
        self._last_frame_time: float = 0.0
        self._frame_times: list[float] = []

    def begin_frame(self) -> None:
        """Call at the start of each frame."""
        self._last_frame_time = time.perf_counter()

    def end_frame(self) -> float:
        """Call at the end of each frame. Returns the frame delta in seconds."""
        now = time.perf_counter()
        delta = now - self._last_frame_time
        self._frame_times.append(delta)

        # Keep last 60 frame times
        if len(self._frame_times) > 60:
            self._frame_times.pop(0)

        self._frame_count += 1
        if now - self._fps_timer >= 1.0:
            elapsed = now - self._fps_timer
            self._fps = self._frame_count / elapsed if elapsed > 0 else 0.0
            self._frame_count = 0
            self._fps_timer = now

        return delta

    @property
    def fps(self) -> float:
        return self._fps

    @property
    def average_frame_time_ms(self) -> float:
        if not self._frame_times:
            return 0.0
        return (sum(self._frame_times) / len(self._frame_times)) * 1000.0

    @property
    def min_frame_time_ms(self) -> float:
        if not self._frame_times:
            return 0.0
        return min(self._frame_times) * 1000.0

    @property
    def max_frame_time_ms(self) -> float:
        if not self._frame_times:
            return 0.0
        return max(self._frame_times) * 1000.0


class RenderingPipeline:
    """Complete rendering pipeline orchestrating all renderers.

    Pipeline:
    paintEvent() → RenderingPipeline.render() → ChunkRenderer → TileRenderer → StackRenderer → OverlayRenderer
    """

    def __init__(
        self,
        chunk_renderer: ChunkRenderer | None = None,
        overlay_renderer: OverlayRenderer | None = None,
        dirty_region_manager: DirtyRegionManager | None = None,
        overlay_config: OverlayConfig | None = None,
    ) -> None:
        self.chunk_renderer = chunk_renderer or ChunkRenderer()
        self.overlay_renderer = overlay_renderer or OverlayRenderer(overlay_config or OverlayConfig())
        self.dirty_region = dirty_region_manager or DirtyRegionManager()
        self.fps_counter = FPSCounter()

        # Performance tracking
        self._last_render_time_ms: float = 0.0
        self._tiles_rendered: int = 0
        self._total_tiles: int = 0

    @property
    def overlay_config(self) -> OverlayConfig:
        return self.overlay_renderer.config

    def render(
        self,
        painter: QPainter,
        camera: Camera,
        tiles: dict[tuple[int, int, int], dict],
        floor: int,
        viewport_rect: QRect,
        selected_tiles: set[tuple[int, int, int]] | None = None,
        hover_tile: tuple[int, int, int] | None = None,
        brush_preview_tiles: list[tuple[int, int, int]] | None = None,
        sel_start: tuple[int, int, int] | None = None,
        sel_current: tuple[int, int, int] | None = None,
        cursor_pos: tuple[float, float] | None = None,
        spawns: list[dict] | None = None,
        waypoints: list[dict] | None = None,
        pz_tiles: set[tuple[int, int, int]] | None = None,
        houses: list[dict] | None = None,
    ) -> None:
        """Execute the complete rendering pipeline for one frame."""
        self.fps_counter.begin_frame()

        # ── Step 1: Background ──────────────────────────────────────────────
        painter.fillRect(viewport_rect, QColor("#0b0d10"))

        # ── Step 2: Chunk Renderer (Tile Rendering) ─────────────────────────
        self._tiles_rendered = self.chunk_renderer.render_visible(
            painter, camera, tiles, floor,
        )
        self._total_tiles = len(tiles)

        # ── Step 3: Overlay Renderer ────────────────────────────────────────
        # Grid
        self.overlay_renderer.render_grid(painter, camera, viewport_rect)

        # Selection
        if selected_tiles:
            self.overlay_renderer.render_selection(painter, camera, selected_tiles, floor)

        # Selection rectangle (in-progress)
        self.overlay_renderer.render_selection_rect(painter, camera, sel_start, sel_current, floor)

        # Brush preview
        if brush_preview_tiles:
            self.overlay_renderer.render_brush_preview(painter, camera, brush_preview_tiles, floor)

        # Tile highlight (hover)
        self.overlay_renderer.render_tile_highlight(painter, camera, hover_tile, floor)

        # Cursor
        self.overlay_renderer.render_cursor(painter, camera, cursor_pos)

        # Spawns
        if spawns:
            self.overlay_renderer.render_spawns(painter, camera, spawns, floor)

        # Waypoints
        if waypoints:
            self.overlay_renderer.render_waypoints(painter, camera, waypoints, floor)

        # Protection zones
        if pz_tiles:
            self.overlay_renderer.render_protection_zones(painter, camera, pz_tiles, floor)

        # Houses
        if houses:
            self.overlay_renderer.render_houses(painter, camera, houses, floor)

        # Chunk borders (debug)
        self.overlay_renderer.render_chunk_borders(painter, camera, viewport_rect)

        # ── Step 4: Debug / FPS Overlay ─────────────────────────────────────
        self.overlay_renderer.render_debug(
            painter,
            fps=self.fps_counter.fps,
            visible_tiles=self._tiles_rendered,
            total_tiles=self._total_tiles,
            floor=floor,
            zoom=camera.zoom,
            hover_tile=hover_tile,
            camera=camera,
            viewport_rect=viewport_rect,
        )

        # Coordinates
        self.overlay_renderer.render_coordinates(
            painter,
            hover_tile=hover_tile,
            floor=floor,
            zoom=camera.zoom,
            visible_tiles=self._tiles_rendered,
            total_tiles=self._total_tiles,
        )

        # ── Step 5: End Frame ───────────────────────────────────────────────
        delta = self.fps_counter.end_frame()
        self._last_render_time_ms = delta * 1000.0

        # Clear dirty regions after render
        self.dirty_region.clear()

    def render_dirty(
        self,
        painter: QPainter,
        camera: Camera,
        tiles: dict[tuple[int, int, int], dict],
        floor: int,
        viewport_rect: QRect,
        selected_tiles: set[tuple[int, int, int]] | None = None,
        hover_tile: tuple[int, int, int] | None = None,
        brush_preview_tiles: list[tuple[int, int, int]] | None = None,
        sel_start: tuple[int, int, int] | None = None,
        sel_current: tuple[int, int, int] | None = None,
        cursor_pos: tuple[float, float] | None = None,
    ) -> None:
        """Render only dirty regions for incremental updates."""
        if self.dirty_region.needs_full_repaint:
            self.render(
                painter, camera, tiles, floor, viewport_rect,
                selected_tiles=selected_tiles,
                hover_tile=hover_tile,
                brush_preview_tiles=brush_preview_tiles,
                sel_start=sel_start,
                sel_current=sel_current,
                cursor_pos=cursor_pos,
            )
            return

        # Render only dirty tiles
        dirty_tiles = self.dirty_region.get_dirty_tiles()
        if dirty_tiles:
            for tx, ty, tz in dirty_tiles:
                if tz != floor:
                    continue
                key = (tx, ty, floor)
                tile_data = tiles.get(key)
                ts = camera.effective_tile_size
                sx, sy = camera.tile_to_screen(tx, ty)
                rect = QRect(int(sx), int(sy), ts, ts)

                if tile_data is not None:
                    self.chunk_renderer.tile_renderer.render_tile(painter, rect)
                else:
                    self.chunk_renderer.tile_renderer.draw_empty_tile(painter, rect)

        # Render dirty screen rects
        for dirty_rect in self.dirty_region.get_dirty_rects():
            painter.fillRect(dirty_rect, QColor("#0b0d10"))

        self.dirty_region.clear()

    def get_performance_report(self) -> dict:
        """Get a performance report for benchmarking."""
        return {
            "fps": self.fps_counter.fps,
            "avg_frame_time_ms": self.fps_counter.average_frame_time_ms,
            "min_frame_time_ms": self.fps_counter.min_frame_time_ms,
            "max_frame_time_ms": self.fps_counter.max_frame_time_ms,
            "tiles_rendered": self._tiles_rendered,
            "total_tiles": self._total_tiles,
            "last_render_time_ms": self._last_render_time_ms,
        }