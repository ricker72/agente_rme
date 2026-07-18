from __future__ import annotations

import struct

from .attributes import encode_supported_attributes
from .model import OtbmItem
from .nodes import OtbmNode

NODE_ITEM = 0x06


def encode_item_payload(item: OtbmItem) -> bytes:
    return struct.pack("<H", item.item_id) + encode_supported_attributes(item.attributes)


def item_to_node(item: OtbmItem) -> OtbmNode:
    return OtbmNode(
        node_type=NODE_ITEM,
        attributes=encode_item_payload(item),
        children=tuple(item_to_node(child) for child in item.children),
    )
