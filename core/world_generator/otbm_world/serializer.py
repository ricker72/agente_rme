from __future__ import annotations

from .escape import NODE_END, NODE_START, escape_otbm_bytes
from .header import OTBM_MAGIC
from .nodes import OtbmNode, OtbmNodeTree, build_node_tree


def serialize_node(node: OtbmNode) -> bytes:
    out = bytearray((NODE_START, node.node_type))
    out.extend(escape_otbm_bytes(node.attributes))
    for child in node.children:
        out.extend(serialize_node(child))
    out.append(NODE_END)
    return bytes(out)


def serialize_node_tree(tree: OtbmNodeTree) -> bytes:
    return OTBM_MAGIC + serialize_node(tree.root)


def serialize_world(world) -> tuple[bytes, OtbmNodeTree]:
    tree = build_node_tree(world)
    return serialize_node_tree(tree), tree
