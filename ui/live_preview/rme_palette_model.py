"""RME-like palette taxonomy for the professional mapping workspace."""

from __future__ import annotations

from dataclasses import dataclass

PALETTE_GROUPS = (
    "Terrain Palette",
    "Doodad Palette",
    "Item Palette",
    "House Palette",
    "Waypoint Palette",
    "Zone Palette",
    "Monster Palette",
    "Npc Palette",
    "RAW Palette",
)

TERRAIN_MATERIALS = (
    "Grounds",
    "Nature",
    "Mountains",
    "Walls",
    "Water",
    "Snow",
    "Roofs",
    "Desert",
    "Wood",
    "Marble",
    "Swamp",
    "Lava",
    "Caves",
    "Stairs",
    "Bridges",
    "Decoration",
    "Tiny Borders",
    "Large Borders",
    "Etc.",
)

ITEM_MATERIALS = (
    "Containers",
    "Furniture",
    "Magic",
    "Quest",
    "Depot",
    "Food",
    "Tools",
    "Signs",
    "Mechanisms",
    "Misc",
)


@dataclass(frozen=True)
class PaletteCard:
    item_id: int
    category: str
    source: str
    name: str
    client_id: int | None = None
    tileset: str = "Materials"
    sprite_status: str = "APPEARANCE_BACKED"
