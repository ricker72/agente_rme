"""
MVP V0.1 — Lua Generator
Generates RME-compatible Lua scripts using ONLY valid OpenTibiaBR RME APIs:

  if not app.hasMap() then return end
  local map = app.map
  app.transaction(...)
  map:getOrCreateTile(x, y, z)
  tile.ground = itemId
  tile:addItem(itemId)
  tile:setSpawn(radius)
  tile:setCreature(monsterName, spawnTime, Direction.SOUTH)
  tile:borderize()

FORBIDDEN (never generated):
  Map.addItem, Map.addCreature, Map.addNpc, Map.setTile, Position, Game.createTile
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class LuaScript:
    code: str
    map_name: str
    tile_count: int = 0
    spawn_count: int = 0
    creature_count: int = 0
    border_count: int = 0
    items_count: int = 0


@dataclass
class _ResolvedInputs:
    """Result of normalising the various (world, hunt_area, spawn_plan) input shapes."""

    tiles: List[Dict[str, Any]]
    rooms: List[Dict[str, Any]]
    spawns: List[Dict[str, Any]]
    boss_spawn: Optional[Dict[str, Any]]
    width: int
    height: int
    base_x: int
    base_y: int
    base_z: int


class LuaGenerator:
    """
    Generates clean RME Lua scripts from a HuntArea and SpawnPlan.
    Uses ONLY the approved OpenTibiaBR RME API.

    Accepted call signatures (backwards compatible):

        gen.generate()                              # no input → empty script
        gen.generate(world)                         # WorldModel only — spawn
                                                     # plan is auto-generated
                                                     # from world.tiles[*].spawn
        gen.generate(world, spawn_plan)             # WorldModel + SpawnPlan
        gen.generate(hunt_area, spawn_plan)         # HuntArea + SpawnPlan
        gen.generate(hunt_area=..., spawn_plan=...) # keyword form
        gen.generate(spawn_plan)                    # SpawnPlan as first arg

    HITO 26.1B fix: when ``spawn_plan`` is ``None`` and a world-like
    object is provided, a :class:`SpawnPlan` is automatically built by
    :class:`core.spawn.spawn_generator.SpawnGenerator.generate_for_world`
    so the original call ``gen.generate(world)`` no longer raises
    ``missing required argument: spawn_plan``.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        world: Any = None,
        spawn_plan: Any = None,
        *,
        map_name: str = "GeneratedMap",
        hunt_area: Any = None,
    ) -> LuaScript:
        """Generate the Lua script.

        Args:
            world: A WorldModel or HuntArea. Optional when ``hunt_area`` is
                provided as a keyword argument.
            spawn_plan: Optional SpawnPlan. If omitted (and a world-like
                object is provided), a spawn plan is auto-generated from
                the world using
                :class:`core.spawn.spawn_generator.SpawnGenerator`.
            map_name: Map name used in the script header.
            hunt_area: Optional HuntArea (used when ``world`` is the spawn
                plan or a non-area object).

        Returns:
            LuaScript with the generated code and statistics.
        """
        # If a spawn plan was passed as the first positional argument,
        # shift it into the spawn_plan slot.
        if (
            world is not None
            and spawn_plan is None
            and self._looks_like_spawn_plan(world)
        ):
            spawn_plan = world
            world = None

        # ----- Auto-generate spawn plan from the world -----
        # If the caller gave us a world (or a hunt area) but no explicit
        # spawn plan, derive one with SpawnGenerator. This is the fix
        # for the regression: LuaGenerator.generate() missing required
        # argument: spawn_plan. The auto-generation is silently skipped
        # if the world carries no spawn information.
        if (
            spawn_plan is None
            and world is not None
            and not self._looks_like_spawn_plan(world)
        ):
            try:
                from core.spawn.spawn_generator import SpawnGenerator as _SG

                spawn_plan = _SG().generate_for_world(world)
            except Exception:
                spawn_plan = None

        resolved = self._resolve_inputs(
            world=world,
            hunt_area=hunt_area,
            spawn_plan=spawn_plan,
        )

        return self._build(resolved, map_name=map_name)

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _looks_like_spawn_plan(obj: Any) -> bool:
        if obj is None:
            return False
        if isinstance(obj, dict):
            return "spawns" in obj
        return hasattr(obj, "spawns") and (
            hasattr(obj, "boss_spawn") or hasattr(obj, "boss")
        )

    def _resolve_inputs(
        self,
        world: Any,
        hunt_area: Any,
        spawn_plan: Any,
    ) -> _ResolvedInputs:
        """Normalise any of (WorldModel, HuntArea, dict, None) into a _ResolvedInputs."""
        area = hunt_area or world

        tiles: List[Dict[str, Any]] = []
        rooms: List[Dict[str, Any]] = []
        base_x, base_y, base_z = 1000, 1000, 7

        if area is not None:
            tiles = list(self._extract_tiles(area))
            rooms = list(self._extract_rooms(area))
            base_x = int(self._get_attr(area, "base_x", base_x))
            base_y = int(self._get_attr(area, "base_y", base_y))
            base_z = int(self._get_attr(area, "base_z", base_z))

        if not tiles and world is not None and world is not area:
            # WorldModel-style fallback: pull from world.tiles
            tiles = list(self._extract_tiles(world))
            base_x = int(self._get_attr(world, "base_x", base_x))
            base_y = int(self._get_attr(world, "base_y", base_y))
            base_z = int(self._get_attr(world, "base_z", base_z))

        # Compute width/height
        if tiles:
            xs = [int(self._get_attr(t, "x", base_x)) for t in tiles]
            ys = [int(self._get_attr(t, "y", base_y)) for t in tiles]
            width = max(xs) - min(xs) + 1 if xs else 1
            height = max(ys) - min(ys) + 1 if ys else 1
        else:
            width, height = 1, 1

        # Resolve spawns from plan or fallback
        spawns_list: List[Dict[str, Any]] = []
        boss_spawn: Optional[Dict[str, Any]] = None
        if spawn_plan is not None:
            for entry in self._get_attr(spawn_plan, "spawns", []) or []:
                spawns_list.append(self._entry_to_dict(entry, base_z))
            boss_spawn_raw = self._get_attr(spawn_plan, "boss_spawn", None)
            if boss_spawn_raw is not None:
                boss_spawn = self._entry_to_dict(boss_spawn_raw, base_z)

        return _ResolvedInputs(
            tiles=tiles,
            rooms=rooms,
            spawns=spawns_list,
            boss_spawn=boss_spawn,
            width=width,
            height=height,
            base_x=base_x,
            base_y=base_y,
            base_z=base_z,
        )

    @staticmethod
    def _get_attr(obj: Any, name: str, default: Any = None) -> Any:
        """Read an attribute that may live on a dict or a dataclass/object."""
        if obj is None:
            return default
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def _extract_tiles(self, source: Any) -> List[Dict[str, Any]]:
        """Pull a list of tile dicts out of any reasonable source shape."""
        raw = self._get_attr(source, "tiles", [])
        out: List[Dict[str, Any]] = []
        if isinstance(raw, dict):
            for k, v in raw.items():
                if isinstance(v, dict):
                    out.append(v)
                elif hasattr(v, "to_dict"):
                    out.append(v.to_dict())
                else:
                    out.append(
                        {
                            "x": self._get_attr(v, "x", 0),
                            "y": self._get_attr(v, "y", 0),
                            "z": self._get_attr(v, "z", 7),
                            "ground": self._get_attr(v, "ground", 106),
                            "wall_id": self._get_attr(v, "wall_id", 0),
                            "decoration_id": self._get_attr(v, "decoration_id", 0),
                            "borderized": self._get_attr(v, "borderized", False),
                            "tile_type": self._get_attr(v, "tile_type", None),
                            "items": self._get_attr(v, "items", []) or [],
                        }
                    )
        elif isinstance(raw, list):
            for v in raw:
                if isinstance(v, dict):
                    out.append(v)
                elif hasattr(v, "to_dict"):
                    out.append(v.to_dict())
        return out

    def _extract_rooms(self, source: Any) -> List[Dict[str, Any]]:
        raw = self._get_attr(source, "rooms", []) or []
        out: List[Dict[str, Any]] = []
        if isinstance(raw, list):
            for r in raw:
                if isinstance(r, dict):
                    out.append(r)
                else:
                    out.append(
                        {
                            "x": self._get_attr(r, "x", 0),
                            "y": self._get_attr(r, "y", 0),
                            "width": self._get_attr(r, "width", 0),
                            "height": self._get_attr(r, "height", 0),
                            "room_type": self._get_attr(r, "room_type", "spawn"),
                        }
                    )
        return out

    def _entry_to_dict(self, entry: Any, base_z: int) -> Dict[str, Any]:
        return {
            "x": int(self._get_attr(entry, "x", 0)),
            "y": int(self._get_attr(entry, "y", 0)),
            "z": int(self._get_attr(entry, "z", base_z)),
            "monster_name": str(self._get_attr(entry, "monster_name", "")),
            "interval": int(self._get_attr(entry, "interval", 60) or 60),
        }

    # ------------------------------------------------------------------
    # Build script
    # ------------------------------------------------------------------

    def _build(self, r: _ResolvedInputs, *, map_name: str) -> LuaScript:
        lines: List[str] = []
        tile_count = 0
        spawn_count = 0
        creature_count = 0
        border_count = 0
        items_count = 0

        lines.append(f"-- OpenTibiaBR RME Map - {map_name}")
        lines.append("-- Generated by RME Map AI Agent MVP V0.1")
        lines.append(
            f"-- Tiles: {len(r.tiles)} | Rooms: {len(r.rooms)} | Spawns: {len(r.spawns)}"
        )
        lines.append("")

        # Guard
        lines.append("if not app.hasMap() then")
        lines.append("    return")
        lines.append("end")
        lines.append("")
        lines.append("local map = app.map")
        lines.append("")

        lines.append(f'app.transaction("{map_name}", function()')
        lines.append(f"  -- Map dimensions: {r.width}x{r.height}")
        lines.append(f"  -- Base position: ({r.base_x}, {r.base_y}, {r.base_z})")
        lines.append("")

        # Tiles
        for tile in r.tiles:
            tx = int(self._get_attr(tile, "x", 0))
            ty = int(self._get_attr(tile, "y", 0))
            tz = int(self._get_attr(tile, "z", r.base_z))
            lines.append(f"  -- Tile ({tx}, {ty}, {tz})")
            lines.append(f"  local t = map:getOrCreateTile({tx}, {ty}, {tz})")
            tile_count += 1

            ground_id = int(
                self._get_attr(tile, "ground", self._get_attr(tile, "ground_id", 0))
                or 0
            )
            if ground_id > 0:
                lines.append(f"  t.ground = {ground_id}")

            wall_id = int(self._get_attr(tile, "wall_id", 0) or 0)
            tile_type = self._get_attr(tile, "tile_type", None)
            if wall_id > 0 and tile_type and str(tile_type).lower() == "wall":
                lines.append(f"  t:addItem({wall_id})")

            decoration_id = int(self._get_attr(tile, "decoration_id", 0) or 0)
            if decoration_id > 0:
                lines.append(f"  t:addItem({decoration_id})")

            for item in self._get_attr(tile, "items", []) or []:
                item_id = int(self._get_attr(item, "id", item) or 0)
                if item_id > 0:
                    lines.append(f"  t:addItem({item_id})")
                    items_count += 1

            if self._get_attr(tile, "borderized", False):
                lines.append("  t:borderize()")
                border_count += 1

            lines.append("")

        # Spawns
        for spawn in r.spawns:
            sx = int(spawn.get("x", 0))
            sy = int(spawn.get("y", 0))
            sz = int(spawn.get("z", r.base_z))
            spawn_interval = int(spawn.get("interval", 60) or 60)
            monster_name = str(spawn.get("monster_name", ""))

            lines.append(f"  -- Spawn: {monster_name} at ({sx}, {sy}, {sz})")
            lines.append(f"  local s = map:getOrCreateTile({sx}, {sy}, {sz})")
            lines.append(f"  s:setSpawn({spawn_interval})")
            lines.append(
                f'  s:setCreature("{monster_name}", {spawn_interval}, Direction.SOUTH)'
            )
            spawn_count += 1
            lines.append("")

        # Boss
        if r.boss_spawn:
            b = r.boss_spawn
            bx = int(b.get("x", 0))
            by = int(b.get("y", 0))
            bz = int(b.get("z", r.base_z))
            b_interval = int(b.get("interval", 600) or 600)
            b_name = str(b.get("monster_name", "Boss"))

            lines.append(f"  -- Boss: {b_name} at ({bx}, {by}, {bz})")
            lines.append(f"  local b = map:getOrCreateTile({bx}, {by}, {bz})")
            lines.append(f"  b:setSpawn({b_interval})")
            lines.append(f'  b:setCreature("{b_name}", {b_interval}, Direction.SOUTH)')
            creature_count += 1
            lines.append("")

        lines.append("end)")
        lines.append("")

        code = "\n".join(lines)
        return LuaScript(
            code=code,
            map_name=map_name,
            tile_count=tile_count,
            spawn_count=spawn_count,
            creature_count=creature_count,
            border_count=border_count,
            items_count=items_count,
        )
