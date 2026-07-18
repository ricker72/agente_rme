from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.editor.action_queue import ActionIdentifier
from core.editor.mapping_engine import TileCoord, WorkspaceMappingEngine, WorkspaceTile

from .compositor import BlueprintCompositor
from .models import BlueprintLayer, SemanticColorBlueprint
from .palette import SemanticColorPalette, SemanticColorToken

MapTile = WorkspaceTile


@dataclass(frozen=True)
class MaterializationReport:
    status: str
    tile_count: int
    ground_count: int
    item_count: int
    border_item_count: int
    border_item_ids: tuple[int, ...]
    unresolved_tokens: tuple[str, ...]
    action_label: str


class BlueprintMaterializer:
    """Inverse minimap pipeline: layered colors -> official RME brush stacks."""

    def __init__(self, palette: SemanticColorPalette, brush_engine: Any | None = None) -> None:
        self.brush_engine = brush_engine
        self.palette = palette.bind_rme_brush_engine(brush_engine) if brush_engine else palette

    def materialize(
        self,
        blueprint: SemanticColorBlueprint,
        editor: WorkspaceMappingEngine,
    ) -> MaterializationReport:
        cells = BlueprintCompositor(self.palette).compose(blueprint)
        used = {token.token_id: token for cell in cells.values() for token in cell.tokens}
        unresolved = sorted(
            token_id
            for token_id, token in used.items()
            if token.layer != BlueprintLayer.GAMEPLAY
            and token.layer != BlueprintLayer.TERRAIN_BORDER
            and not token.resolved
        )
        if unresolved:
            raise ValueError(
                "Blueprint contains semantic colors with no official brush material: "
                + ", ".join(unresolved)
            )

        brush_output = self._postprocess_brushes(cells)

        before: dict[tuple[int, int, int], MapTile | None] = {}
        after: dict[tuple[int, int, int], MapTile | None] = {}
        ground_count = 0
        item_count = 0
        border_item_count = 0
        border_item_ids: set[int] = set()
        for position, cell in cells.items():
            tile = _working_tile(position, editor, before, after)
            final_ground = cell.ground
            for token in cell.tokens:
                if token.layer == BlueprintLayer.GAMEPLAY:
                    tile.metadata[f"gameplay:{token.token_id}"] = "true"
                    continue
                if token.layer == BlueprintLayer.TERRAIN_BORDER:
                    tile.metadata["autoborder"] = "processed" if self.brush_engine else "requested"
                    continue
                if self.brush_engine and token.layer in {BlueprintLayer.WALL, BlueprintLayer.DOOR_WINDOW}:
                    # RME resolves wall shape and door orientation from the complete neighborhood.
                    continue
                if token.ground_ids and token is final_ground:
                    processed = brush_output.get(position, {})
                    tile.ground_id = int(
                        processed.get("ground", _choose(token.ground_ids, position, token.token_id))
                    )
                    tile.role = token.role
                    tile.brush = token.brush_name or token.token_id
                    ground_count += 1
                elif token.composites:
                    composite = token.composites[
                        _stable_index(len(token.composites), position, token.token_id)
                    ]
                    for dx, dy, dz, item_id in composite:
                        target = (position[0] + dx, position[1] + dy, position[2] + dz)
                        target_tile = _working_tile(target, editor, before, after)
                        _place_official_brush_item(
                            target_tile,
                            item_id,
                            token,
                            self.brush_engine,
                            editor.editor_map.item_catalog,
                        )
                        item_count += 1
                elif token.item_ids:
                    item_id = _choose(token.item_ids, position, token.token_id)
                    if item_id != tile.ground_id and item_id not in tile.items:
                        _place_official_brush_item(
                            tile,
                            item_id,
                            token,
                            self.brush_engine,
                            editor.editor_map.item_catalog,
                        )
                        item_count += 1
            for border_id in brush_output.get(position, {}).get("items", []):
                if border_id not in tile.items:
                    _append_sprite_backed(tile, int(border_id), final_ground, self.brush_engine)
                    item_count += 1
                    border_item_count += 1
                    border_item_ids.add(int(border_id))
            tile.metadata["semantic_blueprint"] = blueprint.name
            after[position] = tile

        label = f"Materialize color blueprint: {blueprint.name}"
        editor._commit(label, before, after, ActionIdentifier.DRAW)
        return MaterializationReport(
            status="PASS",
            tile_count=len(cells),
            ground_count=ground_count,
            item_count=item_count,
            border_item_count=border_item_count,
            border_item_ids=tuple(sorted(border_item_ids)),
            unresolved_tokens=(),
            action_label=label,
        )

    def _postprocess_brushes(self, cells: dict[Any, Any]) -> dict[tuple[int, int, int], dict[str, Any]]:
        if self.brush_engine is None:
            return {}
        output: dict[tuple[int, int, int], dict[str, Any]] = {}
        floors = sorted({position[2] for position in cells})
        for z in floors:
            grid: dict[tuple[int, int], dict[str, Any]] = {}
            terrain_to_brush: dict[str, str] = {}
            for position, cell in cells.items():
                if position[2] != z or cell.ground is None:
                    continue
                token = cell.ground
                terrain_to_brush[token.token_id] = token.brush_name
                grid[(position[0], position[1])] = {
                    "terrain": token.token_id,
                    "ground": token.ground_ids[0],
                    "items": [],
                    "brush": token.brush_name,
                }
            self.brush_engine.apply_ground_variants(grid, terrain_to_brush)
            self.brush_engine.apply_auto_borders(grid, terrain_to_brush)
            self.brush_engine.apply_optional_borders(grid, terrain_to_brush)
            wall_groups: dict[str, dict[str, set[tuple[int, int]]]] = {}
            for position, cell in cells.items():
                if position[2] != z:
                    continue
                for token in cell.tokens:
                    if token.layer not in {BlueprintLayer.WALL, BlueprintLayer.DOOR_WINDOW}:
                        continue
                    group = wall_groups.setdefault(token.brush_name, {"positions": set(), "doors": set()})
                    point = (position[0], position[1])
                    group["positions"].add(point)
                    if token.layer == BlueprintLayer.DOOR_WINDOW:
                        group["doors"].add(point)
            wall_plans = [
                {
                    "brush": brush_name,
                    "positions": sorted(group["positions"]),
                    "doors": sorted(group["doors"]),
                    "door_type": "normal",
                }
                for brush_name, group in sorted(wall_groups.items())
            ]
            self.brush_engine.apply_walls(grid, wall_plans)
            for (x, y), tile in grid.items():
                output[(x, y, z)] = tile
        return output


def _choose(values: tuple[int, ...], position: tuple[int, int, int], salt: str) -> int:
    # Stable across Python processes; unlike hash(), this is deterministic.
    seed = position[0] * 73_856_093 ^ position[1] * 19_349_663 ^ position[2] * 83_492_791
    seed ^= sum((index + 1) * ord(char) for index, char in enumerate(salt))
    return values[abs(seed) % len(values)]


def _stable_index(length: int, position: tuple[int, int, int], salt: str) -> int:
    return _choose(tuple(range(length)), position, salt)


def _working_tile(
    position: tuple[int, int, int],
    editor: WorkspaceMappingEngine,
    before: dict[tuple[int, int, int], MapTile | None],
    after: dict[tuple[int, int, int], MapTile | None],
) -> MapTile:
    if position not in before:
        before[position] = editor.tiles[position].copy() if position in editor.tiles else None
    existing = after.get(position)
    if existing is not None:
        return existing
    tile = editor.tiles.get(position, MapTile(coord=TileCoord(*position))).copy()
    tile.coord = TileCoord(*position)
    after[position] = tile
    return tile


def _append_sprite_backed(
    tile: MapTile,
    item_id: int,
    token: SemanticColorToken,
    brush_engine: Any | None,
) -> None:
    if isinstance(item_id, bool) or not isinstance(item_id, int) or item_id <= 0:
        raise TypeError(
            f"Official brush {token.brush_name or token.token_id!r} selected invalid "
            f"item value {item_id!r}; expected one positive server item ID"
        )
    if brush_engine and not brush_engine.is_sprite_backed(item_id):
        raise ValueError(
            f"Official brush {token.brush_name or token.token_id!r} selected "
            f"non-SPRITE_BACKED item {item_id}"
        )
    if item_id not in tile.items:
        tile.items.append(item_id)
    tile.item_id = item_id
    tile.metadata[f"brush:{token.layer.name.lower()}"] = token.brush_name


def _place_official_brush_item(
    tile: MapTile,
    item_id: int,
    token: SemanticColorToken,
    brush_engine: Any | None,
    item_catalog: Any,
) -> None:
    """Apply RME Tile::addItem semantics to a certified brush member."""
    item_type = item_catalog.get(item_id)
    if item_type.is_ground:
        if item_type.is_border:
            raise ValueError(
                f"Transparent border item {item_id} from {token.brush_name!r} "
                "cannot replace the tile ground"
            )
        if brush_engine and not brush_engine.is_sprite_backed(item_id):
            raise ValueError(
                f"Official brush {token.brush_name or token.token_id!r} selected "
                f"non-SPRITE_BACKED ground {item_id}"
            )
        tile.ground_id = item_id
        tile.brush = token.brush_name or token.token_id
        tile.metadata[f"brush:{token.layer.name.lower()}"] = token.brush_name
        return
    _append_sprite_backed(tile, item_id, token, brush_engine)
