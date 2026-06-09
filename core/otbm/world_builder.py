"""
World Builder — assembles a WorldModel from decoded OTBM data.

Pipeline:
    OtbmParser.parse(data) -> raw parsed tree
    NodeDecoder.decode_*(node) -> decoded dicts
    TileDecoder.to_worldmodel_tile(tile) -> tile dicts
    WorldBuilder.build(parsed_tree) -> WorldModel

Handles:
    - Creating WorldModel from fully decoded OTBM data
    - Adding tiles with ground + items
    - Adding spawns with monster names
    - Adding towns/cities with temple positions
    - Adding waypoints
    - Setting map metadata (version, description, etc.)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .node_decoder import NodeDecoder
from .tile_decoder import TileDecoder
from .node_encoder import (
    TILESTATE_NONE,
    TILESTATE_PROTECTIONZONE,
    TILESTATE_NOPVPZONE,
    TILESTATE_NOLOGOUT,
    TILESTATE_PVPZONE,
)


class WorldBuildError(Exception):
    """Raised when building a WorldModel from OTBM data fails."""
    pass


class WorldBuilder:
    """
    Assembles a WorldModel from decoded OTBM data.

    Uses NodeDecoder and TileDecoder to progressively decode the
    parsed OTBM tree, then constructs a WorldModel-compatible dict
    that can be used with the existing export pipeline.
    """

    def __init__(self):
        self._node_decoder = NodeDecoder()
        self._tile_decoder = TileDecoder()

    def build(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a WorldModel-compatible dict from parsed OTBM data.

        Args:
            parsed_data: Output from OtbmParser.parse().

        Returns:
            Dict in WorldModel-compatible format:
            {
                "version": int,
                "width": int,
                "height": int,
                "item_major": int,
                "item_minor": int,
                "description": str,
                "spawn_file": str,
                "house_file": str,
                "tiles": [dict, ...],  # tile dicts
                "spawns": [dict, ...],  # spawn entries
                "cities": [dict, ...],  # town entries as cities
                "waypoints": [dict, ...],  # waypoint entries
                "tile_count": int,
                "spawn_count": int,
                "city_count": int,
                "waypoint_count": int,
            }
        """
        root = parsed_data.get("root", {})
        if not root:
            raise WorldBuildError("No root node found in parsed OTBM data")

        # Decode root structure
        decoded_root = self._node_decoder.decode_root(root)

        # Build result
        result: Dict[str, Any] = {
            "version": decoded_root.get("version", 0),
            "width": decoded_root.get("width", 0),
            "height": decoded_root.get("height", 0),
            "item_major": decoded_root.get("item_major", 3),
            "item_minor": decoded_root.get("item_minor", 57),
            "description": "",
            "spawn_file": "",
            "house_file": "",
            "tiles": [],
            "spawns": [],
            "cities": [],
            "waypoints": [],
            "tile_count": 0,
            "spawn_count": 0,
            "city_count": 0,
            "waypoint_count": 0,
        }

        # Map data (description, spawn_file, house_file)
        map_data = decoded_root.get("map_data")
        if map_data:
            result["description"] = map_data.get("description", "")
            result["spawn_file"] = map_data.get("spawn_file", "")
            result["house_file"] = map_data.get("house_file", "")

        # Tiles from all TILE_AREA nodes
        tiles = self._extract_tiles(decoded_root)
        result["tiles"] = tiles
        result["tile_count"] = len(tiles)

        # Spawns
        spawns = self._extract_spawns(decoded_root)
        result["spawns"] = spawns
        result["spawn_count"] = len(spawns)

        # Towns as cities
        cities = self._extract_cities(decoded_root)
        result["cities"] = cities
        result["city_count"] = len(cities)

        # Waypoints
        waypoints = self._extract_waypoints(decoded_root)
        result["waypoints"] = waypoints
        result["waypoint_count"] = len(waypoints)

        return result

    def build_to_worldmodel_dict(
        self, parsed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build a dict that can be directly used to create a WorldModel instance.

        Returns a flat dict compatible with the WorldModel dataclass:
        {
            "tiles": list of tile dicts,
            "cities": list of city dicts,
            "spawns": list of spawn dicts,
            "waypoints": list of waypoint dicts,
        }
        """
        built = self.build(parsed_data)

        # Convert tiles to the format expected by WorldModel
        return {
            "tiles": built["tiles"],
            "cities": built["cities"],
            "spawns": built["spawns"],
            "waypoints": built["waypoints"],
            "description": built["description"],
        }

    # ------------------------------------------------------------------
    # Internal extraction methods
    # ------------------------------------------------------------------

    def _extract_tiles(self, decoded_root: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all tiles from decoded root, converting to WorldModel format."""
        tiles = []

        for area_node in decoded_root.get("tile_areas", []):
            try:
                area_decoded = self._node_decoder.decode_tile_area(area_node)
                area_tiles = self._tile_decoder.decode_area(area_decoded)
                tiles.extend(area_tiles)
            except Exception as e:
                # Skip malformed areas
                continue

        return tiles

    def _extract_spawns(self, decoded_root: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract spawn entries from decoded root."""
        spawns_node = decoded_root.get("spawns")
        if not spawns_node:
            return []

        spawns_decoded = self._node_decoder.decode_spawns(spawns_node)
        result = []

        for area in spawns_decoded.get("spawn_areas", []):
            for monster in area.get("monsters", []):
                result.append({
                    "monster": monster["name"],
                    "x": area["center_x"],
                    "y": area["center_y"],
                    "z": area["center_z"],
                    "radius": area["radius"],
                    "respawn": monster.get("spawntime", 60),
                    "direction": monster.get("direction", 2),
                })

        return result

    def _extract_cities(self, decoded_root: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract towns as city entries from decoded root."""
        towns_node = decoded_root.get("towns")
        if not towns_node:
            return []

        towns_decoded = self._node_decoder.decode_towns(towns_node)
        result = []

        for town in towns_decoded.get("towns", []):
            result.append({
                "name": town["name"],
                "x": town["temple_x"],
                "y": town["temple_y"],
                "z": town["temple_z"],
                "temple_x": town["temple_x"],
                "temple_y": town["temple_y"],
                "temple_z": town["temple_z"],
                "town_id": town.get("town_id", 0),
            })

        return result

    def _extract_waypoints(
        self, decoded_root: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract waypoints from decoded root."""
        wp_node = decoded_root.get("waypoints")
        if not wp_node:
            return []

        wp_decoded = self._node_decoder.decode_waypoints(wp_node)
        return wp_decoded.get("waypoints", [])

    # ------------------------------------------------------------------
    # Convenience: convert WorldModel dict to Tile dataclass
    # ------------------------------------------------------------------

    def tile_dict_to_tile(self, tile_dict: Dict[str, Any]) -> Any:
        """
        Convert a tile dict to a WorldModel Tile dataclass instance.

        This imports the Tile class from core.world_engine.world_engine
        to avoid circular imports at module level.

        Args:
            tile_dict: Tile dict in the format produced by _extract_tiles.

        Returns:
            Tile dataclass instance.
        """
        from core.world_engine.world_engine import Tile

        ground_str = str(tile_dict.get("ground", "0"))
        try:
            ground_val = int(ground_str)
        except ValueError:
            ground_val = 0

        items = tile_dict.get("items", [])

        flags = tile_dict.get("flags", TILESTATE_NONE)

        tile = Tile(
            x=int(tile_dict.get("x", 0)),
            y=int(tile_dict.get("y", 0)),
            z=int(tile_dict.get("z", 0)),
            ground=str(ground_val),
            items=items,
            flags=flags,
        )

        # Set spawn if present
        spawn = tile_dict.get("spawn")
        if spawn and isinstance(spawn, dict):
            tile.spawn = spawn

        return tile

    def to_worldmodel(self, parsed_data: Dict[str, Any]) -> Any:
        """
        Build a full WorldModel instance from parsed OTBM data.

        Args:
            parsed_data: Output from OtbmParser.parse().

        Returns:
            WorldModel dataclass instance.
        """
        from core.world_engine.world_engine import WorldModel, Tile

        built = self.build(parsed_data)
        wm = WorldModel()

        # Set dimensions
        wm_width = built.get("width", 0)
        wm_height = built.get("height", 0)

        # Add tiles
        for td in built.get("tiles", []):
            tile = self.tile_dict_to_tile(td)
            wm.add_tile(tile)

        # Add spawns
        for spawn in built.get("spawns", []):
            wm.add_spawn(spawn)

        # Add cities
        for city in built.get("cities", []):
            wm.add_city(city)

        # Add waypoints
        for wp in built.get("waypoints", []):
            wm.waypoints.append(wp)

        return wm