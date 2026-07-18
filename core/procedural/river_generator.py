"""
HITO 16 - Procedural World Generation: River Generator
======================================================

Generates rivers as connected paths of water tiles that flow from a
source to a sink. The generator uses a simple deterministic approach:

    1. Choose a start point and an end point (start = high elevation,
       end = low elevation / edge of world).
    2. Walk toward the end with a slight random perturbation so the
       river curves naturally.
    3. Optionally split into tributaries.
    4. Optionally widen the river as it approaches the mouth.

Rivers are placed AFTER the terrain pass, so they always win over biome
ground. They never overwrite structures, spawns, or city tiles (only
empty or water tiles can be replaced).

Architecture:
    River (dataclass)             -> one complete river
    RiverSegment (dataclass)      -> one path
    RiverGenerator                -> the engine
        .generate_river(world, source, sink, ...)
        .generate_rivers(world, sources, sinks, ...)

Public API:
    RiverGenerator
    River
    generate_river(world, source, sink, ...)            -> River
    generate_rivers(world, sources, sinks, ...)          -> List[River]
    RIVER_GROUND_IDS (theme -> id)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# =============================================================================
# Static knowledge: river tile IDs per theme
# =============================================================================

RIVER_GROUND_IDS: Dict[str, int] = {
    "generic": 4597,
    "issavi": 4597,
    "roshamuul": 4598,
    "soul_war": 600,  # lava-style
    "library": 4597,
    "yalahar": 4597,
    "falcon": 4597,
    "cobra": 4597,
    "ice": 4597,
    "jungle": 4597,
    "thais": 4597,
    "venore": 4598,
    "ankrahmun": 4597,
}

RIVER_BANK_IDS: Dict[str, int] = {
    "generic": 361,
    "issavi": 103,
    "roshamuul": 231,
    "soul_war": 231,
    "library": 103,
    "yalahar": 103,
    "falcon": 103,
    "cobra": 103,
    "ice": 672,
    "jungle": 103,
    "thais": 103,
    "venore": 103,
    "ankrahmun": 103,
}


def get_river_ground_id(theme: Any, fallback: int = 4597) -> int:
    name = _theme_name(theme)
    return RIVER_GROUND_IDS.get(name, fallback)


def get_river_bank_id(theme: Any, fallback: int = 361) -> int:
    name = _theme_name(theme)
    return RIVER_BANK_IDS.get(name, fallback)


def _theme_name(theme: Any) -> str:
    if theme is None:
        return "generic"
    if isinstance(theme, str):
        return theme.lower()
    return str(getattr(theme, "name", "generic")).lower()


# =============================================================================
# Data classes
# =============================================================================


@dataclass
class RiverPoint:
    x: int
    y: int
    z: int = 7
    width: int = 1
    is_mouth: bool = False
    is_source: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "width": self.width,
            "is_mouth": self.is_mouth,
            "is_source": self.is_source,
        }


@dataclass
class River:
    """A single river from source to mouth."""

    name: str
    points: List[RiverPoint]
    z: int
    ground_id: int
    bank_id: int
    width: int = 1
    kind: str = "river"  # "river" | "lava_river" | "stream"
    tiles_written: int = 0
    bank_tiles: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def length(self) -> int:
        return len(self.points)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "points": [p.to_dict() for p in self.points],
            "z": self.z,
            "ground_id": self.ground_id,
            "bank_id": self.bank_id,
            "width": self.width,
            "kind": self.kind,
            "tiles_written": self.tiles_written,
            "bank_tiles": self.bank_tiles,
            "length": self.length,
            "metadata": dict(self.metadata),
        }


# =============================================================================
# RiverGenerator
# =============================================================================


class RiverGenerator:
    """
    Generates river paths in a WorldModel.

    Usage:
        gen = RiverGenerator(seed=42)
        river = gen.generate_river(
            world,
            source=(0, 0), sink=(99, 99),
            z=7, theme="issavi", width=2,
        )
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_river(
        self,
        world: Any,
        source: Tuple[int, int],
        sink: Tuple[int, int],
        z: int,
        theme: Any,
        width: int = 1,
        kind: str = "river",
        meander: float = 0.4,
        ground_id: Optional[int] = None,
        bank_id: Optional[int] = None,
        add_banks: bool = True,
        name: Optional[str] = None,
        max_length: int = 2000,
    ) -> River:
        """
        Build a single river from `source` to `sink`.

        Args:
            world: WorldModel to write into.
            source: (x, y) starting point.
            sink: (x, y) ending point (mouth).
            z: Z-layer.
            theme: Theme name or ThemeAssets.
            width: Max river width (tiles).
            kind: "river" | "lava_river" | "stream".
            meander: 0..1 - how much the river wanders (0=straight, 1=very curvy).
            ground_id: Override water tile ID.
            bank_id: Override bank tile ID.
            add_banks: If True, place bank tiles on both sides of the river.
            name: Optional river name.
            max_length: Hard cap on the number of river points.
        """
        gid = ground_id if ground_id is not None else get_river_ground_id(theme)
        bid = bank_id if bank_id is not None else get_river_bank_id(theme)

        path = self._trace_path(
            source=source,
            sink=sink,
            meander=meander,
            max_length=max_length,
        )

        if not path:
            return River(
                name=name or "river_empty",
                points=[],
                z=z,
                ground_id=gid,
                bank_id=bid,
                width=width,
                kind=kind,
            )

        from core.world.tile import Tile

        points: List[RiverPoint] = []
        for i, (x, y) in enumerate(path):
            # Widen the river as it approaches the mouth
            t = i / max(1, len(path) - 1)
            w = max(1, int(round(width * (0.5 + 0.5 * t))))
            rp = RiverPoint(
                x=x,
                y=y,
                z=z,
                width=w,
                is_source=(i == 0),
                is_mouth=(i == len(path) - 1),
            )
            points.append(rp)
            # Place the river tile(s) - skip if the tile has a structure/important ground
            for dy in range(-(w // 2), w // 2 + 1):
                tx, ty = x, y + dy
                # Clamp negative coordinates to avoid invalid tiles
                if tx < 0 or ty < 0:
                    continue
                existing = world.get_tile(tx, ty, z)
                if (
                    existing is not None
                    and existing.zone
                    and (
                        existing.zone.startswith("structure:")
                        or existing.zone.startswith("city:")
                        or existing.zone.startswith("spawn:")
                    )
                ):
                    continue
                world.set_tile(Tile(x=tx, y=ty, z=z, ground=gid, zone=f"river:{kind}"))

        river = River(
            name=name or f"river_{source[0]}_{source[1]}_{sink[0]}_{sink[1]}",
            points=points,
            z=z,
            ground_id=gid,
            bank_id=bid,
            width=width,
            kind=kind,
        )
        river.tiles_written = sum(p.width for p in points)

        # Banks
        if add_banks:
            bank_tiles = 0
            for rp in points:
                for dy in range(-(rp.width // 2) - 1, rp.width // 2 + 2):
                    if -rp.width // 2 <= dy <= rp.width // 2:
                        continue
                    tx, ty = rp.x, rp.y + dy
                    # Clamp negative coordinates to avoid invalid tiles
                    if tx < 0 or ty < 0:
                        continue
                    existing = world.get_tile(tx, ty, z)
                    if (
                        existing is not None
                        and existing.zone
                        and (
                            existing.zone.startswith("structure:")
                            or existing.zone.startswith("city:")
                            or existing.zone.startswith("spawn:")
                            or existing.zone.startswith("river:")
                        )
                    ):
                        continue
                    world.set_tile(Tile(x=tx, y=ty, z=z, ground=bid, zone="river:bank"))
                    bank_tiles += 1
            river.bank_tiles = bank_tiles
        return river

    def generate_rivers(
        self,
        world: Any,
        sources: List[Tuple[int, int]],
        sinks: List[Tuple[int, int]],
        z: int,
        theme: Any,
        width: int = 1,
        kind: str = "river",
        meander: float = 0.4,
        add_banks: bool = True,
    ) -> List[River]:
        """Generate a list of rivers. Pairs sources[i] with sinks[i]."""
        rivers: List[River] = []
        n = max(len(sources), len(sinks))
        for i in range(n):
            s = sources[i % len(sources)]
            t = sinks[i % len(sinks)]
            r = self.generate_river(
                world,
                source=s,
                sink=t,
                z=z,
                theme=theme,
                width=width,
                kind=kind,
                meander=meander,
                add_banks=add_banks,
                name=f"river_{i + 1}",
            )
            rivers.append(r)
        return rivers

    # ------------------------------------------------------------------
    # Path tracing
    # ------------------------------------------------------------------

    def _trace_path(
        self,
        source: Tuple[int, int],
        sink: Tuple[int, int],
        meander: float,
        max_length: int,
    ) -> List[Tuple[int, int]]:
        """Walk a perturbed path from source to sink."""
        sx, sy = source
        tx, ty = sink
        path: List[Tuple[int, int]] = [(sx, sy)]
        x, y = sx, sy
        for _ in range(max_length):
            dx = tx - x
            dy = ty - y
            if abs(dx) <= 1 and abs(dy) <= 1:
                path.append((tx, ty))
                break
            step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
            step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)
            # Pick a primary axis
            if abs(dx) >= abs(dy):
                nx, ny = x + step_x, y
                # small chance to also move on the other axis
                if self._rng.random() < meander and step_y != 0:
                    ny = y + step_y
            else:
                nx, ny = x, y + step_y
                if self._rng.random() < meander and step_x != 0:
                    nx = x + step_x
            if (nx, ny) == (x, y):
                nx, ny = x + step_x, y + step_y
            path.append((nx, ny))
            x, y = nx, ny
        return path


# =============================================================================
# Module-level helpers
# =============================================================================


def generate_river(
    world: Any,
    source: Tuple[int, int],
    sink: Tuple[int, int],
    z: int,
    theme: Any,
    width: int = 1,
    kind: str = "river",
    meander: float = 0.4,
    seed: Optional[int] = None,
) -> River:
    """One-shot helper: build a single river."""
    gen = RiverGenerator(seed=seed)
    return gen.generate_river(
        world,
        source,
        sink,
        z,
        theme,
        width=width,
        kind=kind,
        meander=meander,
    )


def generate_rivers(
    world: Any,
    sources: List[Tuple[int, int]],
    sinks: List[Tuple[int, int]],
    z: int,
    theme: Any,
    width: int = 1,
    kind: str = "river",
    meander: float = 0.4,
    seed: Optional[int] = None,
) -> List[River]:
    """One-shot helper: build multiple rivers."""
    gen = RiverGenerator(seed=seed)
    return gen.generate_rivers(
        world,
        sources,
        sinks,
        z,
        theme,
        width=width,
        kind=kind,
        meander=meander,
    )
