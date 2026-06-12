from __future__ import annotations

import io
import logging
from typing import Any, Dict, Optional

from .node_encoder import NodeEncoder, TILESTATE_PROTECTIONZONE
from .binary_writer import BinaryWriter

logger = logging.getLogger(__name__)


# Known ground-item ID map for common themes
GROUND_IDS: Dict[str, int] = {
    # Issavi / magical
    "issavi_ground": 113,
    "serpent_ground": 113,
    "magic_ground": 406,
    "crystal_floor": 406,
    "glowing_floor": 408,
    "elite_floor": 407,
    # Yalahar / exotic
    "yalahar_ground": 116,
    "exotic_ground": 116,
    "tropical_ground": 110,
    # Ice / Roshamuul
    "ice_ground": 670,
    "snow_ground": 670,
    "frozen_ground": 671,
    "roshamuul_ground": 672,
    "dark_ground": 319,
    # Jungle
    "jungle_ground": 108,
    "grass_ground": 106,
    "earth_ground": 104,
    # Dungeon
    "stone_floor": 319,
    "cave_floor": 110,
    "mountain_floor": 114,
    "dungeon_floor": 110,
    # Temple / City
    "city_floor": 112,
    "temple_floor": 405,
    "marble_floor": 405,
    # Water / Lava
    "water": 4820,
    "lava": 5815,
}

WALL_IDS: Dict[str, int] = {
    "stone_wall": 159,
    "brick_wall": 165,
    "ice_wall": 675,
    "crystal_wall": 409,
    "jungle_wall": 163,
    "cave_wall": 313,
    "mountain_wall": 154,
    "temple_wall": 402,
    "dark_wall": 321,
    "magic_wall": 353,
}

DECORATION_IDS: Dict[str, int] = {
    "torch": 2050,
    "crystal_torch": 2054,
    "blood": 2016,
    "bones": 2225,
    "skull": 2229,
    "glow": 2162,
    "crystal": 2162,
    "rubble": 2117,
    "statue": 1469,
}


class TileEncoder:
    """
    Encodes a tile (from WorldModel or HuntArea) into OTBM binary format.

    Handles:
      - x, y, z
      - ground item
      - decorative / wall items
      - tile flags (PZ, protection)
      - house tiles
      - spawn references
      - creature / NPC placement
    """

    def __init__(self):
        self.node = NodeEncoder()
        self._bw = BinaryWriter()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def encode_tile_from_dict(
        self,
        tile_data: Dict[str, Any],
        base_x: int = 0,
        base_y: int = 0,
    ) -> bytes:
        """
        Encode a tile from a dict (WorldModel-style tile).

        Args:
            tile_data: dict with keys x, y, z, ground, items, spawn, creature
            base_x: tile-area base X (for relative offset)
            base_y: tile-area base Y (for relative offset)

        Returns:
            bytes: Encoded TILE node
        """
        x = int(tile_data.get("x", 0))
        y = int(tile_data.get("y", 0))
        int(tile_data.get("z", 0))

        # Compute offset relative to TILE_AREA base, normalising to [0, 255].
        offset_x = self._normalize_offset(x - base_x, "offset_x", tile_data)
        offset_y = self._normalize_offset(y - base_y, "offset_y", tile_data)

        ground_id = self._resolve_ground(tile_data.get("ground", 0))
        items = tile_data.get("items", []) or []
        flags = tile_data.get("flags", 0)

        # Build item children
        children = io.BytesIO()

        # Ground item always present
        children.write(self.node.encode_item(item_id=ground_id))

        # Additional items
        for item in items:
            item_id = self._resolve_item_id(item)
            count = item.get("count") if isinstance(item, dict) else None
            action_id = item.get("action_id") if isinstance(item, dict) else None
            unique_id = item.get("unique_id") if isinstance(item, dict) else None
            text = item.get("text") if isinstance(item, dict) else None
            children.write(
                self.node.encode_item(
                    item_id=item_id,
                    count=count,
                    action_id=action_id,
                    unique_id=unique_id,
                    text=text,
                )
            )

        return self.node.encode_tile(
            offset_x=offset_x,
            offset_y=offset_y,
            tile_flags=flags,
            children=children.getvalue(),
        )

    def encode_tile_from_huntarea(
        self,
        tile,
        base_x: int = 0,
        base_y: int = 0,
    ) -> bytes:
        """
        Encode a HuntArea TileInfo into OTBM.

        Args:
            tile: TileInfo dataclass with x, y, z, ground_id, items, tile_type
            base_x: tile-area base X
            base_y: tile-area base Y

        Returns:
            bytes: Encoded TILE node
        """
        offset_x = self._normalize_offset(
            tile.x - base_x, "offset_x", getattr(tile, "__dict__", {})
        )
        offset_y = self._normalize_offset(
            tile.y - base_y, "offset_y", getattr(tile, "__dict__", {})
        )

        flags = 0
        tile_type = getattr(tile, "tile_type", None)
        if tile_type and str(tile_type).upper() in (
            "PROTECTIONZONE",
            "PZ",
            "TEMPLE",
        ):
            flags |= TILESTATE_PROTECTIONZONE

        ground_id = self._resolve_ground_id(getattr(tile, "ground_id", 0))

        children = io.BytesIO()
        # Ground item
        children.write(self.node.encode_item(item_id=ground_id))

        # Additional items on the tile
        for item in getattr(tile, "items", []) or []:
            item_id = self._resolve_item_id(item)
            children.write(self.node.encode_item(item_id=item_id))

        return self.node.encode_tile(
            offset_x=offset_x,
            offset_y=offset_y,
            tile_flags=flags,
            children=children.getvalue(),
        )

    def encode_house_tile(
        self,
        offset_x: int,
        offset_y: int,
        house_id: int,
        ground_id: int = 112,
    ) -> bytes:
        """
        Encode a house tile (HOUSETILE node).
        Houses use a special node type so RME can re-serialize them.
        """
        # Normalise values into safe ranges.
        offset_x = self._normalize_offset(offset_x, "house.offset_x")
        offset_y = self._normalize_offset(offset_y, "house.offset_y")
        # house_id is a uint32, so we clamp to [0, 2**32-1].
        if house_id is None:
            house_id = 0
        try:
            house_id = int(house_id)
        except (TypeError, ValueError):
            house_id = 0
        if house_id < 0:
            house_id = 0
        if house_id > 0xFFFFFFFF:
            logger.warning("house_id %d exceeds uint32, clamped", house_id)
            house_id = 0xFFFFFFFF

        children = io.BytesIO()
        children.write(self.node.encode_item(item_id=ground_id))
        return self.node.encode_house_tile(
            offset_x=offset_x,
            offset_y=offset_y,
            house_id=house_id,
            children=children.getvalue(),
        )

    def encode_spawn_area_from_entry(
        self,
        x: int,
        y: int,
        z: int,
        monster_name: str,
        interval: int = 60,
        radius: int = 3,
    ) -> bytes:
        """
        Encode a single spawn entry as SPAWN_AREA + MONSTER.
        """
        # All inputs are normalised via BinaryWriter which uses safe
        # clamping, so this never raises a struct.error.
        monster_node = self.node.encode_monster(
            name=monster_name,
            direction=2,  # South (default)
            spawntime=interval,
        )
        return self.node.encode_spawn_area(
            center_x=x,
            center_y=y,
            center_z=z,
            radius=radius,
            children=monster_node,
        )

    # ------------------------------------------------------------------
    # ID resolution
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_ground(ground_value: Any) -> int:
        """Resolve a ground descriptor to an item ID."""
        try:
            return int(ground_value)
        except (TypeError, ValueError):
            pass
        if isinstance(ground_value, str):
            lower = ground_value.lower().replace(" ", "_").replace("-", "_")
            if lower in GROUND_IDS:
                return GROUND_IDS[lower]
            # Partial match
            for key, val in GROUND_IDS.items():
                if key in lower or lower in key:
                    return val
        return 106  # default grass

    @staticmethod
    def _resolve_ground_id(raw: Any) -> int:
        """Same as _resolve_ground but takes int/str directly."""
        try:
            return int(raw)
        except (TypeError, ValueError):
            pass
        if isinstance(raw, str):
            lower = raw.lower().replace(" ", "_").replace("-", "_")
            for key, val in GROUND_IDS.items():
                if key in lower or lower in key:
                    return val
        return 106

    @staticmethod
    def _resolve_item_id(item: Any) -> int:
        """Resolve an item descriptor to an item ID."""
        if isinstance(item, (int, float)):
            return int(item)
        if isinstance(item, dict):
            # Dict with 'id' key
            if "id" in item:
                try:
                    return int(item["id"])
                except (TypeError, ValueError):
                    pass
            # Dict with 'name' key — look up in our tables
            if "name" in item:
                name = str(item["name"]).lower().replace(" ", "_").replace("-", "_")
                if name in WALL_IDS:
                    return WALL_IDS[name]
                if name in DECORATION_IDS:
                    return DECORATION_IDS[name]
                if name in GROUND_IDS:
                    return GROUND_IDS[name]
                # Partial match
                for d in (WALL_IDS, DECORATION_IDS, GROUND_IDS):
                    for key, val in d.items():
                        if key in name or name in key:
                            return val
            return 0
        if isinstance(item, str):
            lower = item.lower().replace(" ", "_").replace("-", "_")
            for d in (WALL_IDS, DECORATION_IDS, GROUND_IDS):
                for key, val in d.items():
                    if key in lower or lower in key:
                        return val
        return 0

    @staticmethod
    def _normalize_offset(
        value: Any, context: str, source: Optional[dict] = None
    ) -> int:
        """Clamp an offset to the [0, 255] uint8 range used by OTBM tiles.

        When the resulting offset would be negative or > 255, the value
        is clamped and a warning is logged. The function never raises.
        """
        try:
            iv = int(value) if value is not None else 0
        except (TypeError, ValueError):
            logger.warning("TileEncoder.%s non-integer %r, using 0", context, value)
            return 0
        if iv < 0 or iv > 255:
            clamped = max(0, min(255, iv))
            logger.warning(
                "TileEncoder.%s offset %d out of [0,255] (source=%s), clamped to %d",
                context,
                iv,
                context,
                clamped,
            )
            return clamped
        return iv
