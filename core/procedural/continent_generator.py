"""
HITO 16 - Procedural World Generation: Continent Generator
==========================================================

The ContinentGenerator is the top-level orchestrator for procedural
world generation. It takes a `WorldPlan` (output of HITO 15's
AIArchitect) and produces a fully populated `WorldModel`.

Pipeline (in order):
    1. Continental biome base layer (grass / sand / snow / ...)
    2. Terrain features (mountains, hills, water bodies, lava, forest)
    3. River network (from sources to sinks)
    4. Per-zone biome pass (refines the area around each zone)
    5. City structures (temple, depot, market, plaza, ...)
    6. Dungeon structures (entrance, rooms, boss arena)
    7. Hunt areas (open grounds with spawns)
    8. Boss arenas (decorated enclosure with boss spawn)
    9. Quest rooms (small interiors with NPCs)
   10. Road network connecting every zone
   11. City street grids inside each city
   12. Region definitions (so the world knows about each zone)

The generator uses the AIArchitect's `theme_assets` for every kind of
visual decision (grounds, walls, decorations, monsters). It is fully
deterministic given a seed.

Architecture:
    WorldPlan (input) -> ContinentGenerator.generate(plan) -> WorldModel

Public API:
    ContinentGenerator
    ContinentResult (dataclass)
    generate_continent(plan) -> WorldModel
    generate_from_prompt(prompt) -> WorldModel    (uses AIArchitect)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from core.world import WorldModel, Tile, Item, Spawn, Structure, Region

from .biome_generator import (
    BiomeGenerator, BiomeTile, get_biome_palette, pick_primary_tag,
    BIOME_PALETTES, BIOME_TAG_BY_THEME,
)
from .terrain_generator import (
    TerrainGenerator, TerrainFeature, get_terrain_ground_id,
    TERRAIN_GROUND_IDS,
)
from .road_generator import (
    RoadGenerator, RoadSegment, RoadNetwork, Point,
    get_road_ground_id, get_bridge_ground_id,
    ROAD_GROUND_IDS, BRIDGE_GROUND_IDS,
)
from .river_generator import (
    RiverGenerator, River, RiverPoint,
    get_river_ground_id, get_river_bank_id,
    RIVER_GROUND_IDS, RIVER_BANK_IDS,
)


# =============================================================================
# ContinentResult — what the generator produced
# =============================================================================

@dataclass
class ContinentResult:
    """Aggregated report of a full continent generation."""
    world: WorldModel
    zones_placed: List[Dict[str, Any]] = field(default_factory=list)
    roads: List[RoadSegment] = field(default_factory=list)
    rivers: List[River] = field(default_factory=list)
    terrain_features: List[TerrainFeature] = field(default_factory=list)
    structures: List[Structure] = field(default_factory=list)
    regions: List[Region] = field(default_factory=list)
    spawns: List[Spawn] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def total_tiles(self) -> int:
        return self.world.tile_count() if self.world is not None else 0

    @property
    def total_zones(self) -> int:
        return len(self.zones_placed)

    @property
    def total_structures(self) -> int:
        return len(self.structures)

    @property
    def total_spawns(self) -> int:
        return len(self.spawns)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_tiles": self.total_tiles,
            "total_zones": self.total_zones,
            "total_structures": self.total_structures,
            "total_spawns": self.total_spawns,
            "zones": self.zones_placed,
            "roads": [s.to_dict() for s in self.roads],
            "rivers": [r.to_dict() for r in self.rivers],
            "terrain_features": [t.to_dict() for t in self.terrain_features],
            "structures": [s.to_dict() for s in self.structures],
            "regions": [r.to_dict() for r in self.regions],
            "metadata": dict(self.metadata),
        }


# =============================================================================
# Helpers
# =============================================================================

def _plan_attr(plan: Any, *names: str, default: Any = None) -> Any:
    """Get an attribute from a plan that may be a dict or an object."""
    if plan is None:
        return default
    if isinstance(plan, dict):
        for n in names:
            if n in plan:
                return plan[n]
        return default
    for n in names:
        v = getattr(plan, n, None)
        if v is not None:
            return v
    return default


def _layout_zones(plan: Any) -> List[Dict[str, Any]]:
    """
    Extract placed zones from a WorldPlan / WorldLayout.

    Accepts plans that have either:
        - .layout.zones: list of PlacedZone-like objects
        - .placed_zones: list (alternate name)
    """
    layout = _plan_attr(plan, "layout")
    if layout is None:
        return []
    raw_zones = _plan_attr(layout, "zones", "placed_zones", default=[]) or []
    out: List[Dict[str, Any]] = []
    for z in raw_zones:
        if isinstance(z, dict):
            out.append(dict(z))
        else:
            out.append({
                "x": getattr(z, "x", 0),
                "y": getattr(z, "y", 0),
                "z": getattr(z, "z", 7),
                "width": getattr(z, "width", 40),
                "height": getattr(z, "height", 40),
                "name": getattr(z, "name", "zone"),
                "theme": getattr(z, "theme", "generic"),
                "zone_kind": getattr(z, "zone_kind", "hunt"),
                "level_min": getattr(z, "level_min", 1),
                "level_max": getattr(z, "level_max", 200),
                "band": getattr(z, "band", "medium"),
                "plan": getattr(z, "plan", None),
            })
    return out


def _plan_world_size(plan: Any) -> Tuple[int, int]:
    w = int(_plan_attr(plan, "world_width", default=200) or 200)
    h = int(_plan_attr(plan, "world_height", default=200) or 200)
    return max(1, w), max(1, h)


def _plan_z(plan: Any) -> int:
    layout = _plan_attr(plan, "layout")
    if layout is not None:
        zones = _plan_attr(layout, "zones", default=[]) or []
        for z in zones:
            zz = getattr(z, "z", None) if not isinstance(z, dict) else z.get("z")
            if zz is not None:
                return int(zz)
    return 7


def _plan_primary_theme(plan: Any) -> str:
    return str(_plan_attr(plan, "primary_theme", "theme", default="generic") or "generic")


def _plan_difficulty_progression(plan: Any) -> List[Dict[str, Any]]:
    items = _plan_attr(plan, "difficulty_progression", default=[]) or []
    out: List[Dict[str, Any]] = []
    for it in items:
        if isinstance(it, dict):
            out.append(dict(it))
        else:
            out.append({
                "zone_index": getattr(it, "zone_index", 0),
                "zone_kind": getattr(it, "zone_kind", "hunt"),
                "level_min": getattr(it, "level_min", 1),
                "level_max": getattr(it, "level_max", 100),
                "band": getattr(it, "band", "medium"),
                "spawn_density": getattr(it, "spawn_density", "medium"),
                "monster_pool": list(getattr(it, "monster_pool", []) or []),
            })
    return out


def _theme_assets_for_zone(plan: Any, theme_resolver: Any, zone: Dict[str, Any]) -> Any:
    """
    Resolve a ThemeAssets for a given zone by its theme name.
    """
    if theme_resolver is None:
        return None
    theme_name = zone.get("theme") or _plan_primary_theme(plan)
    try:
        return theme_resolver.resolve(str(theme_name))
    except Exception:
        return None


# =============================================================================
# ContinentGenerator
# =============================================================================

class ContinentGenerator:
    """
    Turns a WorldPlan into a fully populated WorldModel.

    Usage:
        architect = AIArchitect()
        plan = architect.plan("Generate Issavi city with 3 hunts level 300 and a boss")

        gen = ContinentGenerator(seed=42)
        world = gen.generate(plan)
        # world is a WorldModel with tiles, structures, regions, spawns
    """

    DEFAULT_DENSITY: Dict[str, int] = {
        "low": 4, "medium": 8, "high": 14, "extreme": 20,
    }

    def __init__(
        self,
        biome_generator: Optional[BiomeGenerator] = None,
        terrain_generator: Optional[TerrainGenerator] = None,
        road_generator: Optional[RoadGenerator] = None,
        river_generator: Optional[RiverGenerator] = None,
        blueprint_registry: Optional[Any] = None,
        theme_resolver: Optional[Any] = None,
        asset_registry: Optional[Any] = None,
        seed: Optional[int] = None,
    ) -> None:
        self._seed = int(seed) if seed is not None else random.randint(0, 999999)
        self._biome = biome_generator or BiomeGenerator(seed=self._seed)
        self._terrain = terrain_generator or TerrainGenerator(seed=self._seed ^ 0x1234)
        self._roads = road_generator or RoadGenerator(seed=self._seed ^ 0x5678)
        self._rivers = river_generator or RiverGenerator(seed=self._seed ^ 0x9ABC)
        self._blueprints = blueprint_registry
        self._theme_resolver = theme_resolver
        self._assets = asset_registry

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, plan: Any) -> WorldModel:
        """
        Run the full continent pipeline on a WorldPlan and return a
        populated WorldModel.
        """
        world = WorldModel()
        result = ContinentResult(world=world, metadata={
            "seed": self._seed,
            "prompt": _plan_attr(plan, "prompt", default=""),
            "primary_theme": _plan_primary_theme(plan),
        })

        world_width, world_height = _plan_world_size(plan)
        z = _plan_z(plan)
        primary_theme = _plan_primary_theme(plan)

        # 1. Resolve all themes used by the plan (one ThemeAssets each)
        themes = self._resolve_all_themes(plan, primary_theme)

        # 2. Continental biome pass
        self._step_continental_biome(world, world_width, world_height, z, primary_theme)

        # 3. Get placed zones
        zones = _layout_zones(plan)
        result.zones_placed = zones

        # 4. Per-zone biome refinement
        self._step_per_zone_biome(world, zones, z, themes)

        # 5. Terrain features around zones
        self._step_terrain_features(world, world_width, world_height, z, primary_theme,
                                    zones, result)

        # 6. Rivers
        self._step_rivers(world, world_width, world_height, z, primary_theme, result)

        # 7. Zone content (cities, dungeons, hunts, bosses, quests)
        self._step_zone_content(world, plan, zones, z, themes, result)

        # 8. Roads connecting zones + city grids
        self._step_roads(world, zones, z, primary_theme, result)

        # 9. Regions
        self._step_regions(plan, zones, result)

        # 10. Final metadata
        result.metadata.update({
            "world_size": [world_width, world_height],
            "z": z,
            "themes_resolved": list(themes.keys()),
        })
        return world

    # ------------------------------------------------------------------
    # Step 1: Continental biome
    # ------------------------------------------------------------------

    def _step_continental_biome(
        self,
        world: WorldModel,
        width: int, height: int, z: int,
        theme: str,
    ) -> int:
        return self._biome.generate(
            world, 0, 0, width - 1, height - 1, z, theme,
            water_chance=0.04,
        )

    # ------------------------------------------------------------------
    # Step 2: Per-zone biome refinement
    # ------------------------------------------------------------------

    def _step_per_zone_biome(
        self,
        world: WorldModel,
        zones: List[Dict[str, Any]],
        z: int,
        themes: Dict[str, Any],
    ) -> None:
        for zone in zones:
            theme_name = zone.get("theme") or "generic"
            theme = themes.get(theme_name) or theme_name
            primary = pick_primary_tag(theme)
            self._biome.generate(
                world,
                zone["x"], zone["y"],
                zone["x"] + zone["width"] - 1,
                zone["y"] + zone["height"] - 1,
                z, theme,
                primary_tag=primary,
                water_chance=0.0,
                overwrite=True,
            )

    # ------------------------------------------------------------------
    # Step 3: Terrain features
    # ------------------------------------------------------------------

    def _step_terrain_features(
        self,
        world: WorldModel,
        width: int, height: int, z: int,
        theme: str,
        zones: List[Dict[str, Any]],
        result: ContinentResult,
    ) -> None:
        mountains = self._terrain.generate_mountains(
            world, 0, 0, width - 1, height - 1, z, theme,
            threshold=0.80,
        )
        result.terrain_features.append(mountains)
        hills = self._terrain.generate_hills(
            world, 0, 0, width - 1, height - 1, z, theme,
        )
        result.terrain_features.append(hills)
        water = self._terrain.generate_water_bodies(
            world, 0, 0, width - 1, height - 1, z, theme,
        )
        result.terrain_features.extend(water)

    # ------------------------------------------------------------------
    # Step 4: Rivers
    # ------------------------------------------------------------------

    def _step_rivers(
        self,
        world: WorldModel,
        width: int, height: int, z: int,
        theme: str,
        result: ContinentResult,
    ) -> None:
        # Build rivers from a few random sources to the world edge
        sources: List[Tuple[int, int]] = []
        sinks: List[Tuple[int, int]] = []
        for _ in range(3):
            sx = self._biome._rng.randint(0, max(0, width - 1))
            sy = self._biome._rng.randint(0, max(0, height - 1))
            # Sink: opposite edge
            edge = self._biome._rng.choice(["top", "bottom", "left", "right"])
            if edge == "top":
                sinks.append((self._biome._rng.randint(0, max(0, width - 1)), 0))
            elif edge == "bottom":
                sinks.append((self._biome._rng.randint(0, max(0, width - 1)), height - 1))
            elif edge == "left":
                sinks.append((0, self._biome._rng.randint(0, max(0, height - 1))))
            else:
                sinks.append((width - 1, self._biome._rng.randint(0, max(0, height - 1))))
            sources.append((sx, sy))
        rivers = self._rivers.generate_rivers(
            world, sources, sinks, z, theme,
            width=2, meander=0.35, add_banks=True,
        )
        result.rivers.extend(rivers)

    # ------------------------------------------------------------------
    # Step 5: Zone content
    # ------------------------------------------------------------------

    def _step_zone_content(
        self,
        world: WorldModel,
        plan: Any,
        zones: List[Dict[str, Any]],
        z: int,
        themes: Dict[str, Any],
        result: ContinentResult,
    ) -> None:
        diff = _plan_difficulty_progression(plan)
        diff_by_index: Dict[int, Dict[str, Any]] = {
            int(d.get("zone_index", i)): d
            for i, d in enumerate(diff)
        }
        from core.world.tile import Tile

        for idx, zone in enumerate(zones):
            zone_kind = zone.get("zone_kind") or zone.get("kind") or "hunt"
            theme_name = zone.get("theme") or "generic"
            theme = themes.get(theme_name) or theme_name
            d = diff_by_index.get(idx, {
                "level_min": zone.get("level_min", 1),
                "level_max": zone.get("level_max", 100),
                "band": zone.get("band", "medium"),
                "spawn_density": zone.get("spawn_density", "medium"),
                "monster_pool": [],
            })
            pool = list(d.get("monster_pool") or [])

            x, y = zone["x"], zone["y"]
            w, h = zone["width"], zone["height"]

            # Place structure and (optionally) decorations
            self._place_zone_structure(
                world, zone, zone_kind, x, y, w, h, z, theme, result,
            )

            # Place spawns
            self._place_zone_spawns(
                world, zone, zone_kind, x, y, w, h, z, theme,
                pool=pool, density=d.get("spawn_density", "medium"),
                result=result,
            )

    def _place_zone_structure(
        self,
        world: WorldModel,
        zone: Dict[str, Any],
        kind: str,
        x: int, y: int, w: int, h: int,
        z: int, theme: Any,
        result: ContinentResult,
    ) -> None:
        """Place a single structure record + its perimeter walls/temple."""
        from core.world.tile import Tile
        from core.world.item import Item

        name = zone.get("name", "zone")
        category = self._category_for_kind(kind)

        # Per-kind structure sizes
        if kind == "city":
            struct_w, struct_h = max(8, min(w, 20)), max(8, min(h, 20))
        elif kind == "dungeon":
            struct_w, struct_h = max(6, min(w, 14)), max(6, min(h, 14))
        elif kind == "boss":
            struct_w, struct_h = max(6, min(w, 10)), max(6, min(h, 10))
        elif kind == "quest":
            struct_w, struct_h = max(4, min(w, 8)), max(4, min(h, 8))
        else:  # hunt
            struct_w, struct_h = max(0, w), max(0, h)

        # If we have a non-zero structure, build walls and an entry
        if struct_w > 0 and struct_h > 0:
            cx = x + (w - struct_w) // 2
            cy = y + (h - struct_h) // 2
            # Use theme walls
            wall_ids = list(getattr(theme, "walls", []) or [])
            wall_id = wall_ids[0] if wall_ids else 1498
            for ix in range(cx, cx + struct_w):
                world.set_tile(Tile(x=ix, y=cy, z=z, ground=wall_id,
                                    zone=f"{category}:wall"))
                world.set_tile(Tile(x=ix, y=cy + struct_h - 1, z=z, ground=wall_id,
                                    zone=f"{category}:wall"))
            for iy in range(cy, cy + struct_h):
                world.set_tile(Tile(x=cx, y=iy, z=z, ground=wall_id,
                                    zone=f"{category}:wall"))
                world.set_tile(Tile(x=cx + struct_w - 1, y=iy, z=z, ground=wall_id,
                                    zone=f"{category}:wall"))

            # Drop a "feature" item at the center (altar, chest, fountain, ...)
            mid_x = cx + struct_w // 2
            mid_y = cy + struct_h // 2
            deco_ids = list(getattr(theme, "decorations", []) or [])
            if deco_ids and kind in ("city", "dungeon", "boss", "quest"):
                feat_id = deco_ids[0]
                tile = world.get_tile(mid_x, mid_y, z) or Tile(x=mid_x, y=mid_y, z=z)
                tile.items.append(Item(itemid=feat_id))
                world.set_tile(tile)

        # Register the structure in the world
        structure = Structure(
            name=str(name),
            category=category,
            x=x, y=y, z=z,
            width=w, height=h,
            tile_count=(struct_w * struct_h if struct_w and struct_h else w * h),
            tags=[kind, str(zone.get("theme", "generic"))],
        )
        world.add_structure(structure)
        result.structures.append(structure)

    def _place_zone_spawns(
        self,
        world: WorldModel,
        zone: Dict[str, Any],
        kind: str,
        x: int, y: int, w: int, h: int,
        z: int, theme: Any,
        pool: List[str],
        density: str,
        result: ContinentResult,
    ) -> None:
        """Place monster spawns inside a zone based on its density and pool."""
        from core.world.spawn import Spawn
        from core.world.tile import Tile

        # Cities, dungeons and quest rooms have NO field spawns
        if kind in ("city", "dungeon", "quest"):
            return

        if not pool:
            pool = list(getattr(theme, "monsters", []) or [])

        if kind == "boss":
            # Single boss spawn at the center
            if pool:
                boss_name = pool[0]
                cx = x + w // 2
                cy = y + h // 2
                tile = world.get_tile(cx, cy, z) or Tile(x=cx, y=cy, z=z)
                tile.spawn = Spawn(monster=boss_name, respawn=120, radius=8)
                tile.zone = f"spawn:boss:{boss_name}"
                world.set_tile(tile)
                result.spawns.append(tile.spawn)
            return

        # Hunt spawns
        n_spawns = self.DEFAULT_DENSITY.get(density, 8)
        n_spawns = max(2, min(n_spawns, (w * h) // 4))
        rng = random.Random(self._seed ^ (x * 1009 + y * 1013))
        if not pool:
            return
        for _ in range(n_spawns):
            sx = rng.randint(x, x + w - 1)
            sy = rng.randint(y, y + h - 1)
            monster = pool[rng.randint(0, len(pool) - 1)]
            tile = world.get_tile(sx, sy, z) or Tile(x=sx, y=sy, z=z)
            tile.spawn = Spawn(monster=monster, respawn=60, radius=5)
            tile.zone = f"spawn:hunt:{monster}"
            world.set_tile(tile)
            result.spawns.append(tile.spawn)

    @staticmethod
    def _category_for_kind(kind: str) -> str:
        if kind == "city":
            return "city"
        if kind == "dungeon":
            return "dungeon"
        if kind == "boss":
            return "boss_room"
        if kind == "quest":
            return "quest_room"
        return "hunt_zone"

    # ------------------------------------------------------------------
    # Step 6: Roads
    # ------------------------------------------------------------------

    def _step_roads(
        self,
        world: WorldModel,
        zones: List[Dict[str, Any]],
        z: int,
        theme: str,
        result: ContinentResult,
    ) -> None:
        if len(zones) < 2:
            # Even with one zone, place a city street grid if it's a city
            for zone in zones:
                if zone.get("zone_kind") == "city":
                    grid = self._roads.build_city_grid(
                        world, zone["x"], zone["y"],
                        zone["width"], zone["height"], z, theme,
                        step=4, margin=2,
                    )
                    result.roads.extend(grid.segments)
            return

        # Connect every zone to the next
        net = self._roads.connect_zones(world, zones, theme, width=1, kind="road")
        result.roads.extend(net.segments)
        for bridge_pt in net.bridges:
            result.metadata.setdefault("bridges", []).append(bridge_pt.to_dict())

        # City grids
        for zone in zones:
            if zone.get("zone_kind") == "city":
                grid = self._roads.build_city_grid(
                    world, zone["x"], zone["y"],
                    zone["width"], zone["height"], z, theme,
                    step=4, margin=2,
                )
                result.roads.extend(grid.segments)

    # ------------------------------------------------------------------
    # Step 7: Regions
    # ------------------------------------------------------------------

    def _step_regions(
        self,
        plan: Any,
        zones: List[Dict[str, Any]],
        result: ContinentResult,
    ) -> None:
        world = result.world
        for i, zone in enumerate(zones):
            lo = int(zone.get("level_min", 1))
            hi = int(zone.get("level_max", 200))
            name = f"{zone.get('zone_kind', 'zone')}_{i + 1}_{zone.get('name', '')}".strip("_")
            theme_name = zone.get("theme") or "generic"
            region = Region(
                name=name,
                theme=str(theme_name),
                min_level=lo, max_level=hi,
                tags=[str(zone.get("zone_kind", "hunt")), str(theme_name)],
            )
            world.add_region(region)
            result.regions.append(region)

    # ------------------------------------------------------------------
    # Theme resolution
    # ------------------------------------------------------------------

    def _resolve_all_themes(self, plan: Any, primary_theme: str) -> Dict[str, Any]:
        themes_in_plan = _plan_attr(plan, "themes", default=[]) or [primary_theme]
        result: Dict[str, Any] = {}
        for name in themes_in_plan:
            key = str(name).lower()
            if self._theme_resolver is not None:
                try:
                    result[key] = self._theme_resolver.resolve(key)
                except Exception:
                    result[key] = key
            else:
                result[key] = key
        # Also resolve any zone-level theme names
        for zone in _layout_zones(plan):
            tn = zone.get("theme")
            if tn and tn not in result:
                if self._theme_resolver is not None:
                    try:
                        result[tn] = self._theme_resolver.resolve(tn)
                    except Exception:
                        result[tn] = tn
                else:
                    result[tn] = tn
        return result


# =============================================================================
# Module-level helpers
# =============================================================================

def generate_continent(plan: Any, seed: Optional[int] = None) -> WorldModel:
    """
    One-shot helper: turn a WorldPlan into a fully populated WorldModel.

    Usage:
        from core.architect import AIArchitect
        from core.procedural import generate_continent

        plan = AIArchitect().plan("Generate Issavi city with 3 hunts and a boss")
        world = generate_continent(plan, seed=42)
    """
    gen = ContinentGenerator(seed=seed)
    return gen.generate(plan)


def generate_from_prompt(
    prompt: str,
    seed: Optional[int] = None,
    world_width: int = 200,
    world_height: int = 200,
) -> WorldModel:
    """
    End-to-end helper: prompt -> plan -> WorldModel.

    Uses AIArchitect to build the plan and ContinentGenerator to build the
    world. Returns the WorldModel only (the plan is discarded); for
    both, use AIArchitect + ContinentGenerator directly.
    """
    from core.architect import AIArchitect
    architect = AIArchitect()
    plan = architect.plan(prompt, world_width=world_width, world_height=world_height)
    return generate_continent(plan, seed=seed)
