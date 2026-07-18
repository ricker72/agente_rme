"""
PMX-04R1 — Independent overlay rendering layers.
Each overlay can be independently enabled/disabled.
Supports: Grid, Selection, Spawn, Waypoint, Protection Zone, House, Brush Preview,
Tile Highlight, Cursor, Debug.
"""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF
from PySide6.QtGui import QColor, QFont, QPainter, QPen

from .camera import Camera


class OverlayConfig:
    """Configuration for which overlays are enabled and their visual properties."""

    def __init__(self) -> None:
        # Enable flags
        self.grid_enabled: bool = True
        self.selection_enabled: bool = True
        self.spawn_enabled: bool = False
        self.waypoint_enabled: bool = False
        self.protection_zone_enabled: bool = False
        self.house_enabled: bool = False
        self.brush_preview_enabled: bool = True
        self.tile_highlight_enabled: bool = True
        self.cursor_enabled: bool = True
        self.debug_enabled: bool = True
        self.coordinates_enabled: bool = True
        self.chunk_borders_enabled: bool = False

        # Visual properties
        self.grid_color: QColor = QColor("#293041")
        self.grid_min_zoom: float = 0.25  # Minimum zoom to show grid

        self.selection_color: QColor = QColor("#ff6b35")
        self.selection_fill: QColor = QColor(255, 107, 53, 40)

        self.brush_preview_color: QColor = QColor("#d6b25e")
        self.brush_preview_fill: QColor = QColor(214, 178, 94, 30)

        self.highlight_color: QColor = QColor("#5cc8ff")
        self.highlight_fill: QColor = QColor(92, 200, 255, 30)

        self.cursor_color: QColor = QColor("#ffffff")

        self.debug_text_color: QColor = QColor("#8a8d94")
        self.debug_font_size: int = 11

        self.coordinate_color: QColor = QColor("#8a8d94")

        self.spawn_color: QColor = QColor("#ff4444")
        self.waypoint_color: QColor = QColor("#44ff44")
        self.pz_color: QColor = QColor("#4444ff")
        self.house_color: QColor = QColor("#ffaa00")


class OverlayRenderer:
    """Renders independent overlay layers on top of the tile rendering.

    Each overlay can be independently enabled/disabled via OverlayConfig.
    """

    def __init__(self, config: OverlayConfig | None = None) -> None:
        self.config = config or OverlayConfig()

    # ── Grid ────────────────────────────────────────────────────────────────

    def render_grid(
        self,
        painter: QPainter,
        camera: Camera,
        viewport_rect: QRect,
    ) -> None:
        """Render the grid overlay."""
        if not self.config.grid_enabled:
            return
        if camera.zoom < self.config.grid_min_zoom:
            return

        ts = camera.effective_tile_size
        if ts < 8:
            return

        min_x, min_y, max_x, max_y = camera.get_visible_tile_range()

        painter.setPen(QPen(self.config.grid_color, 1))

        # Vertical lines
        for tx in range(min_x, max_x + 1):
            sx = int(tx * ts + camera.pan_x)
            painter.drawLine(sx, 0, sx, viewport_rect.height())

        # Horizontal lines
        for ty in range(min_y, max_y + 1):
            sy = int(ty * ts + camera.pan_y)
            painter.drawLine(0, sy, viewport_rect.width(), sy)

    # ── Selection ───────────────────────────────────────────────────────────

    def render_selection(
        self,
        painter: QPainter,
        camera: Camera,
        selected_tiles: set[tuple[int, int, int]],
        floor: int,
    ) -> None:
        """Render the selection overlay."""
        if not self.config.selection_enabled or not selected_tiles:
            return

        ts = camera.effective_tile_size

        for tx, ty, tz in selected_tiles:
            if tz != floor:
                continue
            sx, sy = camera.tile_to_screen(tx, ty)
            rect = QRectF(sx, sy, ts, ts)
            painter.fillRect(rect, self.config.selection_fill)
            painter.setPen(QPen(self.config.selection_color, 2))
            painter.drawRect(rect)

    # ── Selection Rectangle ─────────────────────────────────────────────────

    def render_selection_rect(
        self,
        painter: QPainter,
        camera: Camera,
        sel_start: tuple[int, int, int] | None,
        sel_current: tuple[int, int, int] | None,
        floor: int,
    ) -> None:
        """Render the in-progress selection rectangle."""
        if sel_start is None or sel_current is None:
            return
        if sel_start[2] != floor or sel_current[2] != floor:
            return

        ts = camera.effective_tile_size
        sx1 = int(sel_start[0] * ts + camera.pan_x)
        sy1 = int(sel_start[1] * ts + camera.pan_y)
        sx2 = int(sel_current[0] * ts + camera.pan_x)
        sy2 = int(sel_current[1] * ts + camera.pan_y)

        sel_rect = QRect(
            min(sx1, sx2), min(sy1, sy2),
            abs(sx2 - sx1) + ts, abs(sy2 - sy1) + ts,
        )
        painter.fillRect(sel_rect, self.config.highlight_fill)
        painter.setPen(QPen(self.config.highlight_color, 2))
        painter.drawRect(sel_rect)

    # ── Brush Preview ───────────────────────────────────────────────────────

    def render_brush_preview(
        self,
        painter: QPainter,
        camera: Camera,
        preview_tiles: list[tuple[int, int, int]],
        floor: int,
    ) -> None:
        """Render the brush preview overlay."""
        if not self.config.brush_preview_enabled or not preview_tiles:
            return

        ts = camera.effective_tile_size

        for tx, ty, tz in preview_tiles:
            if tz != floor:
                continue
            sx, sy = camera.tile_to_screen(tx, ty)
            rect = QRectF(sx, sy, ts, ts)
            painter.fillRect(rect, self.config.brush_preview_fill)
            painter.setPen(QPen(self.config.brush_preview_color, 2))
            painter.drawRect(rect)

    # ── Tile Highlight ──────────────────────────────────────────────────────

    def render_tile_highlight(
        self,
        painter: QPainter,
        camera: Camera,
        hover_tile: tuple[int, int, int] | None,
        floor: int,
    ) -> None:
        """Render the hover highlight overlay."""
        if not self.config.tile_highlight_enabled or hover_tile is None:
            return

        hx, hy, hz = hover_tile
        if hz != floor:
            return

        ts = camera.effective_tile_size
        sx, sy = camera.tile_to_screen(hx, hy)
        rect = QRectF(sx, sy, ts, ts)
        painter.setPen(QPen(self.config.highlight_color, 2))
        painter.drawRect(rect)

    # ── Cursor ──────────────────────────────────────────────────────────────

    def render_cursor(
        self,
        painter: QPainter,
        camera: Camera,
        cursor_screen_pos: tuple[float, float] | None,
    ) -> None:
        """Render the cursor crosshair overlay."""
        if not self.config.cursor_enabled or cursor_screen_pos is None:
            return

        cx, cy = cursor_screen_pos
        size = 8
        painter.setPen(QPen(self.config.cursor_color, 1))
        painter.drawLine(int(cx - size), int(cy), int(cx + size), int(cy))
        painter.drawLine(int(cx), int(cy - size), int(cx), int(cy + size))

    # ── Debug / FPS ─────────────────────────────────────────────────────────

    def render_debug(
        self,
        painter: QPainter,
        fps: float,
        visible_tiles: int,
        total_tiles: int,
        floor: int,
        zoom: float,
        hover_tile: tuple[int, int, int] | None,
        camera: Camera,
        viewport_rect: QRect,
    ) -> None:
        """Render the debug overlay with FPS, tile counts, and coordinates."""
        if not self.config.debug_enabled:
            return

        painter.setPen(self.config.debug_text_color)
        font = QFont("monospace", self.config.debug_font_size)
        painter.setFont(font)

        lines: list[str] = [
            f"FPS: {fps:.1f}",
            f"Floor: {floor}",
            f"Zoom: {zoom:.2f}x",
            f"Visible: {visible_tiles}",
            f"Total: {total_tiles}",
            f"Pan: ({camera.pan_x:.0f}, {camera.pan_y:.0f})",
        ]

        if hover_tile is not None:
            lines.insert(0, f"Tile: ({hover_tile[0]}, {hover_tile[1]}, {hover_tile[2]})")

        y_offset = 20
        for line in lines:
            painter.drawText(12, y_offset, line)
            y_offset += 16

    # ── Coordinates ─────────────────────────────────────────────────────────

    def render_coordinates(
        self,
        painter: QPainter,
        hover_tile: tuple[int, int, int] | None,
        floor: int,
        zoom: float,
        visible_tiles: int,
        total_tiles: int,
    ) -> None:
        """Render the coordinate status line."""
        if not self.config.coordinates_enabled:
            return

        painter.setPen(self.config.coordinate_color)
        info = f"Floor {floor} | Zoom {zoom:.1f}x | Tiles {visible_tiles} | Total {total_tiles}"
        if hover_tile is not None:
            info = f"({hover_tile[0]}, {hover_tile[1]}, {hover_tile[2]}) | {info}"
        painter.drawText(12, 24, info)

    # ── Spawn ───────────────────────────────────────────────────────────────

    def render_spawns(
        self,
        painter: QPainter,
        camera: Camera,
        spawns: list[dict],
        floor: int,
    ) -> None:
        """Render spawn zone overlays."""
        if not self.config.spawn_enabled or not spawns:
            return

        ts = camera.effective_tile_size
        painter.setPen(QPen(self.config.spawn_color, 2))

        for spawn in spawns:
            sx = spawn.get("x", 0)
            sy = spawn.get("y", 0)
            sz = spawn.get("z", floor)
            if sz != floor:
                continue
            px, py = camera.tile_to_screen(sx, sy)
            painter.drawRect(QRectF(px, py, ts, ts))

    # ── Waypoint ────────────────────────────────────────────────────────────

    def render_waypoints(
        self,
        painter: QPainter,
        camera: Camera,
        waypoints: list[dict],
        floor: int,
    ) -> None:
        """Render waypoint overlays."""
        if not self.config.waypoint_enabled or not waypoints:
            return

        ts = camera.effective_tile_size
        painter.setPen(QPen(self.config.waypoint_color, 2))

        for wp in waypoints:
            wx = wp.get("x", 0)
            wy = wp.get("y", 0)
            wz = wp.get("z", floor)
            if wz != floor:
                continue
            px, py = camera.tile_to_screen(wx, wy)
            painter.drawRect(QRectF(px, py, ts, ts))

    # ── Protection Zone ─────────────────────────────────────────────────────

    def render_protection_zones(
        self,
        painter: QPainter,
        camera: Camera,
        pz_tiles: set[tuple[int, int, int]],
        floor: int,
    ) -> None:
        """Render protection zone overlays."""
        if not self.config.protection_zone_enabled or not pz_tiles:
            return

        ts = camera.effective_tile_size
        painter.setPen(QPen(self.config.pz_color, 1))

        for tx, ty, tz in pz_tiles:
            if tz != floor:
                continue
            px, py = camera.tile_to_screen(tx, ty)
            painter.fillRect(QRectF(px, py, ts, ts), QColor(68, 68, 255, 20))
            painter.drawRect(QRectF(px, py, ts, ts))

    # ── House ───────────────────────────────────────────────────────────────

    def render_houses(
        self,
        painter: QPainter,
        camera: Camera,
        houses: list[dict],
        floor: int,
    ) -> None:
        """Render house overlays."""
        if not self.config.house_enabled or not houses:
            return

        ts = camera.effective_tile_size
        painter.setPen(QPen(self.config.house_color, 2))

        for house in houses:
            hx = house.get("x", 0)
            hy = house.get("y", 0)
            hz = house.get("z", floor)
            if hz != floor:
                continue
            px, py = camera.tile_to_screen(hx, hy)
            painter.drawRect(QRectF(px, py, ts, ts))

    # ── Chunk Borders ───────────────────────────────────────────────────────

    def render_chunk_borders(
        self,
        painter: QPainter,
        camera: Camera,
        viewport_rect: QRect,
    ) -> None:
        """Render chunk border lines for debugging."""
        if not self.config.chunk_borders_enabled:
            return

        min_x, min_y, max_x, max_y = camera.get_visible_tile_range()
        chunk_size = 32
        painter.setPen(QPen(QColor("#ff00ff"), 1))

        # Vertical chunk borders
        for cx in range(min_x // chunk_size, max_x // chunk_size + 2):
            sx = int(cx * chunk_size * camera.effective_tile_size + camera.pan_x)
            painter.drawLine(sx, 0, sx, viewport_rect.height())

        # Horizontal chunk borders
        for cy in range(min_y // chunk_size, max_y // chunk_size + 2):
            sy = int(cy * chunk_size * camera.effective_tile_size + camera.pan_y)
            painter.drawLine(0, sy, viewport_rect.width(), sy)