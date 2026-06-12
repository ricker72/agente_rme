from __future__ import annotations

import io
import logging
import struct
from typing import Any, Dict, List, Optional, Tuple

from .node_encoder import (
    NodeEncoder,
    OTBM_NODE_ROOT,
    OTBM_NODE_MAP_DATA,
    OTBM_NODE_TILE_AREA,
    OTBM_NODE_TILE,
    OTBM_NODE_ITEM,
    OTBM_NODE_SPAWNS,
    OTBM_NODE_SPAWN_AREA,
    OTBM_NODE_MONSTER,
    OTBM_NODE_TOWNS,
    OTBM_NODE_TOWN,
    OTBM_NODE_WAYPOINTS,
    OTBM_NODE_WAYPOINT,
    ATTR_TILE_FLAGS,
    ATTR_COUNT,
    ATTR_ACTION_ID,
    ATTR_UNIQUE_ID,
    ATTR_TEXT,
    ATTR_SUBTYPE,
    ATTR_CHARGES,
    ATTR_DURATION,
    ATTR_DECAYING_STATE,
    DEFAULT_OTBM_VERSION,
    DEFAULT_ITEM_MAJOR_VERSION,
    DEFAULT_ITEM_MINOR_VERSION,
)
from .tile_encoder import TileEncoder

logger = logging.getLogger(__name__)

# v1.0.1 HOTFIX:
#   OTBM non-root node payloads are uint16-sized, so a single TILE_AREA
#   node can hold at most 65535 bytes of children. For large maps
#   (>= 256x256) the serialized tile stream exceeded that limit and the
#   old code path silently truncated the payload, producing corrupt OTBM
#   files. We now group tiles into multiple TILE_AREA nodes (chunked) that
#   each fit inside the uint16 size limit. RME and the OpenTibia server
#   accept an arbitrary number of TILE_AREA nodes per z-level.
MAX_TILE_AREA_PAYLOAD = 30000
MAX_TILE_AREA_TILES = 200


class OtbmSerializer:
    """
    Serializes a WorldModel into real OTBM binary format compatible with
    OpenTibiaBR / Remere's Map Editor.

    OTBM structure:
        ROOT (version, width, height, item_ver)
          ├── MAP_DATA (description, spawn_file, house_file)
          │     ├── TILE_AREA (base_x, base_y, base_z)
          │     │     ├── TILE (offset_x, offset_y [, flags])
          │     │     │     ├── ITEM (ground)
          │     │     │     ├── ITEM (items...)
          │     │     │     └── ...
          │     │     └── ...
          │     ├── SPAWNS
          │     │     ├── SPAWN_AREA (center_x, center_y, z, radius)
          │     │     │     ├── MONSTER (name, direction, spawntime)
          │     │     │     └── ...
          │     │     └── ...
          │     ├── TOWNS
          │     │     ├── TOWN (town_id, name, temple_x, temple_y, temple_z)
          │     │     └── ...
          │     └── WAYPOINTS
          │           ├── WAYPOINT (name, x, y, z)
          │           └── ...
    """

    # OTBM file magic identifier
    OTBM_MAGIC = b"OTBM"

    def __init__(self):
        self.node = NodeEncoder()
        self.tile_encoder = TileEncoder()

    # ------------------------------------------------------------------
    # Serialize
    # ------------------------------------------------------------------

    def serialize(self, world_model: Any) -> bytes:
        """
        Convert a WorldModel into OTBM binary data.

        v1.0.1 HOTFIX:
            We intentionally do NOT wrap children in a MAP_DATA node. A
            single MAP_DATA node is uint16-sized (max 65535 bytes of
            payload), which truncated large maps. RME accepts
            TILE_AREA / SPAWNS / TOWNS / WAYPOINTS as direct children of
            ROOT, so we use that form to avoid the per-node size limit.
            We also chunk the tile stream into TILE_AREA-sized groups
            (see ``_chunk_tiles``).
        """
        # Collect tiles and organize by z-level
        tiles_by_z: Dict[int, List[Any]] = {}
        tiles_list = list(getattr(world_model, "tiles", {}).values())
        if not tiles_list and hasattr(world_model, "tiles_list"):
            tiles_list = world_model.tiles_list

        for tile in tiles_list:
            z = self._get_z(tile)
            tiles_by_z.setdefault(z, []).append(tile)

        # Compute map bounds
        all_x, all_y = [], []
        for z_tiles in tiles_by_z.values():
            for t in z_tiles:
                x = self._get_x(t)
                y = self._get_y(t)
                all_x.append(x)
                all_y.append(y)

        if not all_x:
            width = 1
            height = 1
            root_children = io.BytesIO()
            tile_children = self.node.encode_tile(offset_x=0, offset_y=0)
            tile_area = self.node.encode_tile_area(
                base_x=0, base_y=0, base_z=0, children=tile_children
            )
            root_children.write(tile_area)
        else:
            width = max(all_x) - min(all_x) + 1
            height = max(all_y) - min(all_y) + 1
            root_children = io.BytesIO()

            # Write TILE_AREA nodes per z-level, chunked (v1.0.1 HOTFIX).
            for z in sorted(tiles_by_z.keys()):
                z_tiles = tiles_by_z[z]
                base_z = z
                chunks = self._chunk_tiles(z_tiles)
                for base_x, base_y, chunk_tiles in chunks:
                    tile_nodes = io.BytesIO()
                    for tile in chunk_tiles:
                        tile_bytes = self.tile_encoder.encode_tile_from_dict(
                            self._tile_to_dict(tile),
                            base_x=base_x,
                            base_y=base_y,
                        )
                        tile_nodes.write(tile_bytes)

                    tile_area = self.node.encode_tile_area(
                        base_x=base_x,
                        base_y=base_y,
                        base_z=base_z,
                        children=tile_nodes.getvalue(),
                    )
                    root_children.write(tile_area)

            # Spawns
            spawns = getattr(world_model, "spawns", []) or []
            if spawns:
                spawn_children = io.BytesIO()
                for spawn in spawns:
                    monster_name = self._get_spawn_name(spawn)
                    if not monster_name:
                        continue
                    sx = spawn.get("x", spawn.get("center_x", 0))
                    sy = spawn.get("y", spawn.get("center_y", 0))
                    sz = spawn.get("z", spawn.get("center_z", 0))
                    radius = spawn.get("radius", spawn.get("spawn_radius", 3))
                    interval = spawn.get(
                        "respawn", spawn.get("interval", spawn.get("spawntime", 60))
                    )
                    spawn_area_bytes = self.tile_encoder.encode_spawn_area_from_entry(
                        x=sx,
                        y=sy,
                        z=sz,
                        monster_name=monster_name,
                        interval=int(interval) if interval else 60,
                        radius=int(radius) if radius else 3,
                    )
                    spawn_children.write(spawn_area_bytes)

                for tile in tiles_list:
                    tile_spawn = self._get_spawn(tile)
                    tile_creature = self._get_creature(tile)
                    if tile_spawn or tile_creature:
                        name = ""
                        if tile_spawn and isinstance(tile_spawn, dict):
                            name = tile_spawn.get("monster", tile_spawn.get("name", ""))
                            interval = tile_spawn.get(
                                "respawn", tile_spawn.get("interval", 60)
                            )
                        elif tile_creature and isinstance(tile_creature, dict):
                            name = tile_creature.get("name", "")
                            interval = tile_creature.get("respawn", 60)
                        if name:
                            spawn_area_bytes = (
                                self.tile_encoder.encode_spawn_area_from_entry(
                                    x=self._get_x(tile),
                                    y=self._get_y(tile),
                                    z=self._get_z(tile),
                                    monster_name=name,
                                    interval=int(interval) if interval else 60,
                                    radius=3,
                                )
                            )
                            spawn_children.write(spawn_area_bytes)

                if spawn_children.getvalue():
                    spawns_node = self.node.encode_spawns(spawn_children.getvalue())
                    root_children.write(spawns_node)

            # Towns / Cities
            cities = getattr(world_model, "cities", []) or []
            if cities:
                towns_children = io.BytesIO()
                for idx, city in enumerate(cities, start=1):
                    town_bytes = self.node.encode_town(
                        town_id=idx,
                        name=str(city.get("name", f"Town{idx}")),
                        temple_x=int(city.get("temple_x", city.get("x", 0))),
                        temple_y=int(city.get("temple_y", city.get("y", 0))),
                        temple_z=int(city.get("temple_z", city.get("z", 0))),
                    )
                    towns_children.write(town_bytes)
                if towns_children.getvalue():
                    towns_node = self.node.encode_towns(towns_children.getvalue())
                    root_children.write(towns_node)

            # Waypoints
            waypoints = getattr(world_model, "waypoints", []) or []
            if waypoints:
                wp_children = io.BytesIO()
                for wp in waypoints:
                    wp_bytes = self.node.encode_waypoint(
                        name=str(wp.get("name", "waypoint")),
                        x=int(wp.get("x", 0)),
                        y=int(wp.get("y", 0)),
                        z=int(wp.get("z", 0)),
                    )
                    wp_children.write(wp_bytes)
                if wp_children.getvalue():
                    wp_node = self.node.encode_waypoints(wp_children.getvalue())
                    root_children.write(wp_node)

        root_node = self.node.encode_root(
            otbm_version=DEFAULT_OTBM_VERSION,
            width=width,
            height=height,
            item_major=DEFAULT_ITEM_MAJOR_VERSION,
            item_minor=DEFAULT_ITEM_MINOR_VERSION,
            children=root_children.getvalue(),
        )

        return self.OTBM_MAGIC + root_node

        # ------------------------------------------------------------------
        # v1.0.1 HOTFIX: per-z tile chunking
        return self.OTBM_MAGIC + root_node

    # ------------------------------------------------------------------
    # v1.0.1 HOTFIX: per-z tile chunking
    # ------------------------------------------------------------------

    def _chunk_tiles(self, tiles: List[Any]) -> List[Tuple[int, int, List[Any]]]:
        """
        Group tiles into TILE_AREA-sized chunks (v1.0.1 HOTFIX).

        Two safety limits apply per chunk:
          * byte budget  (MAX_TILE_AREA_PAYLOAD)
          * tile count   (MAX_TILE_AREA_TILES)

        When either limit is reached, the current chunk is closed and a new
        one is started with a fresh base coordinate equal to the first tile
        of the new chunk. This guarantees each TILE_AREA node stays well
        below the OTBM uint16 payload limit.
        """
        if not tiles:
            return []

        chunks: List[Tuple[int, int, List[Any]]] = []
        current: List[Any] = []
        current_bytes = 0
        current_base_x: Optional[int] = None
        current_base_y: Optional[int] = None

        def _flush() -> None:
            nonlocal current, current_bytes, current_base_x, current_base_y
            if current and current_base_x is not None and current_base_y is not None:
                chunks.append((current_base_x, current_base_y, current))
            current = []
            current_bytes = 0
            current_base_x = None
            current_base_y = None

        # Deterministic ordering.
        ordered = sorted(tiles, key=lambda t: (self._get_x(t), self._get_y(t)))

        # Always start a new TILE_AREA every MAX_TILE_AREA_TILES tiles
        # AND/OR when the byte budget is exceeded. The base coordinate
        # of each chunk is the first tile inside the chunk.
        for tile in ordered:
            tx = self._get_x(tile)
            ty = self._get_y(tile)

            if current_base_x is None or current_base_y is None:
                current_base_x = tx
                current_base_y = ty

            tile_bytes = self.tile_encoder.encode_tile_from_dict(
                self._tile_to_dict(tile),
                base_x=current_base_x,
                base_y=current_base_y,
            )
            tile_len = len(tile_bytes)

            over_bytes = (current_bytes + tile_len) > MAX_TILE_AREA_PAYLOAD
            over_tiles = len(current) >= MAX_TILE_AREA_TILES

            if (over_bytes or over_tiles) and current:
                _flush()
                current_base_x = tx
                current_base_y = ty
                tile_bytes = self.tile_encoder.encode_tile_from_dict(
                    self._tile_to_dict(tile),
                    base_x=current_base_x,
                    base_y=current_base_y,
                )
                tile_len = len(tile_bytes)

            current.append(tile)
            current_bytes += tile_len

        _flush()
        return chunks

    # ------------------------------------------------------------------
    # Deserialize
    # ------------------------------------------------------------------

    def deserialize(self, data: bytes) -> Dict[str, Any]:
        if not data or len(data) < 4:
            raise ValueError("Truncated OTBM data: too short for magic")
        if data[:4] != self.OTBM_MAGIC:
            raise ValueError("Invalid OTBM magic identifier")

        offset = 4
        result = {"tiles": [], "spawns": [], "towns": [], "waypoints": []}

        if offset >= len(data):
            raise ValueError("Truncated data: no root node type byte")
        node_type = data[offset]
        offset += 1
        if node_type != OTBM_NODE_ROOT:
            raise ValueError(f"Expected ROOT node (0x00), got 0x{node_type:02X}")

        end_root = len(data)
        version = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        width = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        height = struct.unpack_from("<H", data, offset)[0]
        offset += 2
        item_major = struct.unpack_from("<I", data, offset)[0]
        offset += 4
        item_minor = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        result["version"] = version
        result["width"] = width
        result["height"] = height
        result["item_version"] = (item_major, item_minor)

        while offset < end_root:
            offset = self._deserialize_node(data, offset, result)

        return result

    def _deserialize_node(self, data: bytes, offset: int, result: dict) -> int:
        node_type, size, offset = self.node.read_node_header(data, offset)
        end_node = offset + size

        if node_type == OTBM_NODE_MAP_DATA:
            desc, offset = self.node.read_string(data, offset)
            spawn_file, offset = self.node.read_string(data, offset)
            house_file, offset = self.node.read_string(data, offset)
            result["description"] = desc
            result["spawn_file"] = spawn_file
            result["house_file"] = house_file
            while offset < end_node:
                offset = self._deserialize_node(data, offset, result)

        elif node_type == OTBM_NODE_TILE_AREA:
            base_x = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            base_y = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            base_z = data[offset]
            offset += 1
            while offset < end_node:
                offset = self._deserialize_tile(
                    data, offset, result, base_x, base_y, base_z
                )

        elif node_type == OTBM_NODE_SPAWNS:
            while offset < end_node:
                offset = self._deserialize_node(data, offset, result)

        elif node_type == OTBM_NODE_SPAWN_AREA:
            center_x = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            center_y = struct.unpack_from("<H", data, offset)[0]
            offset += 2
            center_z = data[offset]
            offset += 1
            radius = data[offset]
            offset += 1
            spawn_entry = {
                "center_x": center_x,
                "center_y": center_y,
                "center_z": center_z,
                "radius": radius,
                "monsters": [],
            }
            while offset < end_node:
                offset = self._deserialize_monster(data, offset, spawn_entry)
            result["spawns"].append(spawn_entry)

        elif node_type == OTBM_NODE_TOWNS:
            while offset < end_node:
                node_t, sz, offset = self.node.read_node_header(data, offset)
                end_town = offset + sz
                if node_t == OTBM_NODE_TOWN:
                    town_id = struct.unpack_from("<I", data, offset)[0]
                    offset += 4
                    town_name, offset = self.node.read_string(data, offset)
                    temple_x = struct.unpack_from("<H", data, offset)[0]
                    offset += 2
                    temple_y = struct.unpack_from("<H", data, offset)[0]
                    offset += 2
                    temple_z = data[offset]
                    offset += 1
                    result["towns"].append(
                        {
                            "town_id": town_id,
                            "name": town_name,
                            "temple_x": temple_x,
                            "temple_y": temple_y,
                            "temple_z": temple_z,
                        }
                    )
                offset = end_town

        elif node_type == OTBM_NODE_WAYPOINTS:
            while offset < end_node:
                node_t, sz, offset = self.node.read_node_header(data, offset)
                end_wp = offset + sz
                if node_t == OTBM_NODE_WAYPOINT:
                    wp_name, offset = self.node.read_string(data, offset)
                    wp_x = struct.unpack_from("<H", data, offset)[0]
                    offset += 2
                    wp_y = struct.unpack_from("<H", data, offset)[0]
                    offset += 2
                    wp_z = data[offset]
                    offset += 1
                    result["waypoints"].append(
                        {
                            "name": wp_name,
                            "x": wp_x,
                            "y": wp_y,
                            "z": wp_z,
                        }
                    )
                offset = end_wp

        return end_node

    def _deserialize_tile(
        self,
        data: bytes,
        offset: int,
        result: dict,
        base_x: int,
        base_y: int,
        base_z: int,
    ) -> int:
        node_type, size, offset = self.node.read_node_header(data, offset)
        if node_type != OTBM_NODE_TILE:
            return offset + size

        end_tile = offset + size
        off_x = data[offset]
        offset += 1
        off_y = data[offset]
        offset += 1

        abs_x = base_x + off_x
        abs_y = base_y + off_y
        flags = 0

        if offset < end_tile and data[offset] == ATTR_TILE_FLAGS:
            offset += 1
            flags = struct.unpack_from("<I", data, offset)[0]
            offset += 4

        items = []
        while offset < end_tile:
            offset = self._deserialize_item(data, offset, items)

        result["tiles"].append(
            {
                "x": abs_x,
                "y": abs_y,
                "z": base_z,
                "flags": flags,
                "items": items,
            }
        )
        return end_tile

    def _deserialize_item(self, data: bytes, offset: int, items: list) -> int:
        if offset >= len(data):
            return offset

        node_type, size, offset = self.node.read_node_header(data, offset)
        if node_type != OTBM_NODE_ITEM:
            return offset + size

        end_item = offset + size
        item_id = struct.unpack_from("<H", data, offset)[0]
        offset += 2

        item = {"id": item_id}
        while offset < end_item:
            if offset >= len(data):
                break
            attr = data[offset]
            offset += 1

            if attr == ATTR_COUNT or attr == ATTR_SUBTYPE or attr == ATTR_CHARGES:
                item[
                    (
                        "count"
                        if attr == ATTR_COUNT
                        else ("subtype" if attr == ATTR_SUBTYPE else "charges")
                    )
                ] = data[offset]
                offset += 1
            elif attr == ATTR_ACTION_ID or attr == ATTR_UNIQUE_ID:
                item["action_id" if attr == ATTR_ACTION_ID else "unique_id"] = (
                    struct.unpack_from("<H", data, offset)[0]
                )
                offset += 2
            elif attr == ATTR_TEXT:
                text, offset = self.node.read_string(data, offset)
                item["text"] = text
            elif attr == ATTR_DURATION:
                item["duration"] = struct.unpack_from("<I", data, offset)[0]
                offset += 4
            elif attr == ATTR_DECAYING_STATE:
                item["decaying_state"] = data[offset]
                offset += 1
            else:
                break

        items.append(item)
        return end_item

    def _deserialize_monster(self, data: bytes, offset: int, spawn_entry: dict) -> int:
        node_type, size, offset = self.node.read_node_header(data, offset)
        if node_type != OTBM_NODE_MONSTER:
            return offset + size

        end_monster = offset + size
        name, offset = self.node.read_string(data, offset)
        direction = data[offset]
        offset += 1
        spawntime = struct.unpack_from("<I", data, offset)[0]
        offset += 4

        spawn_entry["monsters"].append(
            {
                "name": name,
                "direction": direction,
                "spawntime": spawntime,
            }
        )
        return end_monster

    @staticmethod
    def _tile_to_dict(tile: Any) -> Dict[str, Any]:
        if isinstance(tile, dict):
            return tile
        if hasattr(tile, "to_dict"):
            return tile.to_dict()
        return {
            "x": getattr(tile, "x", 0),
            "y": getattr(tile, "y", 0),
            "z": getattr(tile, "z", 0),
            "ground": getattr(tile, "ground", 106),
            "items": getattr(tile, "items", []),
            "spawn": getattr(tile, "spawn", None),
            "creature": getattr(tile, "creature", None),
            "flags": getattr(tile, "flags", 0),
        }

    @staticmethod
    def _get_x(tile: Any) -> int:
        if isinstance(tile, dict):
            return int(tile.get("x", 0))
        return int(getattr(tile, "x", 0))

    @staticmethod
    def _get_y(tile: Any) -> int:
        if isinstance(tile, dict):
            return int(tile.get("y", 0))
        return int(getattr(tile, "y", 0))

    @staticmethod
    def _get_z(tile: Any) -> int:
        if isinstance(tile, dict):
            return int(tile.get("z", 0))
        return int(getattr(tile, "z", 0))

    @staticmethod
    def _get_spawn(tile: Any) -> Optional[Dict]:
        if isinstance(tile, dict):
            return tile.get("spawn")
        return getattr(tile, "spawn", None)

    @staticmethod
    def _get_creature(tile: Any) -> Optional[Dict]:
        if isinstance(tile, dict):
            return tile.get("creature")
        return getattr(tile, "creature", None)

    @staticmethod
    def _get_spawn_name(spawn: Dict) -> str:
        if isinstance(spawn, dict):
            return str(
                spawn.get("monster", "")
                or spawn.get("name", "")
                or spawn.get("creature", "")
            )
        return ""

    def _get_attr(self, obj, name, default=None):
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def serialize_hunt_area(self, hunt_area, spawn_plan=None) -> bytes:
        tiles_raw = self._get_attr(hunt_area, "tiles", {})
        if isinstance(tiles_raw, dict):
            tiles_list = []
            for _k, _v in tiles_raw.items():
                if isinstance(_v, dict):
                    tiles_list.append(_v)
                else:
                    tiles_list.append(_v)
        else:
            tiles_list = list(tiles_raw)
        spawns_raw = self._get_attr(hunt_area, "spawns", []) or []

        base_x_val = self._get_attr(hunt_area, "base_x", 1000)
        base_y_val = self._get_attr(hunt_area, "base_y", 1000)
        base_z_val = self._get_attr(hunt_area, "base_z", 7)

        all_x = []
        all_y = []
        all_z = []
        for t in tiles_list:
            tx = self._get_attr(t, "x", base_x_val)
            ty = self._get_attr(t, "y", base_y_val)
            tz = (
                self._get_attr(t, "z", base_z_val)
                if (isinstance(t, dict) and "z" in t)
                else getattr(t, "z", base_z_val)
            )
            all_x.append(tx)
            all_y.append(ty)
            all_z.append(tz)

        if not all_x:
            all_x = [base_x_val]
            all_y = [base_y_val]
            all_z = [base_z_val]

        width = max(all_x) - min(all_x) + 1
        height = max(all_y) - min(all_y) + 1

        root_children = io.BytesIO()
        map_children = io.BytesIO()

        base_x = min(all_x)
        base_y = min(all_y)
        base_z = base_z_val

        tile_nodes = io.BytesIO()
        for tile in tiles_list:
            tile_bytes = self.tile_encoder.encode_tile_from_huntarea(
                tile, base_x=base_x, base_y=base_y
            )
            tile_nodes.write(tile_bytes)

        tile_area = self.node.encode_tile_area(
            base_x=base_x,
            base_y=base_y,
            base_z=base_z,
            children=tile_nodes.getvalue(),
        )
        map_children.write(tile_area)

        spawn_entries = []
        for s in spawns_raw:
            if len(s) >= 3:
                spawn_entries.append(
                    {
                        "x": s[0],
                        "y": s[1],
                        "monster": s[2],
                        "interval": s[3] if len(s) > 3 else 60,
                    }
                )

        if spawn_plan:
            for entry in getattr(spawn_plan, "spawns", []):
                spawn_entries.append(
                    {
                        "x": entry.x,
                        "y": entry.y,
                        "z": entry.z if hasattr(entry, "z") else base_z,
                        "monster": entry.monster_name,
                        "interval": getattr(entry, "interval", 60),
                    }
                )
            boss = getattr(spawn_plan, "boss_spawn", None)
            if boss:
                spawn_entries.append(
                    {
                        "x": boss.x,
                        "y": boss.y,
                        "z": boss.z if hasattr(boss, "z") else base_z,
                        "monster": boss.monster_name,
                        "interval": getattr(boss, "interval", 600),
                    }
                )

        if spawn_entries:
            spawn_children = io.BytesIO()
            for entry in spawn_entries:
                spawn_area_bytes = self.tile_encoder.encode_spawn_area_from_entry(
                    x=int(entry["x"]),
                    y=int(entry["y"]),
                    z=int(entry.get("z", base_z)),
                    monster_name=str(entry["monster"]),
                    interval=int(entry.get("interval", 60)),
                    radius=3,
                )
                spawn_children.write(spawn_area_bytes)

            if spawn_children.getvalue():
                spawns_node = self.node.encode_spawns(spawn_children.getvalue())
                map_children.write(spawns_node)

        map_data = self.node.encode_map_data(
            description="Generated by OpenTibiaBR RME Agent — Hunt Area",
            spawn_file="",
            house_file="",
            children=map_children.getvalue(),
        )
        root_children.write(map_data)

        root_node = self.node.encode_root(
            otbm_version=DEFAULT_OTBM_VERSION,
            width=width,
            height=height,
            item_major=DEFAULT_ITEM_MAJOR_VERSION,
            item_minor=DEFAULT_ITEM_MINOR_VERSION,
            children=root_children.getvalue(),
        )

        return self.OTBM_MAGIC + root_node
