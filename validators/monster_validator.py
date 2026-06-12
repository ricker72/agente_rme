"""
Monster Validator — Verifica nombres de monstruos contra el AssetRegistry.

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


def validate_monster(lua_text: str) -> Tuple[bool, List[str]]:
    """
    Validate that all monster names used in tile:setCreature("Name", ...)
    exist in the AssetRegistry.
    """
    registry = _get_registry()
    errors: List[str] = []

    # Pattern: <variable>:setCreature("MonsterName", ...)
    creature_pattern = re.compile(r'\w+:setCreature\(\s*"([^"]+)"')
    for match in creature_pattern.finditer(lua_text):
        monster_name = match.group(1)
        if not registry.monster_exists(monster_name):
            errors.append(f"Unknown Monster '{monster_name}' in tile:setCreature()")

    return len(errors) == 0, errors
