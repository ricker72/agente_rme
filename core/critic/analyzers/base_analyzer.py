"""
BaseAnalyzer — common helpers and types for all critic analyzers.
"""

from __future__ import annotations

import math
from collections import Counter, deque
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from core.world.world_model import WorldModel
from core.world.tile import Tile


@dataclass
class TileSnapshot:
    """Lightweight snapshot of a tile to avoid coupling analyzers to Tile internals."""

    x: int
    y: int
    z: int
    ground: Optional[int]
    item_count: int
    item_ids: Tuple[int, ...]
    has_spawn: bool
    zone: Optional[str]

    @classmethod
    def from_tile(cls, tile: Tile) -> "TileSnapshot":
        items = tile.items or []
        item_ids: List[int] = []
        for it in items:
            if hasattr(it, "itemid"):
                item_ids.append(int(it.itemid))
            elif isinstance(it, dict) and "itemid" in it:
                item_ids.append(int(it["itemid"]))
        return cls(
            x=tile.x,
            y=tile.y,
            z=tile.z,
            ground=tile.ground,
            item_count=len(items),
            item_ids=tuple(item_ids),
            has_spawn=tile.spawn is not None,
            zone=tile.zone,
        )


@dataclass
class Region:
    """A contiguous group of tiles with a common z level."""

    z: int
    tiles: Set[Tuple[int, int]]

    @property
    def size(self) -> int:
        return len(self.tiles)

    @property
    def bounds(self) -> Optional[Tuple[int, int, int, int]]:
        if not self.tiles:
            return None
        xs = [t[0] for t in self.tiles]
        ys = [t[1] for t in self.tiles]
        return (min(xs), min(ys), max(xs), max(ys))

    @property
    def centroid(self) -> Tuple[float, float]:
        if not self.tiles:
            return (0.0, 0.0)
        cx = sum(t[0] for t in self.tiles) / self.size
        cy = sum(t[1] for t in self.tiles) / self.size
        return (cx, cy)


def build_snapshots(world: WorldModel) -> List[TileSnapshot]:
    """Build a flat list of tile snapshots from a world model."""
    return [TileSnapshot.from_tile(t) for t in world.tiles.values()]


def snapshots_by_zone(snapshots: List[TileSnapshot]) -> Dict[str, List[TileSnapshot]]:
    """Group snapshots by their zone name (or "unzoned")."""
    out: Dict[str, List[TileSnapshot]] = {}
    for s in snapshots:
        key = s.zone or "unzoned"
        out.setdefault(key, []).append(s)
    return out


def snapshots_by_z(snapshots: List[TileSnapshot]) -> Dict[int, List[TileSnapshot]]:
    """Group snapshots by z level."""
    out: Dict[int, List[TileSnapshot]] = {}
    for s in snapshots:
        out.setdefault(s.z, []).append(s)
    return out


def find_regions(
    snapshots: List[TileSnapshot], z: int, connectivity: int = 4
) -> List[Region]:
    """
    Find connected components among ground-bearing tiles on a given z.

    connectivity:
        4 = up/down/left/right
        8 = 4 + diagonals
    """
    z_tiles = [s for s in snapshots if s.z == z and s.ground is not None]
    positions: Set[Tuple[int, int]] = {(s.x, s.y) for s in z_tiles}
    visited: Set[Tuple[int, int]] = set()
    regions: List[Region] = []

    if connectivity == 8:
        deltas = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    else:
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for start in positions:
        if start in visited:
            continue
        queue = deque([start])
        visited.add(start)
        comp: Set[Tuple[int, int]] = set()
        while queue:
            cx, cy = queue.popleft()
            comp.add((cx, cy))
            for dx, dy in deltas:
                n = (cx + dx, cy + dy)
                if n in positions and n not in visited:
                    visited.add(n)
                    queue.append(n)
        regions.append(Region(z=z, tiles=comp))
    return regions


def manhattan(p1: Tuple[int, int], p2: Tuple[int, int]) -> int:
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def euclidean(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def safe_ratio(num: float, denom: float, default: float = 0.0) -> float:
    if denom <= 0:
        return default
    return num / denom


def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def average(values: Iterable[float]) -> float:
    vals = list(values)
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def percentile(values: List[float], pct: float) -> float:
    """Return the p-th percentile of a list of values."""
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (pct / 100.0)
    f = int(math.floor(k))
    c = int(math.ceil(k))
    if f == c:
        return s[f]
    return s[f] * (c - k) + s[c] * (k - f)


def stddev(values: Iterable[float]) -> float:
    """Sample standard deviation."""
    vals = list(values)
    if len(vals) < 2:
        return 0.0
    m = sum(vals) / len(vals)
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    return math.sqrt(var)


def histogram(values: Iterable[Any]) -> Counter:
    return Counter(values)
