"""
Item Decoder — converts decoded OTBM ITEM nodes into structured Item objects.

Transforms the raw decoded item dicts from NodeDecoder into a format
suitable for use in the WorldModel (Tile.items list).

Decodes item attributes like:
    - count/subtype (stack count, fluid type)
    - action_id / unique_id
    - text / description
    - charges / duration / decaying_state
"""

from __future__ import annotations

from typing import Any, Dict, List

from .node_encoder import (
    ATTR_COUNT,
    ATTR_ACTION_ID,
    ATTR_UNIQUE_ID,
    ATTR_TEXT,
    ATTR_DESC,
    ATTR_DURATION,
    ATTR_DECAYING_STATE,
    ATTR_WRITTEN_DATE,
    ATTR_WRITTEN_BY,
    ATTR_SLEEPERGUID,
    ATTR_SLEEPSTART,
    ATTR_CHARGES,
    ATTR_SUBTYPE,
    ATTR_EXT_FILE,
)


class ItemDecoder:
    """
    Decodes OTBM item data into structured dicts suitable for WorldModel tiles.

    Input: raw decoded item dict from NodeDecoder.decode_item()
        {
            "item_id": int,
            "attributes": {attr_type: value, ...},
            "children": [nested items...]
        }

    Output: clean item dict
        {
            "item_id": int,
            "count": int or None,
            "subtype": int or None,
            "action_id": int or None,
            "unique_id": int or None,
            "text": str or None,
            "description": str or None,
            "charges": int or None,
            "duration": int or None,
            "decaying_state": int or None,
            "written_date": int or None,
            "written_by": str or None,
            "sleeper_guid": int or None,
            "sleeper_start": int or None,
            "ext_file": str or None,
            "children": [nested items...],
        }
    """

    def decode(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decode a single OTBM item into a structured dict.

        Args:
            item_data: Raw decoded item dict from NodeDecoder.

        Returns:
            Clean item dict with all attributes decoded.
        """
        item_id = item_data.get("item_id", 0)
        attrs = item_data.get("attributes", {})
        children = item_data.get("children", [])

        # Decode children recursively
        decoded_children = [self.decode(c) for c in children]

        return {
            "item_id": item_id,
            "count": attrs.get(ATTR_COUNT),
            "subtype": attrs.get(ATTR_SUBTYPE),
            "action_id": attrs.get(ATTR_ACTION_ID),
            "unique_id": attrs.get(ATTR_UNIQUE_ID),
            "text": attrs.get(ATTR_TEXT),
            "description": attrs.get(ATTR_DESC),
            "charges": attrs.get(ATTR_CHARGES),
            "duration": attrs.get(ATTR_DURATION),
            "decaying_state": attrs.get(ATTR_DECAYING_STATE),
            "written_date": attrs.get(ATTR_WRITTEN_DATE),
            "written_by": attrs.get(ATTR_WRITTEN_BY),
            "sleeper_guid": attrs.get(ATTR_SLEEPERGUID),
            "sleeper_start": attrs.get(ATTR_SLEEPSTART),
            "ext_file": attrs.get(ATTR_EXT_FILE),
            "children": decoded_children,
        }

    def decode_ground(self, item_data: Dict[str, Any]) -> int:
        """
        Extract just the ground item ID from an item dict.

        Args:
            item_data: Decoded item dict.

        Returns:
            Ground item ID (integer).
        """
        return item_data.get("item_id", 0)

    def decode_item_list(
        self, items_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Decode a list of OTBM items.

        Args:
            items_data: List of raw decoded item dicts.

        Returns:
            List of clean item dicts.
        """
        return [self.decode(item) for item in items_data]

    def item_to_tile_format(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a decoded item into the format expected by WorldModel Tile.items.

        WorldModel Tile uses format:
            {"id": item_id, "count": ..., "action_id": ...}

        Returns:
            Dict matching Tile.items element format.
        """
        decoded = self.decode(item_data)
        result: Dict[str, Any] = {"id": decoded["item_id"]}

        if decoded["count"] is not None:
            result["count"] = decoded["count"]
        if decoded["action_id"] is not None:
            result["action_id"] = decoded["action_id"]
        if decoded["unique_id"] is not None:
            result["unique_id"] = decoded["unique_id"]
        if decoded["text"] is not None:
            result["text"] = decoded["text"]
        if decoded["charges"] is not None:
            result["charges"] = decoded["charges"]
        if decoded["subtype"] is not None:
            result["subtype"] = decoded["subtype"]
        if decoded["duration"] is not None:
            result["duration"] = decoded["duration"]

        return result

    def is_ground(self, item_id: int) -> bool:
        """
        Check if an item ID is likely a ground tile.

        Ground tiles in Tibia are typically in ranges:
            100-799 (classic grounds)
            800-999 (extended)
            4000-5999 (additional)
            6000-7999 (OTClient grounds)

        Args:
            item_id: Item ID to check.

        Returns:
            True if the item ID is in a typical ground range.
        """
        return (
            (100 <= item_id <= 999)
            or (4000 <= item_id <= 5999)
            or (6000 <= item_id <= 7999)
            or item_id in (0, 106, 110, 112, 113, 114, 116, 319, 405, 406, 407, 408)
        )
