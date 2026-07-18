from __future__ import annotations

import struct

from .attributes import encode_supported_attributes
from .item_encoder import item_to_node
from .model import OtbmTile
from .nodes import OtbmNode

NODE_TILE = 0x05
NODE_HOUSE_TILE = 0x0E


def tile_to_node(tile: OtbmTile, base_x: int, base_y: int) -> OtbmNode:
    offset_x = tile.x - base_x
    offset_y = tile.y - base_y
    if not (0 <= offset_x <= 255 and 0 <= offset_y <= 255):
        raise ValueError(f"tile outside OTBM area chunk: {tile.x},{tile.y},{tile.z}")
    attributes = struct.pack("<BB", offset_x, offset_y)
    node_type = NODE_TILE
    if tile.house_id is not None:
        if not 0 < int(tile.house_id) <= 0xFFFFFFFF:
            raise ValueError(f"invalid house id: {tile.house_id}")
        node_type = NODE_HOUSE_TILE
        attributes += struct.pack("<I", int(tile.house_id))
    attributes += encode_supported_attributes(tile.attributes)
    return OtbmNode(
        node_type=node_type,
        attributes=attributes,
        children=tuple(item_to_node(item) for item in tile.items),
    )
