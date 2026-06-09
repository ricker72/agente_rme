import re
from typing import List, Tuple


MIN_X = 0
MAX_X = 65535
MIN_Y = 0
MAX_Y = 65535
MIN_Z = 0
MAX_Z = 15


def validate_tile(lua_text: str) -> Tuple[bool, List[str]]:
    """
    Validate tile coordinates used in map:getOrCreateTile(x, y, z).

    Checks:
    - No negative coordinates
    - z within valid range [0, 15]
    - No out-of-range tiles
    """
    errors: List[str] = []

    # Pattern: map:getOrCreateTile(x, y, z) — allow negatives with optional minus
    tile_pattern = re.compile(r'map:getOrCreateTile\s*\(\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\)')
    for match in tile_pattern.finditer(lua_text):
        x = int(match.group(1))
        y = int(match.group(2))
        z = int(match.group(3))

        if x < MIN_X or x > MAX_X:
            errors.append(f"Invalid X coordinate {x} (valid: {MIN_X}-{MAX_X})")
        if y < MIN_Y or y > MAX_Y:
            errors.append(f"Invalid Y coordinate {y} (valid: {MIN_Y}-{MAX_Y})")
        if z < MIN_Z or z > MAX_Z:
            errors.append(f"Invalid Z coordinate {z} (valid: {MIN_Z}-{MAX_Z})")

    return len(errors) == 0, errors