"""
Convierte el modelo Dungeon (floors, rooms, corridors, boss rooms,
shortcuts, spawns) en un WorldModel multi-nivel para exportacion OTBM.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.world_engine.world_engine import WorldModel, Tile

from .dungeon_generator import Dungeon
from .floor_generator import Floor as FloorModel

# OTBM item IDs for dungeon elements
STAIRS_DOWN_ID = 1386  # ladder/stairs going down
STAIRS_UP_ID = 1387  # ladder/stairs going up
HOLE_ID = 3214  # rope hole
TILE_FLAG_PZ = 0x0001  # Protection Zone flag

# Item IDs per theme
THEME_GROUND_IDS: Dict[str, int] = {
    "issavi": 406,
    "roshamuul": 672,
    "library": 112,
    "cobra": 110,
    "falcon": 319,
    "soulwar": 113,
    "ice": 670,
    "dragon": 319,
    "default": 110,
}

THEME_WALL_IDS: Dict[str, int] = {
    "issavi": 1495,
    "roshamuul": 672,
    "library": 159,
    "cobra": 313,
    "falcon": 321,
    "soulwar": 409,
    "ice": 675,
    "dragon": 154,
    "default": 1495,
}

THEME_DECO_IDS: Dict[str, int] = {
    "issavi": 2162,
    "roshamuul": 2225,
    "library": 2050,
    "cobra": 2117,
    "falcon": 2229,
    "soulwar": 1469,
    "ice": 2050,
    "dragon": 2016,
    "default": 2050,
}

BOSS_TELEPORT_ID = 1387  # teleport marker for boss room entrance


class DungeonToWorldModel:
    """
    Converts a Dungeon dataclass (from DungeonGenerator) into a WorldModel
    with proper multi-z floors, stairs, holes, boss rooms, and respawns.
    """

    def __init__(self, dungeon: Dungeon, template: Optional[Dict[str, Any]] = None):
        self.dungeon = dungeon
        self.template = template or {}
        self._wm = WorldModel()
        self._base_z = 7

    def convert(self) -> WorldModel:
        """Run the full conversion and return a multi-floor WorldModel."""
        prev_floor = None
        for i, floor in enumerate(self.dungeon.floors):
            z = self._base_z - i  # deeper floors = lower z
            self._place_floor(floor, z)
            if prev_floor is not None:
                self._connect_floors(prev_floor, floor, z + 1, z)
            prev_floor = floor
        self._transfer_spawns()
        self._transfer_shortcuts()
        return self._wm

    def _ground_id(self) -> int:
        t = self.dungeon.theme.lower()
        return THEME_GROUND_IDS.get(t, THEME_GROUND_IDS["default"])

    def _wall_id(self) -> int:
        t = self.dungeon.theme.lower()
        return THEME_WALL_IDS.get(t, THEME_WALL_IDS["default"])

    def _deco_id(self) -> int:
        t = self.dungeon.theme.lower()
        return THEME_DECO_IDS.get(t, THEME_DECO_IDS["default"])

    def _add_tile(
        self,
        x: int,
        y: int,
        z: int,
        ground_id: int,
        items: Optional[List[Dict[str, Any]]] = None,
        flags: int = 0,
    ) -> Tile:
        tile = Tile(x=x, y=y, z=z, ground=str(ground_id), flags=flags)
        if items:
            for item in items:
                tile.items.append(item)
        self._wm.add_tile(tile)
        return tile

    # ------------------------------------------------------------------
    # Floor placement
    # ------------------------------------------------------------------

    def _place_floor(self, floor: FloorModel, z: int) -> None:
        """Place all rooms, corridors, and cave tiles for one floor."""
        ground = self._ground_id()
        wall_id = self._wall_id()

        # Place rooms
        for room in floor.rooms:
            for dx in range(room.width):
                for dy in range(room.height):
                    rx = room.x + dx
                    ry = room.y + dy
                    is_border = (
                        dx == 0
                        or dy == 0
                        or dx == room.width - 1
                        or dy == room.height - 1
                    )
                    items = [{"id": wall_id}] if is_border else []
                    self._add_tile(rx, ry, z, ground, items=items)

            # Special room content
            if room.type == "BossRoom":
                cx, cy = room.center()
                # Boss marker + PZ flag
                self._add_tile(
                    cx,
                    cy,
                    z,
                    ground,
                    items=[{"name": "crystal_torch"}, {"name": "blood"}],
                    flags=TILE_FLAG_PZ,
                )
            elif room.type == "TreasureRoom":
                self._add_tile(
                    room.x + 1, room.y + 1, z, ground, items=[{"id": self._deco_id()}]
                )
            elif room.type == "QuestRoom":
                self._add_tile(
                    room.x + 2, room.y + 2, z, ground, items=[{"id": wall_id}]
                )

        # Place cave tiles if present
        cave_tiles = getattr(floor, "cave_tiles", None)
        if cave_tiles:
            for cx, cy in cave_tiles:
                # Check if not already placed by a room
                key = f"{cx}:{cy}:{z}"
                if key not in self._wm.tiles:
                    self._add_tile(cx, cy, z, ground)

        # Place corridor tiles
        for corridor in floor.corridors:
            for cx, cy in corridor:
                key = f"{cx}:{cy}:{z}"
                if key not in self._wm.tiles:
                    self._add_tile(cx, cy, z, ground)

    def _connect_floors(
        self, upper: FloorModel, lower: FloorModel, upper_z: int, lower_z: int
    ) -> None:
        """
        Place stairs/up between two adjacent floors.
        Finds a central tile on each floor and places stairs down
        on the upper floor and stairs up on the lower floor.
        """
        # Find a corridor or room center tile to place stairs
        up_pos = self._find_stair_pos(upper, upper_z)
        down_pos = self._find_stair_pos(lower, lower_z)

        if up_pos and down_pos:
            # Stairs down on upper floor
            self._add_tile(
                *up_pos, ground_id=self._ground_id(), items=[{"id": STAIRS_DOWN_ID}]
            )
            # Stairs up on lower floor
            self._add_tile(
                *down_pos, ground_id=self._ground_id(), items=[{"id": STAIRS_UP_ID}]
            )

            # Optional: rope hole connecting same coordinates
            hole_x = up_pos[0]
            hole_y = up_pos[1]
            self._add_tile(
                hole_x,
                hole_y,
                lower_z,
                ground_id=self._ground_id(),
                items=[{"id": HOLE_ID}],
            )

    @staticmethod
    def _find_stair_pos(floor: FloorModel, z: int) -> Optional[Tuple[int, int, int]]:
        """Find a good position for stairs on a floor."""
        # Try corridor centermost point
        if floor.corridors:
            mid = floor.corridors[0][len(floor.corridors[0]) // 2]
            return (mid[0], mid[1], z)

        # Try a room center
        if floor.rooms:
            cx, cy = floor.rooms[0].center()
            return (cx, cy, z)

        return (20, 20, z)  # fallback

    # ------------------------------------------------------------------
    # Spawns & Shortcuts
    # ------------------------------------------------------------------

    def _transfer_spawns(self) -> None:
        """Transfer dungeon spawns to WorldModel."""
        for spawn in self.dungeon.spawns:
            spawn_copy = dict(spawn)
            spawn_copy.setdefault("z", self._base_z)
            self._wm.add_spawn(spawn_copy)

        # Also add boss spawns
        for boss_room in self.dungeon.bosses:
            cx, cy = boss_room.center()
            self._wm.add_spawn(
                {
                    "monster": self.template.get("bosses", ["Dragon"])[0],
                    "x": cx,
                    "y": cy,
                    "z": self._base_z,
                    "respawn": 600,
                }
            )

    def _transfer_shortcuts(self) -> None:
        """Add shortcut waypoints (teleport pairs) to WorldModel."""
        for sc in self.dungeon.shortcuts:
            self._wm.waypoints.append(
                {
                    "name": f"Shortcut_{sc.type}_{sc.from_coord}_{sc.to_coord}",
                    "x": sc.from_coord[0],
                    "y": sc.from_coord[1],
                    "z": self._base_z,
                    "type": "Teleport",
                }
            )
            self._wm.waypoints.append(
                {
                    "name": f"Shortcut_{sc.type}_dest",
                    "x": sc.to_coord[0],
                    "y": sc.to_coord[1],
                    "z": self._base_z,
                    "type": "Teleport",
                }
            )
