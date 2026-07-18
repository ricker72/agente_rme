"""
PMX-04R1 — Dirty region manager for incremental viewport updates.
Only repaints modified tiles instead of the entire viewport.
"""

from __future__ import annotations

from PySide6.QtCore import QRect


class DirtyRegionManager:
    """Tracks which tiles have been modified and need repainting.

    Supports:
    - tile changes (add/remove/modify)
    - brush operations
    - selection changes
    - overlays
    """

    def __init__(self) -> None:
        # Set of (x, y, z) tiles that are dirty
        self._dirty_tiles: set[tuple[int, int, int]] = set()

        # Full repaint flag (when set, ignore individual tiles)
        self._full_repaint: bool = True

        # Screen-space dirty rects (for overlay changes)
        self._dirty_rects: list[QRect] = []

    # ── Tile Dirtiness ──────────────────────────────────────────────────────

    def mark_tile_dirty(self, x: int, y: int, z: int) -> None:
        """Mark a single tile as dirty."""
        if not self._full_repaint:
            self._dirty_tiles.add((x, y, z))

    def mark_tiles_dirty(self, tiles: set[tuple[int, int, int]]) -> None:
        """Mark multiple tiles as dirty."""
        if not self._full_repaint:
            self._dirty_tiles.update(tiles)

    def mark_region_dirty(self, x1: int, y1: int, x2: int, y2: int, z: int) -> None:
        """Mark a rectangular region of tiles as dirty."""
        if not self._full_repaint:
            for tx in range(x1, x2 + 1):
                for ty in range(y1, y2 + 1):
                    self._dirty_tiles.add((tx, ty, z))

    def mark_brush_dirty(self, center_x: int, center_y: int, z: int, radius: int) -> None:
        """Mark tiles affected by a brush operation as dirty."""
        if not self._full_repaint:
            for dx in range(-radius + 1, radius):
                for dy in range(-radius + 1, radius):
                    self._dirty_tiles.add((center_x + dx, center_y + dy, z))

    # ── Screen Rect Dirtiness ───────────────────────────────────────────────

    def mark_screen_rect_dirty(self, rect: QRect) -> None:
        """Mark a screen-space rectangle as dirty (for overlay changes)."""
        self._dirty_rects.append(rect)

    def mark_selection_dirty(self, selection: set[tuple[int, int, int]]) -> None:
        """Mark selection tiles as dirty."""
        self.mark_tiles_dirty(selection)

    # ── Full Repaint ────────────────────────────────────────────────────────

    def request_full_repaint(self) -> None:
        """Request a full viewport repaint."""
        self._full_repaint = True
        self._dirty_tiles.clear()
        self._dirty_rects.clear()

    @property
    def needs_full_repaint(self) -> bool:
        return self._full_repaint

    # ── Query ───────────────────────────────────────────────────────────────

    def is_tile_dirty(self, x: int, y: int, z: int) -> bool:
        """Check if a specific tile is dirty."""
        if self._full_repaint:
            return True
        return (x, y, z) in self._dirty_tiles

    def get_dirty_tiles(self) -> set[tuple[int, int, int]]:
        """Get all currently dirty tiles."""
        if self._full_repaint:
            return set()  # All tiles are dirty, return empty to signal full repaint
        return self._dirty_tiles.copy()

    def get_dirty_rects(self) -> list[QRect]:
        """Get all currently dirty screen rects."""
        return list(self._dirty_rects)

    def has_dirty_rects(self) -> bool:
        """Check if there are any dirty screen rects."""
        return len(self._dirty_rects) > 0

    # ── Clear ───────────────────────────────────────────────────────────────

    def clear(self) -> None:
        """Clear all dirty state after repaint."""
        self._dirty_tiles.clear()
        self._dirty_rects.clear()
        self._full_repaint = False

    def clear_tiles(self) -> None:
        """Clear only tile dirtiness (keep screen rects)."""
        self._dirty_tiles.clear()

    # ── Floor Change ────────────────────────────────────────────────────────

    def on_floor_changed(self) -> None:
        """Call when the active floor changes to force full repaint."""
        self.request_full_repaint()

    def on_zoom_changed(self) -> None:
        """Call when zoom changes to force full repaint."""
        self.request_full_repaint()

    # ── State ───────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """Reset the dirty region manager to initial state."""
        self._dirty_tiles.clear()
        self._dirty_rects.clear()
        self._full_repaint = True