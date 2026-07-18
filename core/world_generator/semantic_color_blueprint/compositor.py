from __future__ import annotations

from dataclasses import dataclass

from .models import BlueprintLayer, Position, SemanticColorBlueprint
from .palette import SemanticColorPalette, SemanticColorToken


@dataclass(frozen=True)
class ComposedCell:
    position: Position
    tokens: tuple[SemanticColorToken, ...]

    @property
    def ground(self) -> SemanticColorToken | None:
        candidates = [token for token in self.tokens if token.ground_ids]
        return candidates[-1] if candidates else None


class BlueprintCompositor:
    def __init__(self, palette: SemanticColorPalette) -> None:
        self.palette = palette

    def compose(self, blueprint: SemanticColorBlueprint) -> dict[Position, ComposedCell]:
        result: dict[Position, list[SemanticColorToken]] = {}
        for layer in sorted(blueprint.layers):
            mask = blueprint.layers[layer]
            for position, token_id in sorted(mask.cells.items()):
                token = self.palette.get(token_id, layer)
                result.setdefault(position, []).append(token)
        composed = {
            position: ComposedCell(position, tuple(tokens))
            for position, tokens in result.items()
        }
        self._validate(composed)
        return composed

    def _validate(self, cells: dict[Position, ComposedCell]) -> None:
        for position, cell in cells.items():
            ground_tokens = [token for token in cell.tokens if token.brush_type == "ground" and token.layer != BlueprintLayer.TERRAIN_BORDER]
            if len(ground_tokens) > 1:
                # Higher layers intentionally replace lower foundations (sea -> terrain -> road).
                if ground_tokens != sorted(ground_tokens, key=lambda token: token.layer):
                    raise ValueError(f"Invalid ground order at {position}")
            has_ground = bool(ground_tokens)
            requiring = [token.token_id for token in cell.tokens if token.requires_ground]
            if requiring and not has_ground:
                raise ValueError(f"Objects {requiring} at {position} have no ground mask")
