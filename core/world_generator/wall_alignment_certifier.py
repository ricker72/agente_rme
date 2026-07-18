from __future__ import annotations

from typing import Any

from core.world_generator.semantic_color_blueprint import BlueprintLayer, SemanticColorBlueprint


class WallAlignmentCertifier:
    """Certify materialized wall IDs against RME's 16-neighbor alignment table."""

    def certify(self, blueprint: SemanticColorBlueprint, editor: Any, palette: Any, engine: Any) -> dict[str, Any]:
        wall_cells = blueprint.mask(BlueprintLayer.WALL).cells
        door_cells = blueprint.mask(BlueprintLayer.DOOR_WINDOW).cells
        by_brush: dict[tuple[str, int], set[tuple[int, int]]] = {}
        for layer_cells in (wall_cells, door_cells):
            for (x, y, z), token_id in layer_cells.items():
                token = palette.get(token_id)
                by_brush.setdefault((token.brush_name, z), set()).add((x, y))
        mismatches: list[dict[str, Any]] = []
        checked = 0
        for position, token_id in sorted(wall_cells.items()):
            x, y, z = position
            token = palette.get(token_id, BlueprintLayer.WALL)
            brush = engine.wall_brush(token.brush_name)
            if brush is None:
                mismatches.append({"position": position, "reason": "missing brush", "brush": token.brush_name})
                continue
            neighbors = by_brush[(token.brush_name, z)]
            expected = brush.choose(
                north=(x, y - 1) in neighbors,
                south=(x, y + 1) in neighbors,
                east=(x + 1, y) in neighbors,
                west=(x - 1, y) in neighbors,
            )
            tile = editor.tiles.get(position)
            checked += 1
            if expected is not None and (tile is None or expected not in tile.items):
                mismatches.append(
                    {
                        "position": position,
                        "brush": token.brush_name,
                        "expected_item": expected,
                        "actual_items": list(tile.items) if tile else [],
                    }
                )
        return {
            "status": "PASS" if not mismatches else "FAIL",
            "algorithm": "Canary/RME WallBrush::full_border_types with half_border_types fallback",
            "checked_wall_tiles": checked,
            "mismatch_count": len(mismatches),
            "mismatches": mismatches[:100],
        }
