"""
Convierte el modelo City (distritos, roads, buildings, waypoints)
en un WorldModel para exportación directa a OTBM.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.world_engine.world_engine import WorldModel, Tile

from .city_generator import City, District, Waypoint
from .road_generator import Road
from .building_generator import Building
from .temple_generator import generate_temple_layout
from .depot_generator import generate_depot_layout
from .market_generator import generate_market_layout
from .harbor_generator import generate_harbor_layout


class CityToWorldModel:
    """
    Converts a City dataclass (from CityGenerator) into a WorldModel
    ready for OTBM serialization.

    Maps:
      - District tiles → WorldModel tiles
      - Roads → ground tiles with road ID
      - Temple / Depot / Market / Harbor → special item layouts
      - Buildings → wall-bordered structures
      - Waypoints → waypoints array in WorldModel
      - Spawns → spawns array in WorldModel
    """

    # OTBM item IDs for city elements
    CITY_GROUND_IDS: Dict[str, int] = {
        "issavi": 113,
        "thais": 112,
        "venore": 112,
        "yalahar": 116,
        "carlin": 112,
        "ankrahmun": 111,
        "darashia": 111,
        "edron": 114,
        "default": 112,
    }

    ROAD_GROUND_IDS: Dict[str, int] = {
        "issavi": 415,
        "thais": 415,
        "venore": 416,
        "yalahar": 416,
        "carlin": 415,
        "ankrahmun": 415,
        "darashia": 415,
        "edron": 415,
        "default": 415,
    }

    BUILDING_FLOOR_IDS: Dict[str, int] = {
        "issavi": 393,
        "thais": 393,
        "venore": 394,
        "yalahar": 393,
        "carlin": 393,
        "ankrahmun": 394,
        "darashia": 393,
        "edron": 393,
        "default": 393,
    }

    WALL_IDS: Dict[str, int] = {
        "issavi": 1495,
        "thais": 1495,
        "venore": 1496,
        "yalahar": 1495,
        "carlin": 1497,
        "ankrahmun": 1495,
        "darashia": 1495,
        "edron": 1495,
        "default": 1495,
    }

    DECORATION_IDS: Dict[str, int] = {
        "issavi": 2162,   # crystal glow
        "thais": 2050,    # torch
        "venore": 2050,
        "yalahar": 2153,
        "carlin": 2050,
        "ankrahmun": 2050,
        "darashia": 2153,
        "edron": 2050,
        "default": 2050,
    }

    def __init__(self, city: City, template: Optional[Dict[str, Any]] = None):
        self.city = city
        self.template = template or {}
        self._wm = WorldModel()
        self._z = 7  # default city floor

    def convert(self) -> WorldModel:
        """Run the full conversion and return a WorldModel."""
        self._place_district_floors()
        self._place_roads()
        self._place_special_districts()
        self._place_buildings()
        self._transfer_waypoints()
        self._transfer_spawns()
        return self._wm

    def _ground_id(self) -> int:
        theme = self.city.theme.lower()
        return self.CITY_GROUND_IDS.get(theme, self.CITY_GROUND_IDS["default"])

    def _road_id(self) -> int:
        theme = self.city.theme.lower()
        return self.ROAD_GROUND_IDS.get(theme, self.ROAD_GROUND_IDS["default"])

    def _floor_id(self) -> int:
        theme = self.city.theme.lower()
        return self.BUILDING_FLOOR_IDS.get(theme, self.BUILDING_FLOOR_IDS["default"])

    def _wall_id(self) -> int:
        theme = self.city.theme.lower()
        return self.WALL_IDS.get(theme, self.WALL_IDS["default"])

    def _deco_id(self) -> int:
        theme = self.city.theme.lower()
        return self.DECORATION_IDS.get(theme, self.DECORATION_IDS["default"])

    def _add_tile(self, x: int, y: int, ground_id: int, items: Optional[List[int]] = None) -> Tile:
        tile = Tile(x=x, y=y, z=self._z, ground=str(ground_id))
        if items:
            for item_id in items:
                tile.items.append({"id": item_id})
        self._wm.add_tile(tile)
        return tile

    # ------------------------------------------------------------------
    # Placement passes
    # ------------------------------------------------------------------

    def _place_district_floors(self) -> None:
        """Fill each district area with its ground tiles."""
        ground = self._ground_id()
        for district in self.city.districts:
            for dx in range(district.width):
                for dy in range(district.height):
                    self._add_tile(district.x + dx, district.y + dy, ground)

    def _place_roads(self) -> None:
        """Place road tiles along road paths."""
        road_id = self._road_id()
        for road in self.city.roads:
            for (x, y) in road.path:
                self._add_tile(x, y, road_id)

    def _place_special_districts(self) -> None:
        """Apply special layouts for Temple, Depot, Market, Harbor districts."""
        for district in self.city.districts:
            if district.type == "Temple":
                shapes = generate_temple_layout(district, self.template)
                self._apply_shapes(shapes)
            elif district.type == "Depot":
                shapes = generate_depot_layout(district, self.template)
                self._apply_shapes(shapes)
            elif district.type == "Market":
                shapes = generate_market_layout(district, self.template)
                self._apply_shapes(shapes)
            elif district.type == "Harbor":
                shapes = generate_harbor_layout(district, self.template)
                self._apply_shapes(shapes)

    def _apply_shapes(self, shapes: List[Dict[str, Any]]) -> None:
        """Apply layout shapes (dicts with x, y, ground, item) to the WorldModel."""
        for shape in shapes:
            gid = shape.get("ground")
            iid = shape.get("item")
            x = shape.get("x", 0)
            y = shape.get("y", 0)

            if gid is not None:
                ground_str = str(int(gid))
            elif iid is not None:
                ground_str = str(self._ground_id())
            else:
                continue

            items = []
            if iid is not None:
                items.append({"id": int(iid)})
            self._add_tile(x, y, int(ground_str), items=items)

    def _place_buildings(self) -> None:
        """Place building structures with walls as border items."""
        floor_id = self._floor_id()
        wall_id = self._wall_id()

        for building in self.city.buildings:
            for dx in range(building.width):
                for dy in range(building.height):
                    bx = building.x + dx
                    by = building.y + dy
                    # Check if border
                    is_border = (
                        dx == 0
                        or dy == 0
                        or dx == building.width - 1
                        or dy == building.height - 1
                    )
                    items = [{"id": wall_id}] if is_border else []
                    self._add_tile(bx, by, floor_id, items=items)

    def _transfer_waypoints(self) -> None:
        """Transfer City waypoints to WorldModel waypoints list."""
        for wp in self.city.waypoints:
            self._wm.waypoints.append({
                "name": wp.name,
                "x": wp.x,
                "y": wp.y,
                "z": 7,
                "type": wp.type,
            })

    def _transfer_spawns(self) -> None:
        """Transfer spawn entries to WorldModel."""
        for spawn in self.city.spawns:
            spawn_copy = dict(spawn)
            spawn_copy.setdefault("z", 7)
            self._wm.add_spawn(spawn_copy)