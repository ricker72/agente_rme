"""
HITO 16 - Procedural World Generation: Road Generator
=====================================================

Builds a road network that connects placed zones inside a WorldModel.

The generator supports:
    - straight L-shaped Manhattan paths between two points
    - variable-width roads (1 or 3 tiles wide)
    - custom road ground IDs per theme
    - bridges over water tiles (placed at the same coords with a
      special "bridge" zone tag)
    - per-path metadata (length, kind, from, to, ...)

Architecture:
    RoadSegment (dataclass)        -> one path between two anchors
    RoadNetwork (dataclass)        -> collection of segments + meta
    RoadGenerator                  -> the engine
        .build_path(world, a, b, ...)
        .connect_points(world, points, ...)
        .connect_zones(world, zones, ...)
        .build_city_grid(world, x, y, w, h, ...)
        .build_bridge(world, x, y, z)

Public API:
    RoadGenerator
    RoadSegment
    RoadNetwork
    generate_road(world, a, b, ...)            -> RoadSegment
    connect_zones(world, zones, ...)           -> RoadNetwork
    build_city_grid(world, x, y, w, h, ...)    -> RoadNetwork
    build_bridge(world, x, y, z, ...)          -> int
    ROAD_GROUND_IDS (theme -> id)
    BRIDGE_GROUND_IDS
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# =============================================================================
# Static knowledge: road & bridge tile IDs per theme
# =============================================================================

# Default ground ID for a road on each theme
ROAD_GROUND_IDS: Dict[str, int] = {
    "generic":    360,
    "issavi":     415,
    "roshamuul":  1053,
    "soul_war":   514,
    "library":    396,
    "yalahar":    450,
    "falcon":     428,
    "cobra":      514,
    "ice":        670,
    "jungle":     440,
    "thais":      351,
    "venore":     360,
    "ankrahmun":  480,
}

# Bridge tile IDs
BRIDGE_GROUND_IDS: Dict[str, int] = {
    "generic":   3610,
    "issavi":    3610,
    "roshamuul": 3610,
    "soul_war":  3610,
    "library":   3610,
    "yalahar":   3610,
    "falcon":    3610,
    "cobra":     3610,
    "ice":       3610,
    "jungle":    3610,
    "thais":     3610,
    "venore":    3610,
    "ankrahmun": 3610,
}


def get_road_ground_id(theme: Any, fallback: int = 360) -> int:
    name = _theme_name(theme)
    return ROAD_GROUND_IDS.get(name, fallback)


def get_bridge_ground_id(theme: Any, fallback: int = 3610) -> int:
    name = _theme_name(theme)
    return BRIDGE_GROUND_IDS.get(name, fallback)


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
class Point:
    x: int
    y: int
    z: int = 7
    label: str = ""

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Point":
        return cls(
            x=int(d.get("x", 0)),
            y=int(d.get("y", 0)),
            z=int(d.get("z", 7)),
            label=str(d.get("label", "")),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"x": self.x, "y": self.y, "z": self.z, "label": self.label}


@dataclass
class RoadSegment:
    """A single connected path of road tiles."""
    name: str
    points: List[Point]
    z: int
    width: int
    ground_id: int
    kind: str = "road"           # "road" | "bridge" | "path" | "city_street"
    from_label: str = ""
    to_label: str = ""
    tiles_written: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def length(self) -> int:
        return len(self.points)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "points": [p.to_dict() for p in self.points],
            "z": self.z,
            "width": self.width,
            "ground_id": self.ground_id,
            "kind": self.kind,
            "from": self.from_label,
            "to": self.to_label,
            "tiles_written": self.tiles_written,
            "length": self.length,
            "metadata": dict(self.metadata),
        }


@dataclass
class RoadNetwork:
    """A whole network of road segments inside the world."""
    segments: List[RoadSegment] = field(default_factory=list)
    bridges: List[Point] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tiles(self) -> int:
        return sum(s.tiles_written for s in self.segments)

    @property
    def total_segments(self) -> int:
        return len(self.segments)

    def segments_by_kind(self, kind: str) -> List[RoadSegment]:
        return [s for s in self.segments if s.kind == kind]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segments": [s.to_dict() for s in self.segments],
            "bridges": [p.to_dict() for p in self.bridges],
            "total_tiles": self.total_tiles,
            "total_segments": self.total_segments,
            "metadata": dict(self.metadata),
        }


# =============================================================================
# Path helpers
# =============================================================================

def _manhattan_path(a: Point, b: Point) -> List[Point]:
    """L-shaped Manhattan path from a to b (horizontal first, then vertical)."""
    path: List[Point] = []
    z = a.z

    step_x = 1 if b.x >= a.x else -1
    if step_x == 0:
        step_x = 1
    for x in range(a.x, b.x + step_x, step_x):
        path.append(Point(x=x, y=a.y, z=z))

    # Remove duplicate if b is on the same row
    if path and path[-1].x == b.x:
        path.pop()

    step_y = 1 if b.y >= a.y else -1
    if step_y == 0:
        step_y = 1
    last_x = b.x
    for y in range(a.y, b.y + step_y, step_y):
        path.append(Point(x=last_x, y=y, z=z))

    return path


def _thick_points(points: Sequence[Point], width: int) -> List[Point]:
    """Return a wider set of points around a polyline path."""
    if width <= 1 or not points:
        return list(points)
    out: List[Point] = []
    seen: set = set()
    for p in points:
        for dx in range(-(width // 2), width // 2 + 1):
            for dy in range(-(width // 2), width // 2 + 1):
                key = (p.x + dx, p.y + dy, p.z)
                if key in seen:
                    continue
                seen.add(key)
                out.append(Point(x=p.x + dx, y=p.y + dy, z=p.z))
    return out


# =============================================================================
# RoadGenerator
# =============================================================================

class RoadGenerator:
    """
    Builds road networks inside a WorldModel.

    Usage:
        gen = RoadGenerator(seed=42)
        net = gen.connect_zones(
            world, [
                {"x": 100, "y": 100, "z": 7, "label": "city"},
                {"x": 200, "y": 200, "z": 7, "label": "hunt1"},
            ],
            theme="issavi",
        )
    """

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_path(
        self,
        world: Any,
        a: Point,
        b: Point,
        theme: Any,
        width: int = 1,
        kind: str = "road",
        ground_id: Optional[int] = None,
        name: Optional[str] = None,
        auto_bridge: bool = True,
    ) -> RoadSegment:
        """
        Build one road segment from a -> b.

        Args:
            world: WorldModel to write into.
            a, b: Endpoints.
            theme: Theme name or ThemeAssets.
            width: Tile width of the road (1 or 3).
            kind: "road" | "bridge" | "path" | "city_street".
            ground_id: Override the road ground ID.
            name: Optional segment name.
            auto_bridge: If True and the road crosses water, mark the
                         water tile as a bridge.
        """
        gid = ground_id if ground_id is not None else get_road_ground_id(theme)
        bridge_gid = get_bridge_ground_id(theme)

        path = _manhattan_path(a, b)
        wide = _thick_points(path, width)

        from core.world.tile import Tile

        seg_name = name or f"road_{a.label or a.x}_{a.y}_to_{b.label or b.x}_{b.y}"
        seg = RoadSegment(
            name=seg_name,
            points=wide,
            z=a.z,
            width=width,
            ground_id=gid,
            kind=kind,
            from_label=a.label,
            to_label=b.label,
        )

        for p in wide:
            existing = world.get_tile(p.x, p.y, p.z)
            is_water = (
                existing is not None
                and existing.ground in (4597, 4598, 4600, 4601)
            )
            if auto_bridge and is_water:
                # Replace water with bridge tile and record it
                new_gid = bridge_gid
                zone = "road:bridge"
            else:
                new_gid = gid
                zone = f"road:{kind}"
            world.set_tile(Tile(x=p.x, y=p.y, z=p.z,
                                ground=new_gid, zone=zone))
            seg.tiles_written += 1
        return seg

    def connect_points(
        self,
        world: Any,
        points: List[Dict[str, Any]],
        theme: Any,
        width: int = 1,
        kind: str = "road",
        name_prefix: str = "path",
    ) -> RoadNetwork:
        """Connect a list of points in order (P1 -> P2 -> P3 -> ...)."""
        pts = [Point.from_dict(p) for p in points]
        if len(pts) < 2:
            return RoadNetwork(metadata={"points": len(pts), "theme": _theme_name(theme)})
        net = RoadNetwork(metadata={"theme": _theme_name(theme), "kind": kind})
        for i in range(len(pts) - 1):
            seg = self.build_path(
                world, pts[i], pts[i + 1], theme,
                width=width, kind=kind,
                name=f"{name_prefix}_{i + 1}",
            )
            net.segments.append(seg)
        return net

    def connect_zones(
        self,
        world: Any,
        zones: List[Any],
        theme: Any,
        width: int = 1,
        kind: str = "road",
    ) -> RoadNetwork:
        """
        Connect a list of zones by their centers.

        `zones` can be:
            - dicts with x, y, z, name
            - objects with .x .y .z .name attributes
            - PlacedZone instances (uses .x + .width//2, etc.)
        """
        net = RoadNetwork(metadata={"theme": _theme_name(theme), "kind": kind})
        if not zones:
            return net
        anchors = [self._zone_anchor(z) for z in zones]
        for i in range(len(anchors) - 1):
            seg = self.build_path(
                world, anchors[i], anchors[i + 1], theme,
                width=width, kind=kind,
                name=f"road_{i + 1}",
            )
            net.segments.append(seg)
        return net

    def build_city_grid(
        self,
        world: Any,
        x: int, y: int, width: int, height: int,
        z: int,
        theme: Any,
        step: int = 4,
        margin: int = 1,
        ground_id: Optional[int] = None,
    ) -> RoadNetwork:
        """
        Build a regular grid of roads inside a city block.

        Args:
            x, y, width, height: City bounds (inclusive of width/height).
            z: Z-layer.
            step: Distance between parallel roads.
            margin: Distance from city edge to first road.
        """
        gid = ground_id if ground_id is not None else get_road_ground_id(theme)
        from core.world.tile import Tile
        net = RoadNetwork(
            metadata={"theme": _theme_name(theme), "kind": "city_street", "grid_step": step},
        )

        x0 = x + margin
        y0 = y + margin
        x1 = x + width - 1 - margin
        y1 = y + height - 1 - margin

        # Horizontal streets
        iy = y0
        row_index = 0
        while iy <= y1:
            pts: List[Point] = []
            for ix in range(x0, x1 + 1):
                pts.append(Point(x=ix, y=iy, z=z))
            seg = RoadSegment(
                name=f"h_street_{row_index}",
                points=pts,
                z=z,
                width=1,
                ground_id=gid,
                kind="city_street",
                from_label=f"h{row_index}_l",
                to_label=f"h{row_index}_r",
            )
            for p in pts:
                world.set_tile(Tile(x=p.x, y=p.y, z=p.z,
                                    ground=gid, zone="road:city_street"))
            seg.tiles_written = len(pts)
            net.segments.append(seg)
            iy += step
            row_index += 1

        # Vertical streets
        ix = x0
        col_index = 0
        while ix <= x1:
            pts = []
            for iy2 in range(y0, y1 + 1):
                pts.append(Point(x=ix, y=iy2, z=z))
            seg = RoadSegment(
                name=f"v_street_{col_index}",
                points=pts,
                z=z,
                width=1,
                ground_id=gid,
                kind="city_street",
                from_label=f"v{col_index}_t",
                to_label=f"v{col_index}_b",
            )
            for p in pts:
                world.set_tile(Tile(x=p.x, y=p.y, z=p.z,
                                    ground=gid, zone="road:city_street"))
            seg.tiles_written = len(pts)
            net.segments.append(seg)
            ix += step
            col_index += 1

        return net

    def build_bridge(
        self,
        world: Any,
        x: int, y: int, z: int,
        theme: Any,
        ground_id: Optional[int] = None,
    ) -> int:
        """Place a single bridge tile and return 1 (success)."""
        gid = ground_id if ground_id is not None else get_bridge_ground_id(theme)
        from core.world.tile import Tile
        world.set_tile(Tile(x=x, y=y, z=z, ground=gid, zone="road:bridge"))
        return 1

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _zone_anchor(self, zone: Any) -> Point:
        if isinstance(zone, dict):
            x = int(zone.get("x", 0))
            y = int(zone.get("y", 0))
            z = int(zone.get("z", 7))
            label = str(zone.get("name") or zone.get("label") or "")
        else:
            # PlacedZone or zone plan
            x = getattr(zone, "x", 0)
            y = getattr(zone, "y", 0)
            z = getattr(zone, "z", 7)
            w = getattr(zone, "width", 0)
            h = getattr(zone, "height", 0)
            if w:
                x = x + w // 2
            if h:
                y = y + h // 2
            label = str(getattr(zone, "name", "") or "")
        return Point(x=x, y=y, z=z, label=label)


# =============================================================================
# Module-level helpers
# =============================================================================

def generate_road(
    world: Any,
    a: Dict[str, Any],
    b: Dict[str, Any],
    theme: Any,
    width: int = 1,
    kind: str = "road",
    seed: Optional[int] = None,
) -> RoadSegment:
    """One-shot helper: build a single road between two anchor dicts."""
    gen = RoadGenerator(seed=seed)
    return gen.build_path(
        world, Point.from_dict(a), Point.from_dict(b), theme,
        width=width, kind=kind,
    )


def connect_zones(
    world: Any,
    zones: List[Any],
    theme: Any,
    width: int = 1,
    kind: str = "road",
    seed: Optional[int] = None,
) -> RoadNetwork:
    """One-shot helper: connect a list of zones by their centers."""
    gen = RoadGenerator(seed=seed)
    return gen.connect_zones(world, zones, theme, width=width, kind=kind)


def build_city_grid(
    world: Any,
    x: int, y: int, width: int, height: int,
    z: int,
    theme: Any,
    step: int = 4,
    margin: int = 1,
    seed: Optional[int] = None,
) -> RoadNetwork:
    """One-shot helper: build a regular city street grid."""
    gen = RoadGenerator(seed=seed)
    return gen.build_city_grid(
        world, x, y, width, height, z, theme, step=step, margin=margin,
    )


def build_bridge(
    world: Any,
    x: int, y: int, z: int,
    theme: Any,
    ground_id: Optional[int] = None,
    seed: Optional[int] = None,
) -> int:
    """One-shot helper: place a single bridge tile."""
    gen = RoadGenerator(seed=seed)
    return gen.build_bridge(world, x, y, z, theme, ground_id=ground_id)


# Backwards-compatible alias for the old string-returning Lua-style helper.
def road_generator_lua(x1: int, y1: int, x2: int, y2: int, z: int, floor_id: int) -> str:
    """Legacy Lua-style helper preserved for compatibility."""
    return (
        f"-- Road generator\n"
        "if not app.hasMap() then\n    return\nend\n\n"
        f"app.transaction(function(map)\n"
        f"    for x = {x1}, {x2} do\n"
        f"        local tile = map:getOrCreateTile(x, {y1}, {z})\n"
        f"        tile.ground = {floor_id}\n"
        f"    end\n"
        f"    for y = {y1}, {y2} do\n"
        f"        local tile = map:getOrCreateTile({x1}, y, {z})\n"
        f"        tile.ground = {floor_id}\n"
        f"    end\n"
        f"end)\n"
    )
   