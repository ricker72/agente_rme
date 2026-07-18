"""
Asset Validator — Verifica IDs de items contra el AssetRegistry.

Usa AssetRegistry como fuente de verdad única.
"""

import re
from typing import List, Tuple

from core.assets.asset_registry import AssetRegistry

_registry: AssetRegistry = None


def _get_registry() -> AssetRegistry:
    global _registry
    if _registry is None:
        _registry = AssetRegistry()
        _registry.load()
    return _registry


def validate_asset(lua_text: str) -> Tuple[bool, List[str]]:
    """
    Validate that all item IDs used in tile:addItem(N) and tile.ground = N
    exist in the AssetRegistry.
    """
    registry = _get_registry()
    errors: List[str] = []

    # Check tile:addItem(N)
    additem_pattern = re.compile(r"\w+:addItem\((\d+)\)")
    for match in additem_pattern.finditer(lua_text):
        item_id = int(match.group(1))
        if not registry.item_exists(item_id):
            errors.append(f"Unknown ItemID {item_id} in tile:addItem()")

    # Check tile.ground = N
    ground_pattern = re.compile(r"\w+\.ground\s*=\s*(\d+)")
    for match in ground_pattern.finditer(lua_text):
        ground_id = int(match.group(1))
        if not registry.item_exists(ground_id):
            errors.append(f"Unknown GroundID {ground_id} in tile.ground assignment")

    return len(errors) == 0, errors
