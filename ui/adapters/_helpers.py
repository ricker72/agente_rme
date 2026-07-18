"""Shared helpers for UI core adapters."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

CORE_UNAVAILABLE = "Core unavailable"
CORE_EXECUTION_FAILED = "Core execution failed"


def safe_str(error: BaseException) -> str:
    """Return a stable English error string."""
    return str(error) or error.__class__.__name__


def read_attr(obj: Any, name: str, default: Any = None) -> Any:
    """Read either an object attribute or a mapping key."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def count_tiles(world: Any) -> int:
    """Return a defensive tile count for a core world object."""
    tile_count = getattr(world, "tile_count", None)
    if callable(tile_count):
        try:
            return int(tile_count())
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Failed to read tile_count(): %s", exc)
    tiles = getattr(world, "tiles", None)
    if tiles is not None:
        try:
            return len(tiles)
        except TypeError:
            return 0
    return 0
