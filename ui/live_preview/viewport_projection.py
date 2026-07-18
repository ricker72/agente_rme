from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPoint, QRect


@dataclass(frozen=True)
class RMEViewportProjection:
    """Map tile coordinates to the RME-like editor screen plane."""

    mode: str = "rme_orthogonal"

    def tile_to_screen(self, x: int, y: int, tile_size: int, pan: QPoint) -> QPoint:
        if self.mode == "parallel_oblique_45":
            return QPoint(
                int((x - y) * tile_size * 0.5) + pan.x(),
                int((x + y) * tile_size * 0.25) + pan.y(),
            )
        return QPoint(int(x) * tile_size + pan.x(), int(y) * tile_size + pan.y())

    def screen_to_tile(self, point: QPoint, tile_size: int, pan: QPoint) -> tuple[int, int]:
        local_x = point.x() - pan.x()
        local_y = point.y() - pan.y()
        if self.mode == "parallel_oblique_45":
            map_x = local_x / (tile_size * 0.5)
            map_y = local_y / (tile_size * 0.25)
            x = int((map_x + map_y) / 2)
            y = int((map_y - map_x) / 2)
            return x, y
        return int(local_x / tile_size), int(local_y / tile_size)

    def tile_rect(self, x: int, y: int, tile_size: int, pan: QPoint) -> QRect:
        origin = self.tile_to_screen(x, y, tile_size, pan)
        return QRect(origin.x(), origin.y(), tile_size, tile_size)

    def sprite_rect(self, x: int, y: int, tile_size: int, pan: QPoint, width_tiles: int = 1, height_tiles: int = 1) -> QRect:
        rect = self.tile_rect(x, y, tile_size, pan)
        width = max(1, int(width_tiles)) * tile_size
        height = max(1, int(height_tiles)) * tile_size
        return QRect(rect.right() - width + 1, rect.bottom() - height + 1, width, height)
