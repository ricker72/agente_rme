"""
HITO 16 - Procedural World Generation: Biome Generator
======================================================

Turns an empty rectangular area of a WorldModel into a coherent biome
surface (grass, sand, ice, swamp, lava, etc.) using a deterministic
biome palette derived from the theme's metadata.

The biome generator is the *first* layer applied to a fresh area. Roads,
rivers, structures and spawns are added on top of the biome tiles.

Architecture:
    (x1, y1, x2, y2, z, theme) -> BiomeGenerator.generate(...)
    -> Dict[(x, y, z), {"ground": int, "tag": str}]

Public API:
    BiomeGenerator
    BiomeTile (dataclass)
    generate_biome(world, x1, y1, x2, y2, z, theme, ...) -> int
    generate_continental_biome(world, width, height, z, theme) -> int
    generate_zone_biome(world, x, y, w, h, z, theme) -> int
    get_biome_palette(theme) -> Dict[str, List[int]]
    BIOME_PALETTES
    BIOME_TAG_BY_THEME
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple


# =============================================================================
# Tile result dataclass
# =============================================================================

@dataclass
class BiomeTile:
    """A single biome tile produced by the generator."""
    x: int
    y: int
    z: int
    ground: int
    tag: str = "biome"           # "grass" | "sand" | "water" | "stone" | ...
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x, "y": self.y, "z": self.z,
            "ground": self.ground, "tag": self.tag,
            "metadata": dict(self.metadata),
        }


# =============================================================================
# Static knowledge: which tile IDs belong to each biome tag
# =============================================================================

# Each palette is a tag -> list of item IDs (most common first).
# The generator picks ground IDs by rotating through the palette so
# neighbouring tiles do not all look identical.
BIOME_PALETTES: Dict[str, Dict[str, List[int]]] = {
    "generic": {
        "grass": [396, 397, 398],
        "dirt":  [360, 361, 362],
        "stone": [361, 103, 102],
        "sand":  [360, 361],
        "water": [4597, 4598, 4600],
        "snow":  [670, 671, 672],
        "lava":  [598, 599],
    },
    "issavi": {
        "grass":  [415, 393, 421],
        "dirt":   [103, 102],
        "stone":  [103, 102, 361],
        "sand":   [360, 361, 362],
        "water":  [4597, 4598, 4600],
        "snow":   [670, 671],
        "lava":   [598, 599],
    },
    "roshamuul": {
        "grass":  [1053, 1056, 1057],
        "dirt":   [447, 231, 358],
        "stone":  [231, 358, 103],
        "sand":   [360, 361],
        "water":  [4597, 4598, 4600],
        "snow":   [670, 671],
        "lava":   [598, 599, 600],
    },
    "soul_war": {
        "grass":  [514, 513, 516],
        "dirt":   [514, 516],
        "stone":  [231, 358, 103],
        "sand":   [360, 361],
        "water":  [4597, 4598, 4600],
        "snow":   [670, 671],
        "lava":   [598, 599, 600],
    },
    "library": {
        "grass":  [396, 397, 398],
        "dirt":   [360, 361],
        "stone":  [103, 102, 361],
        "sand":   [360, 361],
        "water":  [4597, 4598, 4600],
        "snow":   [670, 671],
        "lava":   [598, 599],
    },
    "yalahar": {
        "grass":  [450, 451, 452],
        "dirt":   [450, 453, 454],
        "stone":  [103, 102, 361],
        "sand":   [360, 361],
        "water":  [4597, 4598, 4600],
        "snow":   [670, 671],
        "lava":   [598, 599],
    },
    "falcon": {
        "grass":  [428, 429, 430],
        "dirt":   [431, 432],
        "stone":  [103, 102, 361],
        "sand":   [360, 361],
        "water":  [4597, 4598, 4600],
        "snow":   [670, 671, 672],
        "lava":   [598, 599],
    },
    "cobra": {
        "grass":  [514, 513, 516],
        "dirt":   [514, 516],
        "stone":  [231, 358, 103],
        "sand":   [360, 361],
        "water":  [4597, 4598, 4600],
        "snow":   [670, 671],
        "lava":   [598, 599],
    },
    "ice": {
        "grass":  [670, 671, 672],
        "dirt":   [673, 674],
        "stone":  [103, 102, 361],
        "sand":   [360, 361],
        "water":  [4597, 4598, 4600],
        "snow":   [670, 671, 672, 673],
        "lava":   [598, 599],
    },
    "jungle": {
        "grass":  [440, 441, 442],
        "dirt":   [443, 444],
        "stone":  [103, 102, 361],
        "sand":   [360, 361],
        "water":  [4597, 4598, 4600],
        "snow":   [670, 671],
        "lava":   [598, 599],
    },
    "thais": {
        "grass":  [351, 352, 353],
        "dirt":   [354],
        "stone":  [103, 102, 361],
        "sand":   [360, 361],
        "water":  [4597, 4598, 4600],
        "snow":   [670, 671],
        "lava":   [598, 599],
    },
    "venore": {
        "grass":  [360, 361, 362],
        "dirt":   [363],
        "stone":  [103, 102, 361],
        "sand":   [360, 361, 362],
        "water":  [4597, 4598, 4600, 4601],
        "snow":   [670, 671],
        "lava":   [598, 599],
    },
    "ankrahmun": {
        "grass":  [480, 481, 482],
        "dirt":   [483],
        "stone":  [103, 102, 361],
        "sand":   [360, 361, 362, 363],
        "water":  [4597, 4598, 4600],
        "snow":   [670, 671],
        "lava":   [598, 599],
    },
}

# Mapping: theme.metadata["biome"] -> primary surface tag
BIOME_TAG_BY_THEME: Dict[str, str] = {
    "desert":       "sand",
    "desert_ruins": "sand",
    "desert_city":  "sand",
    "nightmare":    "stone",
    "nether":       "stone",
    "arcane":       "stone",
    "exotic_urban": "grass",
    "mountain":     "stone",
    "swamp":        "dirt",
    "arctic":       "snow",
    "tropical":     "grass",
    "temperate":    "grass",
    "generic":      "grass",
}


# =============================================================================
# Helpers
# =============================================================================

def get_biome_palette(theme: Any) -> Dict[str, List[int]]:
    """
    Return the palette for a given theme.

    Accepts:
        - a ThemeAssets (uses .name and .metadata["biome"])
        - a string (theme name)
    """
    if theme is None:
        return {k: list(v) for k, v in BIOME_PALETTES["generic"].items()}

    if isinstance(theme, str):
        name = theme.lower()
    else:
        name = str(getattr(theme, "name", "generic")).lower()

    palette = BIOME_PALETTES.get(name, BIOME_PALETTES["generic"])
    return {k: list(v) for k, v in palette.items()}


def pick_ground_for_tag(palette: Dict[str, List[int]], tag: str, salt: int) -> int:
    """Pick a ground ID for a tile tag, rotating by salt to avoid repetition."""
    options = palette.get(tag) or palette.get("grass") or [396]
    if not options:
        return 396
    return int(options[salt % len(options)])


def pick_primary_tag(theme: Any) -> str:
    """
    Pick the primary surface tag for a theme.

    Inspects theme.metadata["biome"] when available.
    """
    if theme is None:
        return "grass"
    if isinstance(theme, str):
        return "grass"
    meta = getattr(theme, "metadata", None) or {}
    if not isinstance(meta, dict):
        return "grass"
    biome = meta.get("biome", "generic")
    return BIOME_TAG_BY_THEME.get(str(biome), "grass")


# =============================================================================
# BiomeGenerator
# =============================================================================

class BiomeGenerator:
    """
    Fills an area with biome-appropriate ground tiles.

    The generator:
        1. Picks the dominant surface tag for the theme (sand for desert,
           snow for arctic, grass for temperate, ...).
        2. Adds 1-2 neighbour tags around the edges (e.g. grass+sand at a
           desert border) to soften the transition.
        3. Places water tiles in a few low spots for visual interest.
        4. Avoids putting the same ground ID on every tile.

    Usage:
        gen = BiomeGenerator(seed=42)
        count = gen.generate(world_model, x1=0, y1=0, x2=99, y2=99,
                             z=7, theme=theme_assets)
    """

    DEFAULT_EDGE_TAGS: Dict[str, List[str]] = {
        "sand":  ["grass", "dirt"],
        "grass": ["dirt", "sand"],
        "dirt":  ["grass", "stone"],
        "stone": ["dirt", "grass"],
        "snow":  ["stone", "dirt"],
        "lava":  ["stone", "dirt"],
    }

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        world: Any,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        z: int,
        theme: Any,
        primary_tag: Optional[str] = None,
        edge_thickness: int = 2,
        water_chance: float = 0.02,
        overwrite: bool = False,
    ) -> int:
        """
        Fill the rectangle (x1,y1)-(x2,y2) at z with biome tiles.

        Args:
            world: WorldModel to write into.
            x1, y1, x2, y2: Inclusive rectangle bounds.
            z: Z-layer.
            theme: ThemeAssets, or theme name string.
            primary_tag: Override the dominant surface tag.
            edge_thickness: How many tiles of the "edge" tag at the border.
            water_chance: Per-tile chance of being a water tile (0..1).
            overwrite: If False, skip tiles that are already set.

        Returns:
            Number of tiles written.
        """
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1

        palette = get_biome_palette(theme)
        primary = primary_tag or pick_primary_tag(theme)
        edge_tags = self.DEFAULT_EDGE_TAGS.get(primary, ["dirt", "grass"])
        edge_tag = edge_tags[0] if edge_tags else primary

        from core.world.tile import Tile  # local import to avoid cycles

        count = 0
        for ix in range(x1, x2 + 1):
            for iy in range(y1, y2 + 1):
                if not overwrite and world.has_tile(ix, iy, z):
                    continue

                # Water wins: small chance anywhere
                roll = self._rng.random()
                if roll < water_chance and "water" in palette:
                    tag = "water"
                else:
                    tag = self._tag_for_position(
                        ix, iy, x1, y1, x2, y2,
                        primary=primary, edge=edge_tag,
                        edge_thickness=edge_thickness,
                    )

                ground = pick_ground_for_tag(palette, tag, salt=(ix * 7 + iy * 13))
                tile = Tile(x=ix, y=iy, z=z, ground=ground, zone=f"biome:{tag}")
                world.set_tile(tile)
                count += 1

        return count

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _tag_for_position(
        self,
        ix: int,
        iy: int,
        x1: int, y1: int, x2: int, y2: int,
        primary: str,
        edge: str,
        edge_thickness: int,
    ) -> str:
        """Decide which tag (primary, edge, ...) a tile should belong to."""
        # Distance to the nearest border
        d_left   = ix - x1
        d_right  = x2 - ix
        d_top    = iy - y1
        d_bottom = y2 - iy
        d_min = min(d_left, d_right, d_top, d_bottom)

        if d_min < edge_thickness:
            return edge

        # Soft random patches of the secondary tag
        if self._rng.random() < 0.08:
            return edge
        return primary


# =============================================================================
# Module-level helpers
# =============================================================================

def generate_biome(
    world: Any,
    x1: int, y1: int, x2: int, y2: int,
    z: int,
    theme: Any,
    primary_tag: Optional[str] = None,
    seed: Optional[int] = None,
    water_chance: float = 0.02,
    overwrite: bool = False,
) -> int:
    """
    One-shot helper: fill a rectangle with biome tiles and return count.
    """
    gen = BiomeGenerator(seed=seed)
    return gen.generate(
        world, x1, y1, x2, y2, z, theme,
        primary_tag=primary_tag,
        water_chance=water_chance,
        overwrite=overwrite,
    )


def generate_continental_biome(
    world: Any,
    world_width: int,
    world_height: int,
    z: int,
    theme: Any,
    seed: Optional[int] = None,
    water_chance: float = 0.04,
) -> int:
    """
    Fill the whole world bounds (0..world_width, 0..world_height) with a
    continental-scale biome pass (slightly higher water chance, used as
    a background before zones are placed).
    """
    return generate_biome(
        world, 0, 0, world_width, world_height, z, theme,
        seed=seed, water_chance=water_chance, overwrite=False,
    )


def generate_zone_biome(
    world: Any,
    x: int, y: int, width: int, height: int,
    z: int,
    theme: Any,
    primary_tag: Optional[str] = None,
    seed: Optional[int] = None,
    water_chance: float = 0.0,
) -> int:
    """
    Fill the area of a single placed zone (top-left + size).
    """
    return generate_biome(
        world, x, y, x + width - 1, y + height - 1, z, theme,
        primary_tag=primary_tag, seed=seed, water_chance=water_chance,
        overwrite=False,
    )
# Backwards-compatible alias for the old string-returning Lua-style helper.
def biome_generator_lua(theme: str, x1: int, y1: int, x2: int, y2: int, z: int) -> str:
    """Legacy compatibility shim - returns a Lua code string."""
    if theme == "ice":
        ground = 428
    elif theme == "jungle":
        ground = 514
    elif theme == "roshamuul":
        ground = 1056
    else:
        ground = 415
    return (
        f"-- Biome generator for theme: {theme}\n"
        "if not app.hasMap() then\n    return\nend\n\n"
        f"app.transaction(function(map)\n"
        f"    for x = {x1}, {x2} do\n"
        f"        for y = {y1}, {y2} do\n"
        f"            local tile = map:getOrCreateTile(x, y, {z})\n"
        f"            tile.ground = {ground}\n"
        f"        end\n"
        f"    end\n"
        f"end)\n"
    )
