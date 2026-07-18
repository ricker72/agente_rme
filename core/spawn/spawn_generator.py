"""
MVP V0.1 — Spawn Generator
Automatically assigns monsters to spawn areas based on:
- Theme monster pools
- Level range difficulty
- Room type (spawn, boss, corridor)

Two public entry points are supported:

1. ``generate(rooms, theme_monsters, level_range, base_z)`` — original
   room-based API that returns a :class:`SpawnPlan` populated from a
   list of room-like objects.

2. ``generate_for_world(world)`` — convenience wrapper that derives a
   :class:`SpawnPlan` directly from a populated :class:`WorldModel`,
   reading monster/respawn data that the map generators already wrote
   onto individual ``Tile.spawn`` slots. This is the function the
   :class:`core.lua.lua_generator.LuaGenerator` calls when the caller
   passes a world but no explicit spawn plan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple


@dataclass
class SpawnEntry:
    x: int
    y: int
    z: int
    monster_name: str
    interval: int = 60
    is_boss: bool = False


@dataclass
class SpawnPlan:
    spawns: List[SpawnEntry] = field(default_factory=list)
    boss_spawn: Optional[SpawnEntry] = None


class SpawnGenerator:
    """
    Generates monster spawn entries for a HuntArea.

    Difficulty-based monster assignment:
    - Easy (level < 200): 1-2 monsters per spawn room
    - Medium (200-400): 2-3 monsters per spawn room
    - Hard (400-600): 3-4 monsters per spawn room
    - Extreme (600+): 4-5 monsters per spawn room + stronger variants
    """

    # Monster difficulty tiers
    MONSTER_TIERS = {
        "easy": [
            "Crypt Warden",
            "Skeleton",
            "Demon Skeleton",
            "Priestess",
            "Death Priest",
        ],
        "medium": [
            "Frazzlemaw",
            "Sphinx",
            "Cloak Of Terror",
            "Crypt Warden",
            "Vexclaw",
        ],
        "hard": [
            "Frazzlemaw",
            "Guzzlemaw",
            "Cloak Of Terror",
            "Sphinx",
            "Vexclaw",
            "Shrieker",
        ],
        "extreme": [
            "Guzzlemaw",
            "Cloak Of Terror",
            "Vexclaw",
            "Shrieker",
            "Frazzlemaw",
        ],
    }

    # Anything with respawn >= BOSS_RESPAWN_THRESHOLD is treated as a boss
    BOSS_RESPAWN_THRESHOLD = 120

    def generate(
        self,
        rooms: List,  # List[Room]
        theme_monsters: List[str],
        level_range: Tuple[int, int],
        base_z: int = 7,
    ) -> SpawnPlan:
        plan = SpawnPlan()

        avg_level = (level_range[0] + level_range[1]) / 2
        tier = self._difficulty_tier(avg_level)

        # Get available monsters: theme monsters filtered by tier
        available = [m for m in theme_monsters if m in self.MONSTER_TIERS.get(tier, [])]
        if not available:
            available = self.MONSTER_TIERS.get(tier, self.MONSTER_TIERS["medium"])

        for room in rooms:
            if room.room_type == "boss":
                # Boss spawn in center of room
                bx = room.x + room.width // 2
                by = room.y + room.height // 2
                boss_name = self._pick_boss(available, avg_level)
                entry = SpawnEntry(
                    x=bx,
                    y=by,
                    z=base_z,
                    monster_name=boss_name,
                    interval=120,
                    is_boss=True,
                )
                plan.spawns.append(entry)
                plan.boss_spawn = entry
            elif room.room_type == "spawn":
                # Regular spawns at room corners
                import random

                rng = random.Random(hash(f"{room.x}_{room.y}_spawn") % (2**31))
                num_spawns = self._num_spawns(tier, avg_level)

                for _ in range(num_spawns):
                    dx = rng.randint(1, max(room.width - 2, 1))
                    dy = rng.randint(1, max(room.height - 2, 1))
                    monster = rng.choice(available)
                    plan.spawns.append(
                        SpawnEntry(
                            x=room.x + dx,
                            y=room.y + dy,
                            z=base_z,
                            monster_name=monster,
                            interval=60,
                        )
                    )

        return plan

    # ------------------------------------------------------------------
    # WorldModel-based auto-generation (used by LuaGenerator fallback)
    # ------------------------------------------------------------------

    def generate_for_world(self, world: Any) -> SpawnPlan:
        """Build a :class:`SpawnPlan` directly from a populated ``WorldModel``.

        This is the convenience entry point used by
        :class:`core.lua.lua_generator.LuaGenerator` whenever a caller
        passes a world but no explicit spawn plan. It walks every tile
        in the world, picks up any ``Tile.spawn`` metadata already
        written by the map generators, and assembles it into a
        :class:`SpawnPlan`. Tiles whose spawn has a respawn time at or
        above :data:`BOSS_RESPAWN_THRESHOLD` are classified as boss
        spawns (or the first such tile becomes the canonical boss).

        The method is intentionally tolerant:

        * ``None`` → returns an empty plan.
        * A bare dict with a ``"spawns"`` key → coerced into a plan.
        * A :class:`WorldModel` (with ``.tiles``) → walked normally.
        * A "designer" :class:`WorldModel` (with ``.zones`` whose zones
          carry hunts / bosses / spawns) → walked via the designer
          path.
        """
        if world is None:
            return SpawnPlan()

        # Designer-style world: agente_rme.core.designer.world_model.WorldModel
        zones = getattr(world, "zones", None)
        if zones:
            return self._generate_from_designer_world(world, zones)

        tiles = getattr(world, "tiles", None)
        if tiles is not None:
            return self._generate_from_tiles(tiles)

        # Dict-style world
        if isinstance(world, dict):
            return self._generate_from_dict(world)

        # Fallback: best effort
        return SpawnPlan()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _generate_from_tiles(self, tiles: Any) -> SpawnPlan:
        """Walk a ``{key: Tile}`` mapping and build a spawn plan."""
        plan = SpawnPlan()
        boss_candidate: Optional[SpawnEntry] = None

        # tiles may be a dict (key->Tile) or an iterable of Tiles
        iterable: Iterable[Any]
        if isinstance(tiles, dict):
            iterable = tiles.values()
        else:
            iterable = iter(tiles)

        for tile in iterable:
            spawn = getattr(tile, "spawn", None)
            if spawn is None:
                continue

            monster = (
                getattr(spawn, "monster", None)
                or getattr(spawn, "monster_name", None)
                or (spawn.get("monster") if isinstance(spawn, dict) else None)
                or (spawn.get("monster_name") if isinstance(spawn, dict) else None)
                or "Unknown"
            )
            respawn = (
                getattr(spawn, "respawn", None)
                or getattr(spawn, "interval", None)
                or (spawn.get("respawn") if isinstance(spawn, dict) else None)
                or (spawn.get("interval") if isinstance(spawn, dict) else None)
                or 60
            )
            is_boss_flag = getattr(spawn, "is_boss", None)
            if is_boss_flag is None and isinstance(spawn, dict):
                is_boss_flag = spawn.get("is_boss", False)

            is_boss = bool(is_boss_flag) or int(respawn) >= self.BOSS_RESPAWN_THRESHOLD

            entry = SpawnEntry(
                x=int(getattr(tile, "x", 0)),
                y=int(getattr(tile, "y", 0)),
                z=int(getattr(tile, "z", 7)),
                monster_name=str(monster),
                interval=int(respawn) or 60,
                is_boss=is_boss,
            )

            if is_boss and boss_candidate is None:
                boss_candidate = entry
                plan.boss_spawn = entry
            else:
                plan.spawns.append(entry)

        return plan

    def _generate_from_designer_world(self, world: Any, zones: List[Any]) -> SpawnPlan:
        """Build a plan from a designer-style world (zones/hunts/bosses)."""
        plan = SpawnPlan()
        boss_candidate: Optional[SpawnEntry] = None
        base_z = 7

        try:
            base_z = int(getattr(world.goal, "min_level", 0) and 7 or 7)
        except Exception:
            base_z = 7

        for zone in zones:
            int(getattr(zone, "min_level", 0) and 7 or 7)

            # Hunt areas contribute regular spawns
            for hunt in getattr(zone, "hunts", []) or []:
                center = getattr(hunt, "center", None)
                if center is None:
                    continue
                cx = int(getattr(center, "x", 0))
                cy = int(getattr(center, "y", 0))
                for spawn in getattr(hunt, "spawns", []) or []:
                    monster = (
                        getattr(spawn, "monster_name", None)
                        or (
                            spawn.get("monster_name")
                            if isinstance(spawn, dict)
                            else None
                        )
                        or "Unknown"
                    )
                    schedule = (
                        getattr(spawn, "schedule", None)
                        or (spawn.get("schedule") if isinstance(spawn, dict) else None)
                        or "default"
                    )
                    is_boss = str(schedule).lower() in ("raid", "boss", "event")
                    interval = 600 if is_boss else 60
                    entry = SpawnEntry(
                        x=cx,
                        y=cy,
                        z=base_z,
                        monster_name=str(monster),
                        interval=interval,
                        is_boss=is_boss,
                    )
                    if is_boss and boss_candidate is None:
                        boss_candidate = entry
                        plan.boss_spawn = entry
                    else:
                        plan.spawns.append(entry)

            # Boss areas contribute a boss spawn (priority over hunts)
            for boss_area in getattr(zone, "bosses", []) or []:
                center = getattr(boss_area, "center", None)
                if center is None:
                    continue
                cx = int(getattr(center, "x", 0))
                cy = int(getattr(center, "y", 0))
                b_name = str(getattr(boss_area, "boss_name", "Boss"))
                entry = SpawnEntry(
                    x=cx,
                    y=cy,
                    z=base_z,
                    monster_name=b_name,
                    interval=600,
                    is_boss=True,
                )
                plan.boss_spawn = entry
                boss_candidate = entry
                # also list in spawns so it gets emitted
                plan.spawns.append(entry)

        return plan

    def _generate_from_dict(self, world: Dict[str, Any]) -> SpawnPlan:
        """Coerce a plain dict (with a 'spawns' or 'tiles' key) into a plan."""
        plan = SpawnPlan()

        has_spawns_key = "spawns" in world and isinstance(world["spawns"], list)
        has_tiles_key = "tiles" in world and isinstance(world["tiles"], list)

        if has_spawns_key:
            for entry in world["spawns"]:
                if not isinstance(entry, dict):
                    continue
                is_boss = bool(entry.get("is_boss", False))
                interval = int(entry.get("interval", 600 if is_boss else 60) or 60)
                if not is_boss and interval >= self.BOSS_RESPAWN_THRESHOLD:
                    is_boss = True
                se = SpawnEntry(
                    x=int(entry.get("x", 0)),
                    y=int(entry.get("y", 0)),
                    z=int(entry.get("z", 7)),
                    monster_name=str(
                        entry.get("monster_name", entry.get("monster", "Unknown"))
                    ),
                    interval=interval,
                    is_boss=is_boss,
                )
                if is_boss and plan.boss_spawn is None:
                    plan.boss_spawn = se
                plan.spawns.append(se)
        elif has_tiles_key:
            return self._generate_from_tiles(world["tiles"])

        # Always honour an explicit 'boss_spawn' key (works whether or not
        # the dict also has a 'spawns' key).
        if "boss_spawn" in world and world["boss_spawn"]:
            boss = world["boss_spawn"]
            if isinstance(boss, dict):
                boss_entry = SpawnEntry(
                    x=int(boss.get("x", 0)),
                    y=int(boss.get("y", 0)),
                    z=int(boss.get("z", 7)),
                    monster_name=str(
                        boss.get("monster_name", boss.get("name", "Boss"))
                    ),
                    interval=int(boss.get("interval", 600) or 600),
                    is_boss=True,
                )
                plan.boss_spawn = boss_entry
                if boss_entry not in plan.spawns:
                    plan.spawns.append(boss_entry)

        return plan

    # ------------------------------------------------------------------
    # Difficulty helpers (kept for backwards compatibility)
    # ------------------------------------------------------------------

    def _difficulty_tier(self, avg_level: float) -> str:
        if avg_level < 200:
            return "easy"
        elif avg_level < 400:
            return "medium"
        elif avg_level < 600:
            return "hard"
        else:
            return "extreme"

    def _num_spawns(self, tier: str, avg_level: float) -> int:
        if tier == "easy":
            return 1
        elif tier == "medium":
            return 2
        elif tier == "hard":
            return 3
        else:
            return 4

    def _pick_boss(self, available: List[str], avg_level: float) -> str:
        import random

        rng = random.Random(hash(f"boss_{avg_level}") % (2**31))

        boss_candidates = [
            m
            for m in available
            if m
            in {
                "Frazzlemaw",
                "Guzzlemaw",
                "Cloak Of Terror",
                "Vexclaw",
            }
        ]
        if boss_candidates:
            return rng.choice(boss_candidates)
        return available[0] if available else "Frazzlemaw"
