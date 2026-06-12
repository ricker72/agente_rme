"""
Tile Decoder — converts decoded OTBM TILE/TILE_AREA nodes into WorldModel Tile objects.

Pipeline:
    OtbmParser.parse(data) -> raw nodes
    NodeDecoder.decode_tile_area(node) -> decoded tile area dicts
    TileDecoder.to_worldmodel_tile(decoded_tile) -> WorldModel Tile dataclass

Handles:
    - Normal tiles (TILE node type)
    - House tiles (HOUSETILE node type)
    - Tile flags (PZ, PVP, no-logout, etc.)
    - Ground items -> Tile.ground (as string ID)
    - Additional items -> Tile.items (as dicts with id, count, etc.)
"""

from __future__ import annotations

from typing import Any, Dict, List

from .node_encoder import (
    TILESTATE_NONE,
    TILESTATE_PROTECTIONZONE,
    TILESTATE_NOPVPZONE,
    TILESTATE_NOLOGOUT,
    TILESTATE_PVPZONE,
    TILESTATE_REFRESH,
    TILESTATE_TRASHED,
)
from .item_decoder import ItemDecoder


class TileDecoder:
    """
    Decodes parsed OTBM tile data into WorldModel-compatible Tile objects.

    Input: decoded tile dicts from NodeDecoder
        {
            "x": int, "y": int, "z": int,
            "flags": int,
            "ground": {"item_id": int, "attributes": {...}},
            "items": [{"item_id": int, "attributes": {...}}, ...],
            "all_items": [all items including ground, ...],
            "is_house": bool (optional),
            "house_id": int (optional),
        }

    Output: dict suitable for WorldModel Tile creation
        {
            "x": int, "y": int, "z": int,
            "ground": str(item_id),
            "items": [{"id": item_id, "count": ..., ...}, ...],
            "flags": int,
            "spawn": None or {"monster": str, "respawn": int, ...},
            "creature": None,
        }
    """

    # Known wall item IDs (for decoration categorization)
    WALL_ITEM_IDS = {
        154,
        155,
        156,
        157,
        158,
        159,
        160,
        161,
        162,
        163,
        164,
        165,
        166,
        167,
        168,
        169,
        170,
        313,
        314,
        315,
        316,
        317,
        318,
        319,
        320,
        321,
        322,
        323,
        353,
        354,
        355,
        356,
        357,
        358,
        359,
        360,
        361,
        362,
        363,
        364,
        365,
        366,
        367,
        368,
        369,
        370,
        371,
        372,
        373,
        374,
        375,
        376,
        402,
        403,
        404,
        409,
        410,
        411,
        412,
        413,
        414,
        415,
        416,
        417,
        418,
        419,
        420,
        421,
        422,
        423,
        424,
        425,
        426,
        427,
        428,
        429,
        430,
        431,
        432,
        433,
        434,
        435,
        436,
        437,
        438,
        439,
        440,
        441,
        442,
        443,
        444,
        445,
        446,
        447,
        448,
        449,
        450,
        451,
        452,
        453,
        454,
        455,
        456,
        457,
        458,
        459,
        460,
        461,
        462,
        463,
        464,
        465,
        466,
        467,
        468,
        469,
        470,
    }

    def __init__(self):
        self._item_decoder = ItemDecoder()

    def to_worldmodel_tile(self, decoded_tile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a decoded OTBM tile into WorldModel-compatible format.

        Args:
            decoded_tile: Decoded tile dict from NodeDecoder.

        Returns:
            Dict compatible with WorldModel Tile creation.
        """
        x = decoded_tile.get("x", 0)
        y = decoded_tile.get("y", 0)
        z = decoded_tile.get("z", 0)
        flags = decoded_tile.get("flags", TILESTATE_NONE)
        is_house = decoded_tile.get("is_house", False)

        # Decode ground
        ground_data = decoded_tile.get("ground")
        ground_id = 0
        if ground_data:
            ground_id = self._item_decoder.decode_ground(ground_data)

        # Decode additional items
        items_data = decoded_tile.get("items", [])
        items = [self._item_decoder.item_to_tile_format(it) for it in items_data]

        # Build result
        result: Dict[str, Any] = {
            "x": x,
            "y": y,
            "z": z,
            "ground": str(ground_id) if ground_id else "0",
            "items": items,
            "flags": flags,
            "spawn": None,
            "creature": None,
        }

        if is_house:
            result["house_id"] = decoded_tile.get("house_id", 0)

        return result

    def decode_area(self, area_decoded: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Decode all tiles in a TILE_AREA.

        Args:
            area_decoded: Decoded tile area dict from NodeDecoder.

        Returns:
            List of WorldModel-compatible tile dicts.
        """
        return [self.to_worldmodel_tile(tile) for tile in area_decoded.get("tiles", [])]

    def flags_to_strings(self, flags: int) -> List[str]:
        """
        Convert tile flags bitmask to list of string descriptions.

        Args:
            flags: Tile flags bitmask.

        Returns:
            List of flag names like ["PROTECTIONZONE", "NOPVP"].
        """
        result = []
        if flags & TILESTATE_PROTECTIONZONE:
            result.append("PROTECTIONZONE")
        if flags & TILESTATE_NOPVPZONE:
            result.append("NOPVPZONE")
        if flags & TILESTATE_NOLOGOUT:
            result.append("NOLOGOUT")
        if flags & TILESTATE_PVPZONE:
            result.append("PVPZONE")
        if flags & TILESTATE_REFRESH:
            result.append("REFRESH")
        if flags & TILESTATE_TRASHED:
            result.append("TRASHED")
        return result

    def is_ground_item(self, item_id: int) -> bool:
        """
        Check if an item ID is a ground tile.

        Delegates to ItemDecoder.is_ground.
        """
        return self._item_decoder.is_ground(item_id)

    def is_wall_item(self, item_id: int) -> bool:
        """
        Check if an item ID is a wall/border item.

        Args:
            item_id: Item ID to check.

        Returns:
            True if the item ID is a known wall item.
        """
        return item_id in self.WALL_ITEM_IDS
