"""
PMX-04R1 — Chunk renderer that splits rendering into 32x32 tile chunks.
Only renders visible chunks for optimal performance.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter

from .camera import Camera
from .tile_renderer import TileRenderer


# Chunk size in tiles
CHUNK_SIZE = 32


class ChunkRenderer:
    """Renders the map in chunks for efficient visible-area rendering.

    Only processes chunks that intersect the visible viewport.
    Each chunk is 32x32 tiles.
    """

    def __init__(self, tile_renderer: TileRenderer | None = None) -> None:
        self.tile_renderer = tile_renderer or TileRenderer()

    def render_visible(
        self,
        painter: QPainter,
        camera: Camera,
        tiles: dict[tuple[int, int, int], dict],
        floor: int,
    ) -> int:
        """Render all visible tiles on the given floor.
        Returns the number of tiles rendered.
        """
        min_x, min_y, max_x, max_y = camera.get_visible_tile_range()
        rendered_count = 0

        # Iterate over visible chunks
        chunk_min_x = min_x // CHUNK_SIZE
        chunk_min_y = min_y // CHUNK_SIZE
        chunk_max_x = max_x // CHUNK_SIZE
        chunk_max_y = max_y // CHUNK_SIZE

        for chunk_x in range(chunk_min_x, chunk_max_x + 1):
            for chunk_y in range(chunk_min_y, chunk_max_y + 1):
                rendered_count += self._render_chunk(
                    painter, camera, tiles, floor,
                    chunk_x, chunk_y,
                    min_x, min_y, max_x, max_y,
                )

        return rendered_count

    def render_chunk_at(
        self,
        painter: QPainter,
        camera: Camera,
        tiles: dict[tuple[int, int, int], dict],
        floor: int,
        chunk_x: int,
        chunk_y: int,
    ) -> int:
        """Render a specific chunk. Returns the number of tiles rendered."""
        min_x = chunk_x * CHUNK_SIZE
        min_y = chunk_y * CHUNK_SIZE
        max_x = min_x + CHUNK_SIZE - 1
        max_y = min_y + CHUNK_SIZE - 1

        return self._render_chunk_impl(
            painter, camera, tiles, floor,
            min_x, min_y, max_x, max_y,
        )

    def get_chunk_for_tile(self, tx: int, ty: int) -> tuple[int, int]:
        """Get the chunk coordinates for a tile."""
        return (tx // CHUNK_SIZE, ty // CHUNK_SIZE)

    def get_chunk_bounds(self, chunk_x: int, chunk_y: int) -> tuple[int, int, int, int]:
        """Get the tile bounds of a chunk (min_x, min_y, max_x, max_y)."""
        return (
            chunk_x * CHUNK_SIZE,
            chunk_y * CHUNK_SIZE,
            chunk_x * CHUNK_SIZE + CHUNK_SIZE - 1,
            chunk_y * CHUNK_SIZE + CHUNK_SIZE - 1,
        )

    def get_visible_chunks(self, camera: Camera) -> list[tuple[int, int]]:
        """Get the list of visible chunk coordinates."""
        min_x, min_y, max_x, max_y = camera.get_visible_tile_range()
        chunks: list[tuple[int, int]] = []
        for cx in range(min_x // CHUNK_SIZE, max_x // CHUNK_SIZE + 1):
            for cy in range(min_y // CHUNK_SIZE, max_y // CHUNK_SIZE + 1):
                chunks.append((cx, cy))
        return chunks

    # ── Internal ────────────────────────────────────────────────────────────

    def _render_chunk(
        self,
        painter: QPainter,
        camera: Camera,
        tiles: dict[tuple[int, int, int], dict],
        floor: int,
        chunk_x: int,
        chunk_y: int,
        view_min_x: int,
        view_min_y: int,
        view_max_x: int,
        view_max_y: int,
    ) -> int:
        """Render a single chunk, clipped to the visible viewport."""
        chunk_min_x = chunk_x * CHUNK_SIZE
        chunk_min_y = chunk_y * CHUNK_SIZE
        chunk_max_x = chunk_min_x + CHUNK_SIZE - 1
        chunk_max_y = chunk_min_y + CHUNK_SIZE - 1

        # Clip chunk to visible area
        render_min_x = max(chunk_min_x, view_min_x)
        render_min_y = max(chunk_min_y, view_min_y)
        render_max_x = min(chunk_max_x, view_max_x)
        render_max_y = min(chunk_max_y, view_max_y)

        return self._render_chunk_impl(
            painter, camera, tiles, floor,
            render_min_x, render_min_y, render_max_x, render_max_y,
        )

    def _render_chunk_impl(
        self,
        painter: QPainter,
        camera: Camera,
        tiles: dict[tuple[int, int, int], dict],
        floor: int,
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
    ) -> int:
        """Render a rectangular region of tiles."""
        rendered_count = 0
        ts = camera.effective_tile_size

        for tx in range(min_x, max_x + 1):
            for ty in range(min_y, max_y + 1):
                key = (tx, ty, floor)
                tile_data = tiles.get(key)

                sx, sy = camera.tile_to_screen(tx, ty)
                rect = QRectF(sx, sy, ts, ts)

                if tile_data is not None:
                    # Render tile with its items
                    self.tile_renderer.render_tile(painter, rect)
                else:
                    # Render empty tile
                    self.tile_renderer.draw_empty_tile(painter, rect)

                rendered_count += 1

        return rendered_count