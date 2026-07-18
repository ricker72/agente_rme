"""
PMX-04R1 — Camera implementation with zoom, pan, center view, smooth scroll,
mouse wheel zoom, and zoom centered on cursor.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QRectF

TILE_SIZE = 32


class Camera:
    """Viewport camera controlling zoom, pan, and smooth scrolling."""

    def __init__(self) -> None:
        # Position in screen pixel space (pan offset)
        self._pan_x: float = 0.0
        self._pan_y: float = 0.0

        # Zoom level (1.0 = 100%)
        self._zoom: float = 1.0

        # Smooth scroll state
        self._target_pan_x: float = 0.0
        self._target_pan_y: float = 0.0
        self._is_smooth_scrolling: bool = False
        self._scroll_start_time: float = 0.0
        self._scroll_duration: float = 0.3  # seconds
        self._scroll_start_x: float = 0.0
        self._scroll_start_y: float = 0.0

        # Viewport size (set by widget)
        self._viewport_width: int = 640
        self._viewport_height: int = 480

    # ── Properties ──────────────────────────────────────────────────────────

    @property
    def pan_x(self) -> float:
        return self._pan_x

    @pan_x.setter
    def pan_x(self, value: float) -> None:
        self._pan_x = value

    @property
    def pan_y(self) -> float:
        return self._pan_y

    @pan_y.setter
    def pan_y(self, value: float) -> None:
        self._pan_y = value

    @property
    def zoom(self) -> float:
        return self._zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        self._zoom = max(0.125, min(8.0, value))

    @property
    def effective_tile_size(self) -> int:
        return max(4, int(TILE_SIZE * self._zoom))

    def set_viewport_size(self, width: int, height: int) -> None:
        """Set the viewport dimensions."""
        self._viewport_width = max(1, width)
        self._viewport_height = max(1, height)

    # ── Pan ─────────────────────────────────────────────────────────────────

    def pan(self, dx: float, dy: float) -> None:
        """Pan the camera by a screen pixel delta."""
        self._pan_x += dx
        self._pan_y += dy
        self._is_smooth_scrolling = False

    def pan_to(self, x: float, y: float) -> None:
        """Set the camera pan position directly."""
        self._pan_x = x
        self._pan_y = y
        self._is_smooth_scrolling = False

    # ── Zoom ────────────────────────────────────────────────────────────────

    def zoom_abs(self, value: float) -> None:
        """Set absolute zoom level."""
        self.zoom = value

    def zoom_in(self) -> None:
        """Zoom in by one step."""
        self._zoom = max(0.125, min(8.0, self._zoom * 1.25))

    def zoom_out(self) -> None:
        """Zoom out by one step."""
        self._zoom = max(0.125, min(8.0, self._zoom / 1.25))

    def zoom_reset(self) -> None:
        """Reset zoom to 1.0."""
        self._zoom = 1.0

    def zoom_centered_on_screen(self, factor: float, screen_x: float, screen_y: float) -> None:
        """Zoom centered on a specific screen point (e.g., cursor position).
        The world point under (screen_x, screen_y) stays fixed.
        """
        old_ts = self.effective_tile_size
        self._zoom = max(0.125, min(8.0, self._zoom * factor))
        new_ts = self.effective_tile_size

        # World coordinate under cursor before zoom
        world_x = (screen_x - self._pan_x) / old_ts
        world_y = (screen_y - self._pan_y) / old_ts

        # Adjust pan so same world point is under cursor after zoom
        self._pan_x = screen_x - world_x * new_ts
        self._pan_y = screen_y - world_y * new_ts

    # ── Center View ─────────────────────────────────────────────────────────

    def center_on(self, tile_x: int, tile_y: int) -> None:
        """Center the view on a specific tile coordinate."""
        ts = self.effective_tile_size
        self._pan_x = (self._viewport_width / 2.0) - (tile_x * ts)
        self._pan_y = (self._viewport_height / 2.0) - (tile_y * ts)
        self._is_smooth_scrolling = False

    def center_on_smooth(self, tile_x: int, tile_y: int, duration: float = 0.3) -> None:
        """Smoothly scroll to center on a tile coordinate."""
        ts = self.effective_tile_size
        self._target_pan_x = (self._viewport_width / 2.0) - (tile_x * ts)
        self._target_pan_y = (self._viewport_height / 2.0) - (tile_y * ts)
        self._scroll_start_x = self._pan_x
        self._scroll_start_y = self._pan_y
        self._scroll_start_time = time.perf_counter()
        self._scroll_duration = max(0.05, duration)
        self._is_smooth_scrolling = True

    # ── Smooth Scroll Update ────────────────────────────────────────────────

    def update_smooth_scroll(self) -> bool:
        """Update smooth scroll animation. Returns True if still animating."""
        if not self._is_smooth_scrolling:
            return False

        elapsed = time.perf_counter() - self._scroll_start_time
        t = min(1.0, elapsed / self._scroll_duration)

        # Smooth step interpolation
        t_smooth = t * t * (3.0 - 2.0 * t)

        self._pan_x = self._scroll_start_x + (self._target_pan_x - self._scroll_start_x) * t_smooth
        self._pan_y = self._scroll_start_y + (self._target_pan_y - self._scroll_start_y) * t_smooth

        if t >= 1.0:
            self._pan_x = self._target_pan_x
            self._pan_y = self._target_pan_y
            self._is_smooth_scrolling = False
            return False

        return True

    # ── Coordinate Conversion ───────────────────────────────────────────────

    def tile_to_screen(self, tx: int, ty: int) -> tuple[float, float]:
        """Convert tile coordinates to screen pixel coordinates."""
        ts = self.effective_tile_size
        return (tx * ts + self._pan_x, ty * ts + self._pan_y)

    def screen_to_tile(self, sx: float, sy: float) -> tuple[int, int]:
        """Convert screen pixel coordinates to tile coordinates."""
        ts = self.effective_tile_size
        return (int((sx - self._pan_x) / ts), int((sy - self._pan_y) / ts))

    def get_visible_tile_range(self) -> tuple[int, int, int, int]:
        """Get the range of visible tiles (min_x, min_y, max_x, max_y)."""
        ts = self.effective_tile_size
        min_x = int(-self._pan_x / ts) - 1
        min_y = int(-self._pan_y / ts) - 1
        max_x = min_x + int(self._viewport_width / ts) + 2
        max_y = min_y + int(self._viewport_height / ts) + 2
        return (min_x, min_y, max_x, max_y)

    def get_visible_rect(self) -> QRectF:
        """Get the visible world rectangle in tile coordinates."""
        ts = self.effective_tile_size
        left = -self._pan_x / ts
        top = -self._pan_y / ts
        right = left + self._viewport_width / ts
        bottom = top + self._viewport_height / ts
        return QRectF(left, top, right - left, bottom - top)

    # ── State ───────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset camera to default state."""
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._zoom = 1.0
        self._is_smooth_scrolling = False

    def get_state(self) -> dict:
        """Get camera state for serialization."""
        return {
            "pan_x": self._pan_x,
            "pan_y": self._pan_y,
            "zoom": self._zoom,
        }

    def set_state(self, state: dict) -> None:
        """Restore camera state from serialized data."""
        self._pan_x = state.get("pan_x", 0.0)
        self._pan_y = state.get("pan_y", 0.0)
        self._zoom = max(0.125, min(8.0, state.get("zoom", 1.0)))
