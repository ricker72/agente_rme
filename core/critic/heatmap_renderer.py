"""
HeatmapRenderer — produces per-category heatmaps (PNGs) for the visual critic.

Uses only the Python standard library (PNG written manually) so it has no
external dependencies.
"""

from __future__ import annotations

import logging
import os
import struct
import zlib
from typing import Dict, Tuple

from core.world.world_model import WorldModel

from .analyzers import build_snapshots

logger = logging.getLogger(__name__)


def _png(width: int, height: int, rgb_bytes: bytes) -> bytes:
    """Write a minimal RGB PNG (no external dependencies)."""

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = b"".join(
        b"\x00" + rgb_bytes[y * width * 3 : (y + 1) * width * 3] for y in range(height)
    )
    idat = zlib.compress(raw, 9)
    return header + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def _color_for_value(v: float, vmin: float, vmax: float) -> Tuple[int, int, int]:
    """Map v in [vmin, vmax] to a heat color (blue -> green -> yellow -> red)."""
    if vmax <= vmin:
        return (128, 128, 128)
    t = max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))
    if t < 0.5:
        # blue -> green
        u = t / 0.5
        r = int(0 * (1 - u) + 0 * u)
        g = int(0 * (1 - u) + 200 * u)
        b = int(200 * (1 - u) + 0 * u)
    else:
        # green -> yellow -> red
        u = (t - 0.5) / 0.5
        r = int(0 * (1 - u) + 220 * u)
        g = int(200 * (1 - u) + 30 * u)
        b = int(0 * (1 - u) + 0 * u)
    return (r, g, b)


class HeatmapRenderer:
    """
    Renders category-based heatmaps of the world.
    """

    CATEGORIES = ("visual", "navigation", "density", "spawn")

    def __init__(self, cell_size: int = 4, padding: int = 2, max_dimension: int = 1024):
        self.cell_size = max(1, cell_size)
        self.padding = max(0, padding)
        self.max_dimension = max(64, max_dimension)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_score_map(
        self,
        world: WorldModel,
        score_per_tile: Dict[Tuple[int, int], float],
        output_path: str,
        background: Tuple[int, int, int] = (32, 32, 32),
    ) -> str:
        """
        Render a 2D heatmap of per-tile scores.

        score_per_tile: dict of (x, y) -> value (clamped to [0, 100]).
        """
        snapshots = build_snapshots(world)
        if not snapshots:
            # Write a tiny placeholder
            return self._write_placeholder(output_path, "empty world")

        xs = [s.x for s in snapshots]
        ys = [s.y for s in snapshots]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = (max_x - min_x + 1) * self.cell_size + 2 * self.padding
        height = (max_y - min_y + 1) * self.cell_size + 2 * self.padding

        # Downscale to max_dimension
        scale = 1.0
        if max(width, height) > self.max_dimension:
            scale = self.max_dimension / float(max(width, height))
        cell = max(1, int(self.cell_size * scale))
        pad = max(0, int(self.padding * scale))
        map_w = (max_x - min_x + 1) * cell
        map_h = (max_y - min_y + 1) * cell

        canvas_w = map_w + 2 * pad
        canvas_h = map_h + 2 * pad

        rgb = bytearray(
            [background[0], background[1], background[2]] * canvas_w * canvas_h
        )

        values = list(score_per_tile.values())
        vmin = min(values) if values else 0.0
        vmax = max(values) if values else 1.0
        if vmax - vmin < 1e-9:
            vmax = vmin + 1.0

        for (x, y), val in score_per_tile.items():
            r, g, b = _color_for_value(val, vmin, vmax)
            for dy in range(cell):
                for dx in range(cell):
                    px = (x - min_x) * cell + dx + pad
                    py = (y - min_y) * cell + dy + pad
                    if 0 <= px < canvas_w and 0 <= py < canvas_h:
                        idx = (py * canvas_w + px) * 3
                        rgb[idx] = r
                        rgb[idx + 1] = g
                        rgb[idx + 2] = b

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(_png(canvas_w, canvas_h, bytes(rgb)))
        return output_path

    def render_density_heatmap(self, world: WorldModel, output_path: str) -> str:
        """Item-count per tile."""
        snapshots = build_snapshots(world)
        scores: Dict[Tuple[int, int], float] = {}
        for s in snapshots:
            scores[(s.x, s.y)] = float(s.item_count)
        return self.render_score_map(world, scores, output_path)

    def render_spawn_heatmap(self, world: WorldModel, output_path: str) -> str:
        """Spawn count per tile (0/1/2+)."""
        snapshots = build_snapshots(world)
        scores: Dict[Tuple[int, int], float] = {}
        for s in snapshots:
            scores[(s.x, s.y)] = 100.0 if s.has_spawn else 0.0
        return self.render_score_map(world, scores, output_path)

    def render_navigation_heatmap(self, world: WorldModel, output_path: str) -> str:
        """Tiles colored by reachability from the first walkable tile."""
        from .analyzers import WalkableGraph, bfs

        graph = WalkableGraph(world).build()
        if not graph.positions:
            return self._write_placeholder(output_path, "empty")
        start = graph.find_entry_point()
        assert start is not None
        visited = bfs(start, start, graph.neighbors_fn, max_nodes=20000)
        scores: Dict[Tuple[int, int], float] = {}
        for pos in graph.positions:
            scores[(pos[0], pos[1])] = 100.0 if pos in visited else 0.0
        return self.render_score_map(world, scores, output_path)

    def render_visual_heatmap(self, world: WorldModel, output_path: str) -> str:
        """Per-tile content richness score."""
        snapshots = build_snapshots(world)
        scores: Dict[Tuple[int, int], float] = {}
        for s in snapshots:
            base = 30.0 if s.ground is not None else 0.0
            base += min(70.0, s.item_count * 15.0)
            if s.has_spawn:
                base += 30.0
            scores[(s.x, s.y)] = min(100.0, base)
        return self.render_score_map(world, scores, output_path)

    def render_all(
        self, world: WorldModel, output_dir: str, prefix: str = ""
    ) -> Dict[str, str]:
        os.makedirs(output_dir, exist_ok=True)
        p = (prefix + "_") if prefix else ""
        return {
            "visual": self.render_visual_heatmap(
                world, os.path.join(output_dir, f"{p}visual_score.png")
            ),
            "navigation": self.render_navigation_heatmap(
                world, os.path.join(output_dir, f"{p}navigation_heatmap.png")
            ),
            "density": self.render_density_heatmap(
                world, os.path.join(output_dir, f"{p}density_heatmap.png")
            ),
            "spawn": self.render_spawn_heatmap(
                world, os.path.join(output_dir, f"{p}spawn_heatmap.png")
            ),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_placeholder(self, path: str, text: str) -> str:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "wb") as f:
            f.write(_png(64, 64, bytes([80, 80, 80] * 64 * 64)))
        return path
