"""
PMX-04R1 — Bidirectional coordinate translation between world and screen coordinates.
Supports zoom, pan, and all editor tools.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF

TILE_SIZE = 32


class CoordinateTranslator:
    """Translates between world (tile) coordinates and screen (pixel) coordinates."""

    def __init__(self) -> None:
        self._pan_x: float = 0.0
        self._pan_y: float = 0.0
        self._zoom: float = 1.0

    def set_camera(self, pan_x: float, pan_y: float, zoom: float) -> None:
        self._pan_x = pan_x
        self._pan_y = pan_y
        self._zoom = max(0.125, min(8.0, zoom))

    @property
    def zoom(self) -> float:
        return self._zoom

    @zoom.setter
    def zoom(self, value: float) -> None:
        self._zoom = max(0.125, min(8.0, value))

    @property
    def pan_x(self) -> float:
        return self._pan_x

    @property
    def pan_y(self) -> float:
        return self._pan_y

    @property
    def effective_tile_size(self) -> int:
        return max(4, int(TILE_SIZE * self._zoom))

    # ── World → Screen ──────────────────────────────────────────────────────

    def tile_to_screen(self, tx: int, ty: int) -> tuple[float, float]:
        """Convert tile coordinates to screen pixel coordinates (top-left of tile)."""
        ts = self.effective_tile_size
        sx = tx * ts + self._pan_x
        sy = ty * ts + self._pan_y
        return (sx, sy)

    def tile_to_screen_rect(self, tx: int, ty: int) -> QRectF:
        """Get the screen rectangle for a tile."""
        ts = self.effective_tile_size
        sx, sy = self.tile_to_screen(tx, ty)
        return QRectF(sx, sy, ts, ts)

    def tile_center_to_screen(self, tx: int, ty: int) -> tuple[float, float]:
        """Convert tile center to screen coordinates."""
        ts = self.effective_tile_size
        sx, sy = self.tile_to_screen(tx, ty)
        return (sx + ts / 2.0, sy + ts / 2.0)

    # ── Screen → World ──────────────────────────────────────────────────────

    def screen_to_tile(self, sx: float, sy: float) -> tuple[int, int]:
        """Convert screen pixel coordinates to tile coordinates (floor)."""
        ts = self.effective_tile_size
        tx = int((sx - self._pan_x) / ts)
        ty = int((sy - self._pan_y) / ts)
        return (tx, ty)

    def screen_to_tile_precise(self, sx: float, sy: float) -> tuple[float, float]:
        """Convert screen pixel coordinates to precise fractional tile coordinates."""
        ts = self.effective_tile_size
        tx = (sx - self._pan_x) / ts
        ty = (sy - self._pan_y) / ts
        return (tx, ty)

    def screen_to_tile_rect(self, sx: float, sy: float, sw: float, sh: float) -> tuple[int, int, int, int]:
        """Get the visible tile range from a screen rectangle.
        Returns (min_tx, min_ty, max_tx, max_ty).
        """
        min_tx, min_ty = self.screen_to_tile(sx, sy)
        max_tx, max_ty = self.screen_to_tile(sx + sw, sy + sh)
        return (min_tx - 1, min_ty - 1, max_tx + 1, max_ty + 1)

    # ── Zoom helpers ────────────────────────────────────────────────────────

    def zoom_centered_on_screen(self, factor: float, screen_x: float, screen_y: float) -> None:
        """Apply zoom centered on a specific screen point (e.g., cursor position)."""
        old_ts = self.effective_tile_size
        self._zoom = max(0.125, min(8.0, self._zoom * factor))
        new_ts = self.effective_tile_size

        # Adjust pan so the point under the cursor stays fixed
        world_x = (screen_x - self._pan_x) / old_ts
        world_y = (screen_y - self._pan_y) / old_ts
        self._pan_x = screen_x - world_x * new_ts
        self._pan_y = screen_y - world_y * new_ts

    def screen_delta_to_tile_delta(self, dx: float, dy: float) -> tuple[float, float]:
        """Convert a screen pixel delta to a tile delta (for panning)."""
        ts = self.effective_tile_size
        return (dx / ts, dy / ts)
