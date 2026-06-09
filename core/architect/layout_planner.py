"""
HITO 15 — AI Architect: Layout Planner
======================================

Decides WHERE each zone goes inside the world and HOW big it is.

The LayoutPlanner takes a sequence of zones (CityPlan, DungeonPlan,
HuntPlan, BossPlan, QuestPlan) and arranges them on a 2D world grid.

Layout strategies:
    - "city_centric" : city at center, hunts radiate around it, boss at edge
    - "linear"       : zones stacked left-to-right (good for "expansion" prompts)
    - "hub_spoke"    : city is the hub, all hunts connect to it
    - "scattered"    : zones are placed semi-randomly with no collision
    - "auto"         : choose the best strategy based on zone kinds

The planner also computes the world bounds, a road network, teleport
links, and the full set of waypoints that connect the zones.

Architecture:
    List[ZonePlan] + world_width + world_height
        ↓
    LayoutPlanner.arrange(...)
        ↓
    WorldLayout
        ├── zones:  List[PlacedZone]
        ├── roads:  List[Dict]
        ├── teleports: List[Dict]
        ├── waypoints: List[Dict]
        └── bounds: Tuple[int, int, int, int]
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .zone_planner import ZonePlanner


# =============================================================================
# PlacedZone — a zone plus its concrete position inside the world
# =============================================================================

@dataclass
class PlacedZone:
    """
    A zone (any kind) with its concrete position and size in world coords.
    """
    zone_kind: str                # "city" | "dungeon" | "hunt" | "boss" | "quest"
    name: str
    theme: str
    x: int                        # world coord (top-left)
    y: int                        # world coord (top-left)
    width: int                    # tiles
    height: int                   # tiles
    z: int = 7                    # default z
    level_min: int = 1
    level_max: int = 100
    band: str = "medium"
    plan: Any = None              # original plan dataclass
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_kind": self.zone_kind,
            "name": self.name,
            "theme": self.theme,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "z": self.z,
            "level_range": [self.level_min, self.level_max],
            "band": self.band,
            "metadata": self.metadata,
        }


# =============================================================================
# WorldLayout — the complete spatial arrangement
# =============================================================================

@dataclass
class WorldLayout:
    """
    Complete 2D layout of all zones, plus the routes that link them.
    """
    world_width: int
    world_height: int
    zones: List[PlacedZone] = field(default_factory=list)
    roads: List[Dict[str, Any]] = field(default_factory=list)
    teleports: List[Dict[str, Any]] = field(default_factory=list)
    waypoints: List[Dict[str, Any]] = field(default_factory=list)
    strategy: str = "auto"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def bounds(self) -> Tuple[int, int, int, int]:
        """Return (x1, y1, x2, y2) bounding box of all zones."""
        if not self.zones:
            return (0, 0, self.world_width, self.world_height)
        xs1 = [z.x for z in self.zones]
        ys1 = [z.y for z in self.zones]
        xs2 = [z.x + z.width for z in self.zones]
        ys2 = [z.y + z.height for z in self.zones]
        return (min(xs1), min(ys1), max(xs2), max(ys2))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "world_width": self.world_width,
            "world_height": self.world_height,
            "bounds": list(self.bounds()),
            "strategy": self.strategy,
            "zones": [z.to_dict() for z in self.zones],
            "roads": self.roads,
            "teleports": self.teleports,
            "waypoints": self.waypoints,
            "metadata": self.metadata,
        }


# =============================================================================
# Default sizing rules per zone kind
# =============================================================================

DEFAULT_SIZES: Dict[str, Tuple[int, int]] = {
    "city":    (60, 60),
    "dungeon": (40, 40),
    "hunt":    (50, 50),
    "boss":    (20, 20),
    "quest":   (16, 16),
}


# =============================================================================
# Layout Planner
# =============================================================================

class LayoutPlanner:
    """
    Places a list of zone plans onto a 2D world grid.

    Supports several layout strategies. The default is "auto" which
    picks the best strategy based on the zone kinds.

    Integrates with:
        - BlueprintRegistry (optional): prefers known blueprint sizes
        - ZonePlanner (optional): uses its difficulty classification
          to add per-zone notes

    Usage:
        planner = LayoutPlanner()
        layout = planner.arrange(
            zones=[city, hunt, hunt, hunt, boss],
            world_width=200, world_height=200,
        )
        for zone in layout.zones:
            print(zone.name, zone.x, zone.y, zone.width, zone.height)
    """

    SUPPORTED_STRATEGIES = (
        "auto", "city_centric", "linear", "hub_spoke", "scattered",
    )

    def __init__(
        self,
        blueprint_registry: Optional[Any] = None,
        zone_planner: Optional[ZonePlanner] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.blueprint_registry = blueprint_registry
        self.zone_planner = zone_planner or ZonePlanner()
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def arrange(
        self,
        zones: List[Any],
        world_width: int = 200,
        world_height: int = 200,
        strategy: str = "auto",
        z_level: int = 7,
        seed: Optional[int] = None,
    ) -> WorldLayout:
        """
        Arrange a list of zone plans into a WorldLayout.

        Args:
            zones: List of (CityPlan | DungeonPlan | HuntPlan |
                  BossPlan | QuestPlan). Order matters: first zone is
                  typically the city or main area.
            world_width: World width in tiles (default 200).
            world_height: World height in tiles (default 200).
            strategy: One of "auto", "city_centric", "linear", "hub_spoke",
                      "scattered".
            z_level: Default z (height) for all zones.
            seed: Optional random seed for reproducibility.

        Returns:
            WorldLayout with positioned zones, roads, and waypoints.
        """
        if not zones:
            return WorldLayout(
                world_width=world_width,
                world_height=world_height,
                strategy=strategy,
            )
        rng = random.Random(seed) if seed is not None else self._rng

        # Pick strategy
        if strategy == "auto":
            strategy = self._auto_strategy(zones)
        if strategy not in self.SUPPORTED_STRATEGIES:
            strategy = "city_centric"

        # Build PlacedZone objects with sizes
        placed: List[PlacedZone] = []
        for z in zones:
            size = self._size_for_zone(z)
            placed.append(self._to_placed(z, size, z_level))

        # Place them
        if strategy == "city_centric":
            placed = self._place_city_centric(placed, world_width, world_height, rng)
        elif strategy == "linear":
            placed = self._place_linear(placed, world_width, world_height)
        elif strategy == "hub_spoke":
            placed = self._place_hub_spoke(placed, world_width, world_height, rng)
        else:  # scattered
            placed = self._place_scattered(placed, world_width, world_height, rng)

        # Build roads, teleports, waypoints
        roads = self._build_roads(placed)
        teleports = self._build_teleports(placed)
        waypoints = self._build_waypoints(placed, z_level)

        return WorldLayout(
            world_width=world_width,
            world_height=world_height,
            zones=placed,
            roads=roads,
            teleports=teleports,
            waypoints=waypoints,
            strategy=strategy,
            metadata={"zone_count": len(placed)},
        )

    # ------------------------------------------------------------------
    # Strategy selection
    # ------------------------------------------------------------------

    def _auto_strategy(self, zones: List[Any]) -> str:
        kinds = [self._zone_kind(z) for z in zones]
        if kinds and kinds[0] == "city" and kinds[-1] == "boss":
            return "city_centric"
        if all(k in ("hunt", "boss") for k in kinds):
            return "linear"
        if kinds.count("city") == 1 and len(kinds) > 2:
            return "hub_spoke"
        return "scattered"

    # ------------------------------------------------------------------
    # Size computation
    # ------------------------------------------------------------------

    def _size_for_zone(self, zone: Any) -> Tuple[int, int]:
        """Compute (width, height) for a zone, consulting the blueprint
        registry if available."""
        kind = self._zone_kind(zone)
        w, h = DEFAULT_SIZES.get(kind, (40, 40))

        # If a blueprint is registered for this type/theme, use it as a hint
        if self.blueprint_registry is not None:
            try:
                theme = getattr(zone, "theme", None)
                if theme:
                    bp = self.blueprint_registry.get_blueprint(kind, f"{theme}_{kind}")
                    if bp is None:
                        bp = self.blueprint_registry.get_blueprint(kind)
                    if bp is not None:
                        bw = bp.get("width") or bp.get("size", [w, h])[0]
                        bh = bp.get("height") or bp.get("size", [w, h])[1]
                        if isinstance(bw, int) and isinstance(bh, int) and bw > 0 and bh > 0:
                            w, h = bw, bh
            except Exception:
                pass

        # Hunt area_size override
        if kind == "hunt" and hasattr(zone, "area_size"):
            w, h = zone.area_size

        # Boss arena_size override
        if kind == "boss" and hasattr(zone, "arena_size"):
            w, h = zone.arena_size

        return (max(8, int(w)), max(8, int(h)))

    def _to_placed(self, zone: Any, size: Tuple[int, int], z: int) -> PlacedZone:
        kind = self._zone_kind(zone)
        name = getattr(zone, "name", kind)
        theme = getattr(zone, "theme", "generic")
        lo = getattr(zone, "min_level", getattr(zone, "level_min", 1))
        hi = getattr(zone, "max_level", getattr(zone, "level_max", 100))
        # Difficulty band via the zone_planner
        try:
            band = self.zone_planner.classify_range(lo, hi)
        except Exception:
            band = "medium"
        return PlacedZone(
            zone_kind=kind,
            name=name,
            theme=theme,
            x=0, y=0,                  # will be set by placement strategy
            width=size[0], height=size[1],
            z=z,
            level_min=lo, level_max=hi,
            band=band,
            plan=zone,
        )

    @staticmethod
    def _zone_kind(zone: Any) -> str:
        cls = type(zone).__name__.lower()
        if "city" in cls:
            return "city"
        if "dungeon" in cls:
            return "dungeon"
        if "hunt" in cls:
            return "hunt"
        if "boss" in cls:
            return "boss"
        if "quest" in cls:
            return "quest"
        return getattr(zone, "zone_kind", "hunt")

    # ------------------------------------------------------------------
    # Placement strategies
    # ------------------------------------------------------------------

    def _place_city_centric(
        self,
        placed: List[PlacedZone],
        w: int, h: int,
        rng: random.Random,
    ) -> List[PlacedZone]:
        """City at center, hunts in a ring around it, boss at edge."""
        if not placed:
            return placed

        # Find the city (or first zone) and put it at the center
        city_idx = next(
            (i for i, z in enumerate(placed) if z.zone_kind == "city"),
            0,
        )
        city = placed[city_idx]
        city.x = (w - city.width) // 2
        city.y = (h - city.height) // 2

        ring = [z for i, z in enumerate(placed) if i != city_idx]
        if not ring:
            return placed

        # Boss goes to the far edge
        boss_zones = [z for z in ring if z.zone_kind == "boss"]
        other_zones = [z for z in ring if z.zone_kind != "boss"]

        if boss_zones:
            boss = boss_zones[0]
            boss.x = w - boss.width - 5
            boss.y = (h - boss.height) // 2 + rng.randint(-10, 10)

        # Other zones around the city in a ring
        cx = w // 2
        cy = h // 2
        radius = max(city.width, city.height) // 2 + 25
        n = len(other_zones)
        for i, z in enumerate(other_zones):
            angle = (i / max(1, n)) * 2 * math.pi
            r = radius
            zx = int(cx + r * math.cos(angle)) - z.width // 2
            zy = int(cy + r * math.sin(angle)) - z.height // 2
            z.x = max(0, min(zx, w - z.width))
            z.y = max(0, min(zy, h - z.height))

        return placed

    def _place_linear(
        self,
        placed: List[PlacedZone],
        w: int, h: int,
    ) -> List[PlacedZone]:
        """Place zones left-to-right in a single row."""
        if not placed:
            return placed

        margin = 5
        x_cursor = margin
        y_center = (h - max(p.height for p in placed)) // 2
        for z in placed:
            z.x = x_cursor
            z.y = max(margin, y_center)
            x_cursor += z.width + margin
        return placed

    def _place_hub_spoke(
        self,
        placed: List[PlacedZone],
        w: int, h: int,
        rng: random.Random,
    ) -> List[PlacedZone]:
        """City in the center, hunts arranged around it like spokes."""
        if not placed:
            return placed

        city_idx = next(
            (i for i, z in enumerate(placed) if z.zone_kind == "city"),
            0,
        )
        city = placed[city_idx]
        city.x = (w - city.width) // 2
        city.y = (h - city.height) // 2

        ring = [z for i, z in enumerate(placed) if i != city_idx]
        n = len(ring)
        cx = w // 2
        cy = h // 2
        for i, z in enumerate(ring):
            angle = (i / max(1, n)) * 2 * math.pi
            r = max(city.width, city.height) // 2 + 30
            zx = int(cx + r * math.cos(angle)) - z.width // 2
            zy = int(cy + r * math.sin(angle)) - z.height // 2
            z.x = max(0, min(zx, w - z.width))
            z.y = max(0, min(zy, h - z.height))
        return placed

    def _place_scattered(
        self,
        placed: List[PlacedZone],
        w: int, h: int,
        rng: random.Random,
    ) -> List[PlacedZone]:
        """Place zones in a deterministic but spread-out fashion."""
        if not placed:
            return placed

        margin = 5
        cols = max(1, int(len(placed) ** 0.5))
        rows = (len(placed) + cols - 1) // cols
        cell_w = (w - 2 * margin) // cols
        cell_h = (h - 2 * margin) // rows
        for i, z in enumerate(placed):
            col = i % cols
            row = i // cols
            z.x = margin + col * cell_w + (cell_w - z.width) // 2
            z.y = margin + row * cell_h + (cell_h - z.height) // 2
        return placed

    # ------------------------------------------------------------------
    # Roads, teleports, waypoints
    # ------------------------------------------------------------------

    def _build_roads(self, placed: List[PlacedZone]) -> List[Dict[str, Any]]:
        """
        Build a road network connecting all placed zones.

        Roads go from the city (or first zone) to every other zone
        using an L-shaped Manhattan path.
        """
        if not placed:
            return []

        # Find anchor: city if any, else first zone
        anchor = next(
            (z for z in placed if z.zone_kind == "city"),
            placed[0],
        )
        ax = anchor.x + anchor.width // 2
        ay = anchor.y + anchor.height // 2
        roads: List[Dict[str, Any]] = []

        for z in placed:
            if z is anchor:
                continue
            zx = z.x + z.width // 2
            zy = z.y + z.height // 2
            path: List[Dict[str, int]] = []
            mid_x = zx
            step_x = 1 if mid_x >= ax else -1
            for x in range(ax, mid_x + step_x, step_x):
                path.append({"x": int(x), "y": int(ay), "z": anchor.z})
            step_y = 1 if zy >= ay else -1
            for y in range(ay, zy + step_y, step_y):
                path.append({"x": int(mid_x), "y": int(y), "z": anchor.z})
            roads.append({
                "type": "main_road",
                "from": anchor.name,
                "to": z.name,
                "path": path,
                "length": len(path),
            })

        return roads

    def _build_teleports(self, placed: List[PlacedZone]) -> List[Dict[str, Any]]:
        if not placed:
            return []
        city = next((z for z in placed if z.zone_kind == "city"), None)
        if city is None:
            return []
        teleports: List[Dict[str, Any]] = []
        for z in placed:
            if z is city:
                continue
            if z.zone_kind in ("dungeon", "boss"):
                teleports.append({
                    "name": f"teleport_{city.name}_to_{z.name}",
                    "from": {
                        "x": city.x + city.width - 1,
                        "y": city.y + city.height // 2,
                        "z": city.z,
                    },
                    "to": {
                        "x": z.x + z.width // 2,
                        "y": z.y + z.height // 2,
                        "z": z.z,
                    },
                    "type": "teleport",
                })
        return teleports

    def _build_waypoints(
        self, placed: List[PlacedZone], z: int,
    ) -> List[Dict[str, Any]]:
        waypoints: List[Dict[str, Any]] = []
        for zone in placed:
            waypoints.append({
                "name": f"waypoint_{zone.name}",
                "x": zone.x + zone.width // 2,
                "y": zone.y + zone.height // 2,
                "z": z,
                "zone_kind": zone.zone_kind,
                "theme": zone.theme,
            })
        return waypoints
