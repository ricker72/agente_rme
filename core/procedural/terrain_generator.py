"""
HITO 16 - Procedural World Generation: Terrain Generator
=========================================================

Generates high-level terrain features (mountains, hills, water, lava) on
top of the biome base layer. Uses a simple deterministic 2D value-noise
function (no external dependencies) so the same seed always produces the
same continent.

The terrain generator is a "decorator" — it never removes a tile that
was placed by a higher-priority layer (city tiles, structure tiles, etc).
Tiles that are already set are kept; only empty tiles get new ground.

Architecture:
    TerrainFeature (dataclass)        -> a region of interest
    TerrainGenerator                  -> the engine
        .generate_mountains(world, ...)
        .generate_hills(world, ...)
        .generate_water(world, ...)
        .generate_lava(world, ...)
        .generate_forest_decorations(world, ...)
        .generate_all(world, bounds, z, theme, ...)

Public API:
    TerrainGenerator
    TerrainFeature
    generate_terrain(world, ...)            -> Dict[str, TerrainFeature]
    generate_mountains(world, ...)          -> TerrainFeature
    generate_hills(world, ...)              -> TerrainFeature
    generate_water_bodies(world, ...)       -> List[TerrainFeature]
    generate_lava_fields(world, ...)        -> List[TerrainFeature]
    value_noise_2d(x, y, seed)              -> float   (0..1)
    fbm_noise_2d(x, y, seed, octaves, ...)  -> float   (0..1)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# TerrainFeature: a region of the world with a specific shape
# =============================================================================


@dataclass
class TerrainFeature:
    """A region of the world shaped by a single terrain pass."""

    name: str
    kind: str  # "mountain" | "hill" | "water" | "lava" | "forest"
    bounds: Tuple[int, int, int, int]  # (x1, y1, x2, y2) inclusive
    ground_id: int
    z: int = 7
    tiles_written: int = 0
    seed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def center(self) -> Tuple[int, int]:
        return (
            (self.bounds[0] + self.bounds[2]) // 2,
            (self.bounds[1] + self.bounds[3]) // 2,
        )

    @property
    def size(self) -> Tuple[int, int]:
        return (
            self.bounds[2] - self.bounds[0] + 1,
            self.bounds[3] - self.bounds[1] + 1,
        )

    def contains(self, x: int, y: int) -> bool:
        return (
            self.bounds[0] <= x <= self.bounds[2]
            and self.bounds[1] <= y <= self.bounds[3]
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "bounds": list(self.bounds),
            "ground_id": self.ground_id,
            "z": self.z,
            "tiles_written": self.tiles_written,
            "seed": self.seed,
            "center": list(self.center),
            "size": list(self.size),
            "metadata": dict(self.metadata),
        }


# =============================================================================
# Item-ID tables (theme-aware)
# =============================================================================

TERRAIN_GROUND_IDS: Dict[str, Dict[str, int]] = {
    # primary ground id for each terrain kind, per theme
    "generic": {
        "mountain": 361,
        "hill": 103,
        "water": 4597,
        "lava": 598,
        "forest_floor": 397,
        "rock": 102,
    },
    "issavi": {
        "mountain": 103,
        "hill": 421,
        "water": 4597,
        "lava": 598,
        "forest_floor": 415,
        "rock": 102,
    },
    "roshamuul": {
        "mountain": 231,
        "hill": 358,
        "water": 4597,
        "lava": 599,
        "forest_floor": 1056,
        "rock": 358,
    },
    "soul_war": {
        "mountain": 231,
        "hill": 358,
        "water": 4597,
        "lava": 600,
        "forest_floor": 514,
        "rock": 231,
    },
    "library": {
        "mountain": 103,
        "hill": 102,
        "water": 4597,
        "lava": 598,
        "forest_floor": 396,
        "rock": 103,
    },
    "yalahar": {
        "mountain": 103,
        "hill": 454,
        "water": 4597,
        "lava": 598,
        "forest_floor": 450,
        "rock": 103,
    },
    "falcon": {
        "mountain": 103,
        "hill": 430,
        "water": 4597,
        "lava": 598,
        "forest_floor": 428,
        "rock": 102,
    },
    "cobra": {
        "mountain": 103,
        "hill": 516,
        "water": 4597,
        "lava": 598,
        "forest_floor": 514,
        "rock": 103,
    },
    "ice": {
        "mountain": 672,
        "hill": 671,
        "water": 4597,
        "lava": 598,
        "forest_floor": 670,
        "rock": 672,
    },
    "jungle": {
        "mountain": 103,
        "hill": 444,
        "water": 4597,
        "lava": 598,
        "forest_floor": 440,
        "rock": 103,
    },
    "thais": {
        "mountain": 103,
        "hill": 351,
        "water": 4597,
        "lava": 598,
        "forest_floor": 351,
        "rock": 102,
    },
    "venore": {
        "mountain": 103,
        "hill": 360,
        "water": 4598,
        "lava": 598,
        "forest_floor": 360,
        "rock": 102,
    },
    "ankrahmun": {
        "mountain": 103,
        "hill": 482,
        "water": 4597,
        "lava": 598,
        "forest_floor": 481,
        "rock": 103,
    },
}


def get_terrain_ground_id(theme: Any, kind: str, fallback: int = 0) -> int:
    """Return a sensible ground ID for a terrain kind, given a theme."""
    name = "generic"
    if isinstance(theme, str):
        name = theme.lower()
    elif theme is not None:
        name = str(getattr(theme, "name", "generic")).lower()
    palette = TERRAIN_GROUND_IDS.get(name, TERRAIN_GROUND_IDS["generic"])
    if fallback:
        return palette.get(kind, fallback)
    return palette.get(kind, 361)


# =============================================================================
# Deterministic value-noise (no external dependencies)
# =============================================================================


def _hash2d(ix: int, iy: int, seed: int) -> float:
    """Cheap deterministic 2D hash -> [0, 1)."""
    h = (ix * 374761393) ^ (iy * 668265263) ^ (seed * 2147483647)
    h = (h ^ (h >> 13)) * 1274126177
    h = h & 0xFFFFFFFF
    return (h % 100000) / 100000.0


def _smoothstep(t: float) -> float:
    return t * t * (3.0 - 2.0 * t)


def value_noise_2d(x: float, y: float, seed: int = 0) -> float:
    """Sample deterministic 2D value-noise in [0, 1]."""
    ix = int(math.floor(x))
    iy = int(math.floor(y))
    fx = x - ix
    fy = y - iy

    v00 = _hash2d(ix, iy, seed)
    v10 = _hash2d(ix + 1, iy, seed)
    v01 = _hash2d(ix, iy + 1, seed)
    v11 = _hash2d(ix + 1, iy + 1, seed)

    u = _smoothstep(fx)
    v = _smoothstep(fy)

    return v00 * (1 - u) * (1 - v) + v10 * u * (1 - v) + v01 * (1 - u) * v + v11 * u * v


def fbm_noise_2d(
    x: float,
    y: float,
    seed: int = 0,
    octaves: int = 4,
    lacunarity: float = 2.0,
    gain: float = 0.5,
) -> float:
    """Fractional Brownian Motion built on value-noise_2d. Returns [0, 1]."""
    amp = 1.0
    freq = 1.0
    total = 0.0
    norm = 0.0
    for _ in range(max(1, octaves)):
        total += value_noise_2d(x * freq, y * freq, seed + int(freq * 31)) * amp
        norm += amp
        amp *= gain
        freq *= lacunarity
    if norm == 0:
        return 0.0
    return total / norm


# =============================================================================
# TerrainGenerator
# =============================================================================


class TerrainGenerator:
    """
    Generates terrain features inside a bounding rectangle.

    The generator uses fbm-noise to decide which tiles become mountains,
    hills, water, etc. and respects an "exclude" mask so it never
    overwrites tiles that already have a ground.

    Usage:
        gen = TerrainGenerator(seed=42)
        features = gen.generate_all(
            world, x1=0, y1=0, x2=199, y2=199, z=7, theme="issavi",
        )
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self._seed = int(seed) if seed is not None else self._rng.randint(0, 999999)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_mountains(
        self,
        world: Any,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        z: int,
        theme: Any,
        threshold: float = 0.78,
        noise_scale: float = 0.06,
        ground_id: Optional[int] = None,
        max_tiles: Optional[int] = None,
    ) -> TerrainFeature:
        """
        Mark high-noise tiles as mountain ground.

        Args:
            world: WorldModel to write into.
            x1, y1, x2, y2: Inclusive bounds.
            z: Z-layer.
            theme: Theme name or ThemeAssets.
            threshold: Noise threshold above which a tile becomes mountain.
            noise_scale: Spatial frequency of the noise (lower = larger mountains).
            ground_id: Override the mountain ground ID.
            max_tiles: Optional cap on how many tiles we will write.

        Returns:
            The TerrainFeature describing the result.
        """
        gid = (
            ground_id
            if ground_id is not None
            else get_terrain_ground_id(theme, "mountain")
        )
        feat = TerrainFeature(
            name="mountains",
            kind="mountain",
            bounds=(x1, y1, x2, y2),
            ground_id=gid,
            z=z,
            seed=self._seed,
        )
        from core.world.tile import Tile

        count = 0
        for iy in range(y1, y2 + 1):
            for ix in range(x1, x2 + 1):
                if max_tiles is not None and count >= max_tiles:
                    feat.tiles_written = count
                    return feat
                n = fbm_noise_2d(
                    ix * noise_scale, iy * noise_scale, self._seed, octaves=5
                )
                if n < threshold:
                    continue
                if world.has_tile(ix, iy, z):
                    continue
                world.set_tile(
                    Tile(x=ix, y=iy, z=z, ground=gid, zone="terrain:mountain")
                )
                count += 1
        feat.tiles_written = count
        return feat

    def generate_hills(
        self,
        world: Any,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        z: int,
        theme: Any,
        threshold: float = 0.62,
        max_threshold: float = 0.78,
        noise_scale: float = 0.08,
        ground_id: Optional[int] = None,
        max_tiles: Optional[int] = None,
    ) -> TerrainFeature:
        """Mark medium-noise tiles as hills (between threshold and max_threshold)."""
        gid = (
            ground_id if ground_id is not None else get_terrain_ground_id(theme, "hill")
        )
        feat = TerrainFeature(
            name="hills",
            kind="hill",
            bounds=(x1, y1, x2, y2),
            ground_id=gid,
            z=z,
            seed=self._seed ^ 0x5A5A,
        )
        from core.world.tile import Tile

        count = 0
        for iy in range(y1, y2 + 1):
            for ix in range(x1, x2 + 1):
                if max_tiles is not None and count >= max_tiles:
                    feat.tiles_written = count
                    return feat
                n = fbm_noise_2d(
                    ix * noise_scale, iy * noise_scale, self._seed ^ 0x5A5A, octaves=4
                )
                if n < threshold or n > max_threshold:
                    continue
                if world.has_tile(ix, iy, z):
                    continue
                world.set_tile(Tile(x=ix, y=iy, z=z, ground=gid, zone="terrain:hill"))
                count += 1
        feat.tiles_written = count
        return feat

    def generate_water_bodies(
        self,
        world: Any,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        z: int,
        theme: Any,
        threshold: float = 0.35,
        noise_scale: float = 0.05,
        ground_id: Optional[int] = None,
        max_tiles: Optional[int] = None,
    ) -> List[TerrainFeature]:
        """
        Mark low-noise tiles as water. We treat contiguous water tiles as a
        single "body" and return one feature per body.
        """
        gid = (
            ground_id
            if ground_id is not None
            else get_terrain_ground_id(theme, "water")
        )
        from core.world.tile import Tile

        # Mark candidate cells
        is_water: Dict[Tuple[int, int], bool] = {}
        for iy in range(y1, y2 + 1):
            for ix in range(x1, x2 + 1):
                n = fbm_noise_2d(
                    ix * noise_scale, iy * noise_scale, self._seed ^ 0x33CC, octaves=3
                )
                is_water[(ix, iy)] = n < threshold

        # Connected-component labelling
        bodies: List[TerrainFeature] = []
        visited: Dict[Tuple[int, int], bool] = {}
        for iy in range(y1, y2 + 1):
            for ix in range(x1, x2 + 1):
                if not is_water[(ix, iy)] or visited.get((ix, iy)):
                    continue
                # BFS
                stack: List[Tuple[int, int]] = [(ix, iy)]
                cells: List[Tuple[int, int]] = []
                while stack:
                    cx, cy = stack.pop()
                    if visited.get((cx, cy)):
                        continue
                    if not is_water.get((cx, cy), False):
                        continue
                    visited[(cx, cy)] = True
                    cells.append((cx, cy))
                    stack.extend(
                        [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]
                    )
                if len(cells) < 4:
                    continue
                xs = [c[0] for c in cells]
                ys = [c[1] for c in cells]
                feat = TerrainFeature(
                    name=f"water_body_{len(bodies) + 1}",
                    kind="water",
                    bounds=(min(xs), min(ys), max(xs), max(ys)),
                    ground_id=gid,
                    z=z,
                    seed=self._seed ^ 0x33CC,
                )
                count = 0
                for cx, cy in cells:
                    if max_tiles is not None and count >= max_tiles:
                        break
                    if world.has_tile(cx, cy, z):
                        continue
                    world.set_tile(
                        Tile(x=cx, y=cy, z=z, ground=gid, zone="terrain:water")
                    )
                    count += 1
                feat.tiles_written = count
                bodies.append(feat)
        return bodies

    def generate_lava_fields(
        self,
        world: Any,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        z: int,
        theme: Any,
        threshold: float = 0.85,
        noise_scale: float = 0.12,
        ground_id: Optional[int] = None,
        max_tiles: Optional[int] = None,
    ) -> List[TerrainFeature]:
        """Mark very-high-noise tiles as lava. Returns one feature per cluster."""
        gid = (
            ground_id if ground_id is not None else get_terrain_ground_id(theme, "lava")
        )
        from core.world.tile import Tile

        is_lava: Dict[Tuple[int, int], bool] = {}
        for iy in range(y1, y2 + 1):
            for ix in range(x1, x2 + 1):
                n = fbm_noise_2d(
                    ix * noise_scale, iy * noise_scale, self._seed ^ 0xA55A, octaves=3
                )
                is_lava[(ix, iy)] = n > threshold

        bodies: List[TerrainFeature] = []
        visited: Dict[Tuple[int, int], bool] = {}
        for iy in range(y1, y2 + 1):
            for ix in range(x1, x2 + 1):
                if not is_lava[(ix, iy)] or visited.get((ix, iy)):
                    continue
                stack: List[Tuple[int, int]] = [(ix, iy)]
                cells: List[Tuple[int, int]] = []
                while stack:
                    cx, cy = stack.pop()
                    if visited.get((cx, cy)):
                        continue
                    if not is_lava.get((cx, cy), False):
                        continue
                    visited[(cx, cy)] = True
                    cells.append((cx, cy))
                    stack.extend(
                        [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]
                    )
                if len(cells) < 3:
                    continue
                xs = [c[0] for c in cells]
                ys = [c[1] for c in cells]
                feat = TerrainFeature(
                    name=f"lava_field_{len(bodies) + 1}",
                    kind="lava",
                    bounds=(min(xs), min(ys), max(xs), max(ys)),
                    ground_id=gid,
                    z=z,
                    seed=self._seed ^ 0xA55A,
                )
                count = 0
                for cx, cy in cells:
                    if max_tiles is not None and count >= max_tiles:
                        break
                    if world.has_tile(cx, cy, z):
                        continue
                    world.set_tile(
                        Tile(x=cx, y=cy, z=z, ground=gid, zone="terrain:lava")
                    )
                    count += 1
                feat.tiles_written = count
                bodies.append(feat)
        return bodies

    def generate_forest_decorations(
        self,
        world: Any,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        z: int,
        theme: Any,
        density: float = 0.15,
        decoration_ids: Optional[List[int]] = None,
    ) -> TerrainFeature:
        """
        Scatter decoration items on top of existing biome tiles.

        The generator does NOT change the ground — it only adds items to
        the tile (so it represents trees, rocks, bushes, etc).
        """
        from core.world.item import Item

        deco_ids = decoration_ids or list(getattr(theme, "decorations", []) or [])
        if not deco_ids:
            # Fallback to known nature-like items
            deco_ids = [2153, 2117, 1803, 1700, 1703, 1810]
        feat = TerrainFeature(
            name="forest_decorations",
            kind="forest",
            bounds=(x1, y1, x2, y2),
            ground_id=0,
            z=z,
            seed=self._seed ^ 0xB33F,
            metadata={"decoration_ids": list(deco_ids), "density": density},
        )
        count = 0
        for iy in range(y1, y2 + 1):
            for ix in range(x1, x2 + 1):
                if self._rng.random() > density:
                    continue
                tile = world.get_tile(ix, iy, z)
                if tile is None:
                    continue
                # Skip tiles that already have non-decoration items
                if tile.spawn is not None:
                    continue
                item_id = deco_ids[self._rng.randint(0, len(deco_ids) - 1)]
                tile.items.append(Item(itemid=item_id))
                count += 1
        feat.tiles_written = count
        return feat

    def generate_all(
        self,
        world: Any,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        z: int,
        theme: Any,
        with_water: bool = True,
        with_lava: bool = False,
        with_mountains: bool = True,
        with_hills: bool = True,
        with_forest: bool = True,
    ) -> Dict[str, Any]:
        """
        Run all the generators in priority order. Returns a dict with keys:
            mountains, hills, water, lava, forest
        """
        results: Dict[str, Any] = {}
        if with_mountains:
            results["mountains"] = self.generate_mountains(
                world,
                x1,
                y1,
                x2,
                y2,
                z,
                theme,
            )
        if with_hills:
            results["hills"] = self.generate_hills(
                world,
                x1,
                y1,
                x2,
                y2,
                z,
                theme,
            )
        if with_water:
            results["water"] = self.generate_water_bodies(
                world,
                x1,
                y1,
                x2,
                y2,
                z,
                theme,
            )
        if with_lava:
            results["lava"] = self.generate_lava_fields(
                world,
                x1,
                y1,
                x2,
                y2,
                z,
                theme,
            )
        if with_forest:
            results["forest"] = self.generate_forest_decorations(
                world,
                x1,
                y1,
                x2,
                y2,
                z,
                theme,
            )
        return results


# =============================================================================
# Module-level helpers
# =============================================================================


def generate_terrain(
    world: Any,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    z: int,
    theme: Any,
    seed: Optional[int] = None,
    with_water: bool = True,
    with_lava: bool = False,
    with_mountains: bool = True,
    with_hills: bool = True,
    with_forest: bool = True,
) -> Dict[str, Any]:
    """One-shot helper: run all terrain passes and return the result dict."""
    gen = TerrainGenerator(seed=seed)
    return gen.generate_all(
        world,
        x1,
        y1,
        x2,
        y2,
        z,
        theme,
        with_water=with_water,
        with_lava=with_lava,
        with_mountains=with_mountains,
        with_hills=with_hills,
        with_forest=with_forest,
    )


def generate_mountains(
    world: Any,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    z: int,
    theme: Any,
    seed: Optional[int] = None,
    threshold: float = 0.78,
    max_tiles: Optional[int] = None,
) -> TerrainFeature:
    """One-shot helper for mountain generation."""
    gen = TerrainGenerator(seed=seed)
    return gen.generate_mountains(
        world,
        x1,
        y1,
        x2,
        y2,
        z,
        theme,
        threshold=threshold,
        max_tiles=max_tiles,
    )


def generate_hills(
    world: Any,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    z: int,
    theme: Any,
    seed: Optional[int] = None,
    max_tiles: Optional[int] = None,
) -> TerrainFeature:
    """One-shot helper for hill generation."""
    gen = TerrainGenerator(seed=seed)
    return gen.generate_hills(
        world,
        x1,
        y1,
        x2,
        y2,
        z,
        theme,
        max_tiles=max_tiles,
    )


def generate_water_bodies(
    world: Any,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    z: int,
    theme: Any,
    seed: Optional[int] = None,
    max_tiles: Optional[int] = None,
) -> List[TerrainFeature]:
    """One-shot helper for water body generation."""
    gen = TerrainGenerator(seed=seed)
    return gen.generate_water_bodies(
        world,
        x1,
        y1,
        x2,
        y2,
        z,
        theme,
        max_tiles=max_tiles,
    )


def generate_lava_fields(
    world: Any,
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    z: int,
    theme: Any,
    seed: Optional[int] = None,
    max_tiles: Optional[int] = None,
) -> List[TerrainFeature]:
    """One-shot helper for lava field generation."""
    gen = TerrainGenerator(seed=seed)
    return gen.generate_lava_fields(
        world,
        x1,
        y1,
        x2,
        y2,
        z,
        theme,
        max_tiles=max_tiles,
    )


# Backwards-compatible alias for the old string-returning Lua-style helper.
def noise_generator_script(
    origin_x: int,
    origin_y: int,
    width: int,
    height: int,
    z: int,
    floor_high: int,
    floor_low: int,
) -> str:
    """Legacy Lua-style helper preserved for compatibility."""
    return (
        f"-- Procedural noise terrain generator\n"
        "if not app.hasMap() then\n    return\nend\n\n"
        f"app.transaction(function(map)\n"
        f"    for dx = 0, {width} - 1 do\n"
        f"        for dy = 0, {height} - 1 do\n"
        f"            local x = {origin_x} + dx\n"
        f"            local y = {origin_y} + dy\n"
        f"            local value = noise.simplex(x * 0.18, y * 0.18, 0)\n"
        f"            local tile = map:getOrCreateTile(x, y, {z})\n"
        f"            if value > 0.1 then\n"
        f"                tile.ground = {floor_high}\n"
        f"            else\n"
        f"                tile.ground = {floor_low}\n"
        f"            end\n"
        f"        end\n"
        f"    end\n"
        f"end)\n"
    )
