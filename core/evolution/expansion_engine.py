from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class ExpansionType(Enum):
    NEW_AREA = "new_area"
    NEW_CAVE = "new_cave"
    BOSS_ROOM = "boss_room"
    QUEST_ZONE = "quest_zone"
    CITY_EXPANSION = "city_expansion"
    HUNT_EXPANSION = "hunt_expansion"


@dataclass
class ExpansionPlan:
    expansion_type: ExpansionType
    name: str
    position: Tuple[int, int, int]  # (x, y, z)
    width: int
    height: int
    attached_to: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    connection_points: List[Tuple[int, int]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expansion_type": self.expansion_type.value,
            "name": self.name,
            "position": self.position,
            "width": self.width,
            "height": self.height,
            "attached_to": self.attached_to,
            "details": self.details,
            "connection_points": self.connection_points,
        }


@dataclass
class ExpansionResult:
    expanded_data: Dict[str, Any]
    expansions_applied: List[ExpansionPlan]
    tiles_added: int
    new_zones_created: int
    summary: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expansions": [e.to_dict() for e in self.expansions_applied],
            "tiles_added": self.tiles_added,
            "new_zones_created": self.new_zones_created,
            "summary": self.summary,
        }


class ExpansionEngine:
    """
    Adds new areas to an existing OTBM map without breaking the original.

    Capabilities:
      - Add new areas (islands, continents, regions)
      - Add new caves / underground systems
      - Add boss rooms with proper arena design
      - Add quest zones with progression paths
      - Expand city boundaries
      - Expand hunt areas
      - Maintain connectivity with original map via bridges/teleports
    """

    # Ground item IDs for different terrain types
    TERRAIN_GROUNDS = {
        "grass": 103,
        "dirt": 102,
        "stone": 1284,
        "cave_floor": 438,
        "boss_floor": 426,
        "marble": 1118,
        "wood": 420,
        "sand": 231,
    }

    # Wall item IDs
    WALL_IDS = {
        "stone_wall": 1000,
        "cave_wall": 398,
        "boss_wall": 1545,
        "wooden_wall": 1002,
        "marble_wall": 1119,
    }

    # Decorative items for different expansion types
    EXPANSION_DECOR = {
        ExpansionType.BOSS_ROOM: [
            1510,
            1545,
            2052,
            2064,
            2060,
        ],  # Statues, pillars, torches
        ExpansionType.QUEST_ZONE: [1740, 1753, 1764, 1775, 1738],  # Chests, barrels
        ExpansionType.CITY_EXPANSION: [1770, 1779, 1786, 1740, 1738],  # Furniture
        ExpansionType.NEW_AREA: [1304, 2705, 2104, 1499, 1507],  # Nature decor
        ExpansionType.NEW_CAVE: [1304, 1499, 2050, 1775, 1738],  # Cave decor
        ExpansionType.HUNT_EXPANSION: [1304, 2050, 1775, 1499, 2104],  # Mixed
    }

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def expand(
        self,
        otbm_data: Dict[str, Any],
        expansions: Optional[List[ExpansionType]] = None,
    ) -> ExpansionResult:
        """
        Expand an OTBM map with new areas.

        Args:
            otbm_data: Deserialized OTBM structure.
            expansions: List of expansion types to apply. If None, auto-detects.

        Returns:
            ExpansionResult with modified OTBM data and execution summary.
        """
        if expansions is None:
            expansions = self._auto_detect_expansions(otbm_data)

        tiles_before = len(self._get_tiles(otbm_data))
        data = otbm_data
        applied_plans = []
        new_zones = 0

        for exp_type in expansions:
            plan = self._create_expansion_plan(exp_type, data)
            if plan:
                data = self._execute_expansion(plan, data)
                applied_plans.append(plan)
                new_zones += 1

        tiles_after = len(self._get_tiles(data))
        tiles_added = tiles_after - tiles_before

        summary = (
            f"Expansión completada: {len(applied_plans)} nuevas zonas creadas, "
            f"{tiles_added} tiles añadidos. "
            f"Tipos: {[e.expansion_type.value for e in applied_plans]}."
        )

        return ExpansionResult(
            expanded_data=data,
            expansions_applied=applied_plans,
            tiles_added=tiles_added,
            new_zones_created=new_zones,
            summary=summary,
        )

    def expand_with_plan(
        self, otbm_data: Dict[str, Any], plans: List[ExpansionPlan]
    ) -> ExpansionResult:
        """Expand using pre-configured expansion plans."""
        tiles_before = len(self._get_tiles(otbm_data))
        data = otbm_data
        applied = []

        for plan in plans:
            data = self._execute_expansion(plan, data)
            applied.append(plan)

        tiles_after = len(self._get_tiles(data))

        return ExpansionResult(
            expanded_data=data,
            expansions_applied=applied,
            tiles_added=tiles_after - tiles_before,
            new_zones_created=len(applied),
            summary=f"Expansión con {len(applied)} plan(es) predefinidos.",
        )

    # ------------------------------------------------------------------
    # Auto-detection
    # ------------------------------------------------------------------

    def _auto_detect_expansions(self, otbm_data: Dict[str, Any]) -> List[ExpansionType]:
        """Auto-detect what expansions a map needs based on current content."""
        expansions: List[ExpansionType] = []
        map_data = otbm_data.get("map_data", otbm_data)

        towns = map_data.get("towns", [])
        spawns = map_data.get("spawns", [])
        tiles = map_data.get("tiles", [])

        # Check for city
        if not towns:
            expansions.append(ExpansionType.CITY_EXPANSION)

        # Check for boss rooms (look for boss-like monster names)
        boss_names = {
            "boss",
            "lord",
            "king",
            "queen",
            "emperor",
            "demon",
            "dragon lord",
        }
        has_boss = any(
            any(bn in (m.get("name", "")).lower() for bn in boss_names)
            for s in spawns
            for m in s.get("monsters", [])
        )
        if not has_boss and len(tiles) > 50:
            expansions.append(ExpansionType.BOSS_ROOM)

        # Check for quest zones
        has_chests = any(
            item.get("id") in (1740, 1753, 1764)  # Common chest IDs
            for t in tiles
            for item in t.get("items", [])
        )
        if not has_chests and len(tiles) > 30:
            expansions.append(ExpansionType.QUEST_ZONE)

        # Check for caves / underground
        has_underground = any(t.get("z", 7) < 7 for t in tiles)
        if not has_underground and len(tiles) > 40:
            expansions.append(ExpansionType.NEW_CAVE)

        # Always add at least one new area if map is small
        if len(tiles) < 100:
            expansions.append(ExpansionType.NEW_AREA)

        return expansions

    # ------------------------------------------------------------------
    # Plan creation
    # ------------------------------------------------------------------

    def _create_expansion_plan(
        self, exp_type: ExpansionType, data: Dict[str, Any]
    ) -> Optional[ExpansionPlan]:
        """Create an expansion plan based on the map's current layout."""
        tiles = self._get_tiles(data)

        # Find the bounding box to place the new area adjacent
        if tiles:
            tile_set = {(t.get("x", 0), t.get("y", 0)) for t in tiles}
            min_x = min(t[0] for t in tile_set)
            max_x = max(t[0] for t in tile_set)
            min_y = min(t[1] for t in tile_set)
            max_y = max(t[1] for t in tile_set)
        else:
            min_x, max_x, min_y, max_y = 0, 0, 0, 0

        margin = 5

        if exp_type == ExpansionType.NEW_AREA:
            return ExpansionPlan(
                expansion_type=exp_type,
                name="expanded_region",
                position=(max_x + margin, min_y, 7),
                width=15,
                height=15,
                attached_to="main_map",
                details={"terrain": "grass", "description": "New wilderness area"},
            )
        elif exp_type == ExpansionType.NEW_CAVE:
            return ExpansionPlan(
                expansion_type=exp_type,
                name="new_cave_system",
                position=(min_x - margin - 12, max_y + margin, 7),
                width=12,
                height=10,
                attached_to="main_map",
                details={
                    "terrain": "cave_floor",
                    "description": "Underground cave system",
                },
            )
        elif exp_type == ExpansionType.BOSS_ROOM:
            return ExpansionPlan(
                expansion_type=exp_type,
                name="boss_arena",
                position=(max_x + margin, max_y + margin, 7),
                width=10,
                height=10,
                attached_to="main_map",
                details={
                    "terrain": "boss_floor",
                    "description": "Boss arena with decorative elements",
                    "boss_name": "Ancient Dragon",
                },
            )
        elif exp_type == ExpansionType.QUEST_ZONE:
            return ExpansionPlan(
                expansion_type=exp_type,
                name="quest_hall",
                position=(min_x - margin - 10, min_y, 7),
                width=10,
                height=8,
                attached_to="main_map",
                details={
                    "terrain": "marble",
                    "description": "Quest zone with chests and rewards",
                },
            )
        elif exp_type == ExpansionType.CITY_EXPANSION:
            return ExpansionPlan(
                expansion_type=exp_type,
                name="city_expansion",
                position=(max_x + margin, min_y - margin - 12, 7),
                width=12,
                height=12,
                attached_to="main_map",
                details={"terrain": "stone", "description": "City district expansion"},
            )
        elif exp_type == ExpansionType.HUNT_EXPANSION:
            return ExpansionPlan(
                expansion_type=exp_type,
                name="hunting_grounds",
                position=(min_x - margin - 15, max_y + margin, 7),
                width=14,
                height=10,
                attached_to="main_map",
                details={"terrain": "dirt", "description": "Expanded hunting grounds"},
            )

        return None

    # ------------------------------------------------------------------
    # Expansion execution
    # ------------------------------------------------------------------

    def _execute_expansion(
        self, plan: ExpansionPlan, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single expansion plan on the OTBM data."""
        handler = self._get_expansion_handler(plan.expansion_type)
        if handler:
            return handler(data, plan)
        return data

    def _get_expansion_handler(self, exp_type: ExpansionType):
        handlers = {
            ExpansionType.NEW_AREA: self._build_new_area,
            ExpansionType.NEW_CAVE: self._build_new_cave,
            ExpansionType.BOSS_ROOM: self._build_boss_room,
            ExpansionType.QUEST_ZONE: self._build_quest_zone,
            ExpansionType.CITY_EXPANSION: self._build_city_expansion,
            ExpansionType.HUNT_EXPANSION: self._build_hunt_expansion,
        }
        return handlers.get(exp_type)

    # ------------------------------------------------------------------
    # Builder methods
    # ------------------------------------------------------------------

    def _build_new_area(
        self, data: Dict[str, Any], plan: ExpansionPlan
    ) -> Dict[str, Any]:
        """Build a new wilderness area."""
        tiles = self._get_tiles(data)
        bx, by, bz = plan.position
        w, h = plan.width, plan.height
        ground_id = self.TERRAIN_GROUNDS.get(plan.details.get("terrain", "grass"), 103)
        decor_ids = self.EXPANSION_DECOR.get(plan.expansion_type, [1304, 2705, 2104])

        # Build the rectangular area
        for x in range(bx, bx + w):
            for y in range(by, by + h):
                items = [{"id": ground_id, "count": 1}]
                # Add random decoration
                if (x + y) % 4 == 0:
                    decor_id = decor_ids[(x + y) % len(decor_ids)]
                    items.append({"id": decor_id, "count": 1})
                tiles.append(
                    {
                        "x": x,
                        "y": y,
                        "z": bz,
                        "items": items,
                        "flags": 0,
                    }
                )

        # Add walls around the border
        for x in range(bx - 1, bx + w + 1):
            tiles.append(
                {
                    "x": x,
                    "y": by - 1,
                    "z": bz,
                    "items": [{"id": self.WALL_IDS["stone_wall"], "count": 1}],
                    "flags": 64,
                }
            )
            tiles.append(
                {
                    "x": x,
                    "y": by + h,
                    "z": bz,
                    "items": [{"id": self.WALL_IDS["stone_wall"], "count": 1}],
                    "flags": 64,
                }
            )
        for y in range(by, by + h):
            tiles.append(
                {
                    "x": bx - 1,
                    "y": y,
                    "z": bz,
                    "items": [{"id": self.WALL_IDS["stone_wall"], "count": 1}],
                    "flags": 64,
                }
            )
            tiles.append(
                {
                    "x": bx + w,
                    "y": y,
                    "z": bz,
                    "items": [{"id": self.WALL_IDS["stone_wall"], "count": 1}],
                    "flags": 64,
                }
            )

        # Create entrance (gap in wall on the west side)
        entrance_x = bx - 1
        entrance_y = by + h // 2
        # Remove wall at entrance
        tiles = [
            t
            for t in tiles
            if not (
                t["x"] == entrance_x and t["y"] == entrance_y and t.get("flags") == 64
            )
        ]
        tiles.append(
            {
                "x": entrance_x,
                "y": entrance_y,
                "z": bz,
                "items": [{"id": ground_id, "count": 1}],
                "flags": 0,
            }
        )

        # Add spawns in the new area
        spawns = self._get_spawns(data)
        spawns.append(
            {
                "name": f"{plan.name}_spawn",
                "center_position": (bx + w // 2, by + h // 2, bz),
                "radius": 8,
                "monsters": [
                    {"name": "Orc Warrior", "count": 3},
                    {"name": "Minotaur", "count": 2},
                ],
            }
        )

        data = self._set_spawns(data, spawns)
        return self._set_tiles(data, tiles)

    def _build_new_cave(
        self, data: Dict[str, Any], plan: ExpansionPlan
    ) -> Dict[str, Any]:
        """Build a cave system with winding corridors and chambers."""
        tiles = self._get_tiles(data)
        bx, by, bz = plan.position
        w, h = plan.width, plan.height
        ground_id = self.TERRAIN_GROUNDS.get(
            plan.details.get("terrain", "cave_floor"), 438
        )
        wall_id = self.WALL_IDS["cave_wall"]
        decor_ids = self.EXPANSION_DECOR.get(plan.expansion_type, [1304, 1499, 2050])

        # Create natural-looking cave (irregular shape)
        import random

        random.seed(42)

        cave_tiles: Set[Tuple[int, int]] = set()

        # Generate cave chambers
        chambers = [
            (bx + 3, by + 3, 4, 4),
            (bx + 8, by + 5, 3, 3),
            (bx + 2, by + 7, 2, 2),
        ]

        for cx, cy, cw, ch in chambers:
            for x in range(cx, cx + cw):
                for y in range(cy, cy + ch):
                    if random.random() < 0.85:  # 85% fill for natural look
                        cave_tiles.add((x, y))

        # Create corridors connecting chambers
        corridors = [
            ((bx + 5, by + 5), (bx + 8, by + 6)),
            ((bx + 8, by + 6), (bx + 3, by + 8)),
        ]
        for (sx, sy), (ex, ey) in corridors:
            cx, cy = sx, sy
            while cx != ex or cy != ey:
                cave_tiles.add((cx, cy))
                if cx < ex:
                    cx += 1
                elif cx > ex:
                    cx -= 1
                elif cy < ey:
                    cy += 1
                else:
                    cy -= 1
            cave_tiles.add((ex, ey))

        # Fill the cave tiles
        for x, y in cave_tiles:
            if bx <= x < bx + w and by <= y < by + h:
                items = [{"id": ground_id, "count": 1}]
                if random.random() < 0.15:
                    decor_id = decor_ids[random.randint(0, len(decor_ids) - 1)]
                    items.append({"id": decor_id, "count": 1})
                tiles.append(
                    {
                        "x": x,
                        "y": y,
                        "z": bz,
                        "items": items,
                        "flags": 0,
                    }
                )

        # Border walls for cave feeling
        for x in range(bx - 1, bx + w + 1):
            for y in [by - 1, by + h]:
                if (x, y + (1 if y == by + h else 0)) not in cave_tiles:
                    tiles.append(
                        {
                            "x": x,
                            "y": y,
                            "z": bz,
                            "items": [{"id": wall_id, "count": 1}],
                            "flags": 64,
                        }
                    )
        for y in range(by - 1, by + h + 1):
            for x_d in [bx - 1, bx + w]:
                if (x_d, y) not in cave_tiles:
                    tiles.append(
                        {
                            "x": x_d,
                            "y": y,
                            "z": bz,
                            "items": [{"id": wall_id, "count": 1}],
                            "flags": 64,
                        }
                    )

        # Entrance
        tiles.append(
            {
                "x": bx,
                "y": by + h // 2,
                "z": bz,
                "items": [{"id": ground_id, "count": 1}],
                "flags": 0,
            }
        )

        # Add spawns
        spawns = self._get_spawns(data)
        spawns.append(
            {
                "name": f"{plan.name}_spawn",
                "center_position": (bx + w // 2, by + h // 2, bz),
                "radius": 6,
                "monsters": [
                    {"name": "Dwarf", "count": 2},
                    {"name": "Dwarf Soldier", "count": 2},
                    {"name": "Dwarf Guard", "count": 1},
                ],
            }
        )

        data = self._set_spawns(data, spawns)
        return self._set_tiles(data, tiles)

    def _build_boss_room(
        self, data: Dict[str, Any], plan: ExpansionPlan
    ) -> Dict[str, Any]:
        """Build a dedicated boss arena."""
        tiles = self._get_tiles(data)
        bx, by, bz = plan.position
        w, h = plan.width, plan.height
        ground_id = self.TERRAIN_GROUNDS.get(
            plan.details.get("terrain", "boss_floor"), 426
        )
        wall_id = self.WALL_IDS["boss_wall"]
        self.EXPANSION_DECOR.get(plan.expansion_type, [1510, 1545, 2052])

        # Arena floor
        for x in range(bx, bx + w):
            for y in range(by, by + h):
                items = [{"id": ground_id, "count": 1}]
                # Pillars at corners and center edges
                if (x == bx or x == bx + w - 1) and (y == by or y == by + h - 1):
                    items.append({"id": 1545, "count": 1})  # Pillar
                elif x == bx + w // 2 and (y == by + 1 or y == by + h - 2):
                    items.append({"id": 2052, "count": 1})  # Wall torch
                tiles.append({"x": x, "y": y, "z": bz, "items": items, "flags": 0})

        # Walls around arena
        for x in range(bx - 1, bx + w + 1):
            tiles.append(
                {
                    "x": x,
                    "y": by - 1,
                    "z": bz,
                    "items": [{"id": wall_id, "count": 1}],
                    "flags": 64,
                }
            )
            tiles.append(
                {
                    "x": x,
                    "y": by + h,
                    "z": bz,
                    "items": [{"id": wall_id, "count": 1}],
                    "flags": 64,
                }
            )
        for y in range(by, by + h):
            tiles.append(
                {
                    "x": bx - 1,
                    "y": y,
                    "z": bz,
                    "items": [{"id": wall_id, "count": 1}],
                    "flags": 64,
                }
            )
            tiles.append(
                {
                    "x": bx + w,
                    "y": y,
                    "z": bz,
                    "items": [{"id": wall_id, "count": 1}],
                    "flags": 64,
                }
            )

        # Grand entrance on south side
        entrance_y = by + h
        for ex in range(bx + w // 2 - 1, bx + w // 2 + 2):
            tiles = [
                t
                for t in tiles
                if not (t["x"] == ex and t["y"] == entrance_y and t.get("flags") == 64)
            ]
            tiles.append(
                {
                    "x": ex,
                    "y": entrance_y,
                    "z": bz,
                    "items": [{"id": ground_id, "count": 1}],
                    "flags": 0,
                }
            )

        # Boss spawn
        boss_name = plan.details.get("boss_name", "Demon Lord")
        spawns = self._get_spawns(data)
        spawns.append(
            {
                "name": f"{plan.name}_boss",
                "center_position": (bx + w // 2, by + h // 2, bz),
                "radius": 2,
                "monsters": [{"name": boss_name, "count": 1}],
            }
        )

        # Add minion spawns around the boss
        for i, (mx, my) in enumerate(
            [
                (bx + 2, by + 2),
                (bx + w - 3, by + 2),
                (bx + 2, by + h - 3),
                (bx + w - 3, by + h - 3),
            ]
        ):
            spawns.append(
                {
                    "name": f"{plan.name}_minion_{i}",
                    "center_position": (mx, my, bz),
                    "radius": 2,
                    "monsters": [{"name": "Fire Elemental", "count": 2}],
                }
            )

        # Add a teleport/entrance point for the town
        town_data = data.get("map_data", data)
        towns = town_data.get("towns", [])
        if towns:
            towns[0]["temple_position"] = (bx + w // 2, by + h // 2, bz)

        data = self._set_spawns(data, spawns)
        return self._set_tiles(data, tiles)

    def _build_quest_zone(
        self, data: Dict[str, Any], plan: ExpansionPlan
    ) -> Dict[str, Any]:
        """Build a quest zone with rooms and chests."""
        tiles = self._get_tiles(data)
        bx, by, bz = plan.position
        w, h = plan.width, plan.height
        ground_id = self.TERRAIN_GROUNDS.get(
            plan.details.get("terrain", "marble"), 1118
        )

        # Main hall
        for x in range(bx, bx + w):
            for y in range(by, by + h):
                items = [{"id": ground_id, "count": 1}]
                tiles.append({"x": x, "y": y, "z": bz, "items": items, "flags": 0})

        # Walls
        wall_id = self.WALL_IDS["marble_wall"]
        for x in range(bx - 1, bx + w + 1):
            tiles.append(
                {
                    "x": x,
                    "y": by - 1,
                    "z": bz,
                    "items": [{"id": wall_id, "count": 1}],
                    "flags": 64,
                }
            )
            tiles.append(
                {
                    "x": x,
                    "y": by + h,
                    "z": bz,
                    "items": [{"id": wall_id, "count": 1}],
                    "flags": 64,
                }
            )
        for y in range(by, by + h):
            tiles.append(
                {
                    "x": bx - 1,
                    "y": y,
                    "z": bz,
                    "items": [{"id": wall_id, "count": 1}],
                    "flags": 64,
                }
            )
            tiles.append(
                {
                    "x": bx + w,
                    "y": y,
                    "z": bz,
                    "items": [{"id": wall_id, "count": 1}],
                    "flags": 64,
                }
            )

        # Entrance
        entrance_y = by + h // 2
        tiles = [
            t
            for t in tiles
            if not (t["x"] == bx - 1 and t["y"] == entrance_y and t.get("flags") == 64)
        ]
        tiles.append(
            {
                "x": bx - 1,
                "y": entrance_y,
                "z": bz,
                "items": [{"id": ground_id, "count": 1}],
                "flags": 0,
            }
        )

        # Place chests with rewards
        chest_positions = [
            (bx + w - 2, by + 2),
            (bx + w - 2, by + h - 3),
            (bx + 2, by + h - 3),
        ]
        for cx, cy in chest_positions:
            for t in tiles:
                if t["x"] == cx and t["y"] == cy and t["z"] == bz:
                    t["items"].append({"id": 1740, "count": 1})  # Chest
                    break

        # Add quest NPCs / spawns area
        spawns = self._get_spawns(data)
        spawns.append(
            {
                "name": f"{plan.name}_quest_guardians",
                "center_position": (bx + w // 2, by + h - 2, bz),
                "radius": 3,
                "monsters": [
                    {"name": "Hero", "count": 2},
                    {"name": "Necromancer", "count": 1},
                ],
            }
        )

        data = self._set_spawns(data, spawns)
        return self._set_tiles(data, tiles)

    def _build_city_expansion(
        self, data: Dict[str, Any], plan: ExpansionPlan
    ) -> Dict[str, Any]:
        """Build a city district expansion with buildings."""
        tiles = self._get_tiles(data)
        bx, by, bz = plan.position
        w, h = plan.width, plan.height
        ground_id = self.TERRAIN_GROUNDS.get(plan.details.get("terrain", "stone"), 1284)

        # Main plaza
        for x in range(bx, bx + w):
            for y in range(by, by + h):
                items = [{"id": ground_id, "count": 1}]
                # Decorative elements in the plaza
                if x == bx + w // 2 and y == by + h // 2:
                    items.append({"id": 1510, "count": 1})  # Central statue
                tiles.append(
                    {"x": x, "y": y, "z": bz, "items": items, "flags": 1}
                )  # PZ zone

        # Building outlines (using walls to create structures)
        buildings = [
            (bx + 2, by + 2, 4, 3),  # Building 1
            (bx + 7, by + 2, 3, 3),  # Building 2
            (bx + 2, by + 7, 3, 3),  # Building 3
        ]

        wall_id = self.WALL_IDS["stone_wall"]
        floor_id = self.TERRAIN_GROUNDS["wood"]

        for bld_x, bld_y, bld_w, bld_h in buildings:
            # Fill interior with wooden floor
            for ix in range(bld_x, bld_x + bld_w):
                for iy in range(bld_y, bld_y + bld_h):
                    # Replace ground tile with wooden floor
                    tiles = [
                        t
                        for t in tiles
                        if not (t["x"] == ix and t["y"] == iy and t["z"] == bz)
                    ]
                    tiles.append(
                        {
                            "x": ix,
                            "y": iy,
                            "z": bz,
                            "items": [{"id": floor_id, "count": 1}],
                            "flags": 1,
                        }
                    )
            # Walls around building
            for wx in range(bld_x - 1, bld_x + bld_w + 1):
                tiles.append(
                    {
                        "x": wx,
                        "y": bld_y - 1,
                        "z": bz,
                        "items": [{"id": wall_id, "count": 1}],
                        "flags": 64,
                    }
                )
                tiles.append(
                    {
                        "x": wx,
                        "y": bld_y + bld_h,
                        "z": bz,
                        "items": [{"id": wall_id, "count": 1}],
                        "flags": 64,
                    }
                )
            for wy in range(bld_y, bld_y + bld_h):
                tiles.append(
                    {
                        "x": bld_x - 1,
                        "y": wy,
                        "z": bz,
                        "items": [{"id": wall_id, "count": 1}],
                        "flags": 64,
                    }
                )
                tiles.append(
                    {
                        "x": bld_x + bld_w,
                        "y": wy,
                        "z": bz,
                        "items": [{"id": wall_id, "count": 1}],
                        "flags": 64,
                    }
                )
            # Door opening
            door_y = bld_y + bld_h
            door_x = bld_x + bld_w // 2
            tiles = [
                t
                for t in tiles
                if not (t["x"] == door_x and t["y"] == door_y and t.get("flags") == 64)
            ]
            tiles.append(
                {
                    "x": door_x,
                    "y": door_y,
                    "z": bz,
                    "items": [{"id": ground_id, "count": 1}],
                    "flags": 1,
                }
            )

        # Add town data
        town_data = data.get("map_data", data)
        if "towns" not in town_data:
            town_data["towns"] = []
        town_data["towns"].append(
            {
                "name": plan.name,
                "position": (bx + w // 2, by + h // 2, bz),
                "temple_position": (bx + w // 2, by + h // 2, bz),
            }
        )

        return self._set_tiles(data, tiles)

    def _build_hunt_expansion(
        self, data: Dict[str, Any], plan: ExpansionPlan
    ) -> Dict[str, Any]:
        """Build expanded hunting grounds with varied terrain."""
        tiles = self._get_tiles(data)
        bx, by, bz = plan.position
        w, h = plan.width, plan.height
        ground_id = self.TERRAIN_GROUNDS.get(plan.details.get("terrain", "dirt"), 102)

        import random

        random.seed(123)

        # Varied terrain patches
        for x in range(bx, bx + w):
            for y in range(by, by + h):
                ground = ground_id
                if random.random() < 0.2:
                    ground = self.TERRAIN_GROUNDS["grass"]
                elif random.random() < 0.1:
                    ground = self.TERRAIN_GROUNDS["sand"]
                items = [{"id": ground, "count": 1}]
                if random.random() < 0.12:
                    items.append({"id": 2705, "count": 1})  # Bush
                tiles.append({"x": x, "y": y, "z": bz, "items": items, "flags": 0})

        # Spawn points distributed across the area
        spawns = self._get_spawns(data)
        monster_packs = [
            [{"name": "Cyclops", "count": 3}],
            [{"name": "Dragon", "count": 2}],
            [{"name": "Hydra", "count": 1}, {"name": "Serpent Spawn", "count": 2}],
            [{"name": "Behemoth", "count": 2}],
        ]

        for i, pack in enumerate(monster_packs):
            sx = bx + 2 + (i % 2) * (w // 2 - 2)
            sy = by + 2 + (i // 2) * (h // 2 - 2)
            spawns.append(
                {
                    "name": f"{plan.name}_pack_{i}",
                    "center_position": (sx, sy, bz),
                    "radius": 4,
                    "monsters": pack,
                }
            )

        data = self._set_spawns(data, spawns)
        return self._set_tiles(data, tiles)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_tiles(self, data: Dict[str, Any]) -> List[Dict]:
        map_data = data.get("map_data", data)
        return map_data.get("tiles", [])

    def _set_tiles(self, data: Dict[str, Any], tiles: List[Dict]) -> Dict[str, Any]:
        if "map_data" in data:
            data["map_data"]["tiles"] = tiles
        else:
            data["tiles"] = tiles
        return data

    def _get_spawns(self, data: Dict[str, Any]) -> List[Dict]:
        map_data = data.get("map_data", data)
        return map_data.get("spawns", [])

    def _set_spawns(self, data: Dict[str, Any], spawns: List[Dict]) -> Dict[str, Any]:
        if "map_data" in data:
            data["map_data"]["spawns"] = spawns
        else:
            data["spawns"] = spawns
        return data
