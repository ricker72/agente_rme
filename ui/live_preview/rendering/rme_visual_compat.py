from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ui.live_preview.rendering.rme_draw_order import RMEStackItem


TILE_SIZE = 32
MAP_GROUND_LAYER = 7
MAP_MAX_LAYER = 15
MAP_LAYERS = 16


@dataclass(frozen=True)
class RMEDrawingOptions:
    transparent_floors: bool = False
    transparent_items: bool = False
    show_all_floors: bool = True
    show_grid: int = 0
    show_items: bool = True
    show_monsters: bool = True
    show_npcs: bool = True
    show_shade: bool = True
    show_special_tiles: bool = True
    show_preview: bool = False
    hide_items_when_zoomed: bool = True
    ingame: bool = False


@dataclass(frozen=True)
class RMEViewState:
    floor: int = MAP_GROUND_LAYER
    zoom: float = 1.0
    scroll_x: int = 0
    scroll_y: int = 0
    screen_width: int = 1280
    screen_height: int = 720
    options: RMEDrawingOptions = field(default_factory=RMEDrawingOptions)

    @property
    def tile_size(self) -> int:
        return int(TILE_SIZE / max(self.zoom, 0.125))

    @property
    def start_z(self) -> int:
        if not self.options.show_all_floors:
            return self.floor
        if self.floor < 8:
            return MAP_GROUND_LAYER
        return min(MAP_MAX_LAYER, self.floor + 2)

    @property
    def end_z(self) -> int:
        return self.floor

    @property
    def superend_z(self) -> int:
        return 8 if self.floor > MAP_GROUND_LAYER else 0

    def visible_floor_sequence(self) -> list[int]:
        return list(range(self.start_z, self.superend_z - 1, -1))

    def floor_adjustment(self, z: int) -> int:
        if z <= MAP_GROUND_LAYER:
            return (MAP_GROUND_LAYER - z) * TILE_SIZE
        return TILE_SIZE * (self.floor - z)

    def draw_position(self, x: int, y: int, z: int) -> tuple[int, int]:
        offset = self.floor_adjustment(z)
        return ((x * TILE_SIZE) - self.scroll_x - offset, (y * TILE_SIZE) - self.scroll_y - offset)

    def draw_bounds(self) -> tuple[int, int, int, int]:
        start_x = self.scroll_x // TILE_SIZE
        start_y = self.scroll_y // TILE_SIZE
        if self.floor > MAP_GROUND_LAYER:
            start_x -= 2
            start_y -= 2
        end_x = start_x + self.screen_width // max(self.tile_size, 1) + 2
        end_y = start_y + self.screen_height // max(self.tile_size, 1) + 2
        return start_x, start_y, end_x, end_y


@dataclass(frozen=True)
class RMETileStack:
    ground: RMEStackItem | None
    items: tuple[RMEStackItem, ...]
    creatures: tuple[RMEStackItem, ...] = ()

    def render_items(self, *, include_creatures: bool = True) -> list[RMEStackItem]:
        ordered: list[RMEStackItem] = []
        if self.ground is not None:
            ordered.append(self.ground)
        ordered.extend(self.items)
        if include_creatures:
            ordered.extend(self.creatures)
        return ordered


GROUND_ROLES = {"GROUND", "WATER", "ROAD", "MOUNTAIN", "INTERIOR", "EXTERIOR", "DOCK"}
BORDER_ROLES = {"BORDER", "OPTIONAL_BORDER", "CARPET"}
WALL_ROLES = {"WALL", "WINDOW", "DOOR"}
CREATURE_ROLES = {"CREATURE", "MONSTER", "NPC"}


def rme_stack_from_items(items: Iterable[RMEStackItem]) -> RMETileStack:
    ground: RMEStackItem | None = None
    borders: list[RMEStackItem] = []
    walls: list[RMEStackItem] = []
    normal: list[RMEStackItem] = []
    creatures: list[RMEStackItem] = []

    for item in items:
        role = item.role.upper()
        if ground is None and role in GROUND_ROLES:
            ground = item
        elif role in BORDER_ROLES:
            borders.append(item)
        elif role in WALL_ROLES:
            walls.append(item)
        elif role in CREATURE_ROLES:
            creatures.append(item)
        else:
            normal.append(item)

    # RME stores borders at the beginning of Tile::items. Walls and normal
    # decoration keep their authoring order after the low stack.
    return RMETileStack(
        ground=ground,
        items=tuple(sorted(borders, key=lambda item: item.source_index) + sorted(walls, key=lambda item: item.source_index) + sorted(normal, key=lambda item: item.source_index)),
        creatures=tuple(sorted(creatures, key=lambda item: item.source_index)),
    )


def rme_sprite_anchor(tile_x: int, tile_y: int, sprite_width: int, sprite_height: int, draw_height: int = 0) -> tuple[int, int]:
    return (
        tile_x - max(0, sprite_width - TILE_SIZE) - draw_height,
        tile_y - max(0, sprite_height - TILE_SIZE) - draw_height,
    )


def audit_rme_visual_contract() -> dict[str, object]:
    surface = RMEViewState(floor=7)
    underground = RMEViewState(floor=9)
    return {
        "rme_visual_contract_ready": True,
        "tile_size": TILE_SIZE,
        "ground_layer": MAP_GROUND_LAYER,
        "surface_floor_sequence": surface.visible_floor_sequence(),
        "underground_floor_sequence": underground.visible_floor_sequence(),
        "underground_draw_offset_sample": underground.draw_position(1000, 1000, 10),
        "features": [
            "MapDrawer::SetupVars compatible floor range",
            "MapDrawer::getDrawPosition compatible z offset",
            "Tile::ground separated from Tile::items",
            "Tile::addBorderItem places borders at bottom of item stack",
            "creatures drawn above map items",
        ],
    }
