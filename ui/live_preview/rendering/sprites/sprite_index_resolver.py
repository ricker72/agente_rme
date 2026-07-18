from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..appearance_render_model import RenderedTile
from .sprite_reference_loader import SpriteReference
from .sprite_sheet_decoder import DecodedSprite


@dataclass(frozen=True)
class SpriteSelectionContext:
    animation_frame: int = 0
    layer: int = 0
    pattern_x: int = 0
    pattern_y: int = 0
    pattern_z: int = 0
    subtype_index: int | None = None
    direction: int | str | None = None
    variant: int | None = None


@dataclass(frozen=True)
class SpriteSelectionResult:
    sprite_index: int
    sprite_id: int
    animation_frame: int
    layer: int
    pattern_x: int
    pattern_y: int
    pattern_z: int
    selection_source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SpriteIndexResolver:
    """Implements Canary GameSprite::getIndex and MapDrawer pattern rules."""

    DIRECTION_INDEX = {
        "north": 0,
        "east": 1,
        "south": 2,
        "west": 3,
        "n": 0,
        "e": 1,
        "s": 2,
        "w": 3,
    }
    LIQUID_SPRITE_SUBTYPE = {
        1: 1,
        5: 2,
        11: 2,
        3: 3,
        4: 3,
        7: 3,
        13: 3,
        16: 3,
        17: 3,
        6: 4,
        8: 5,
        12: 5,
        14: 5,
        9: 6,
        15: 6,
        10: 7,
        2: 7,
        18: 8,
        20: 9,
        19: 10,
    }

    def context_for_tile(self, tile: RenderedTile, animation_frame: int = 0) -> SpriteSelectionContext:
        reference_patterns = tile.model.render_metadata or {}
        width = max(1, int(reference_patterns.get("pattern_width", 1) or 1))
        height = max(1, int(reference_patterns.get("pattern_height", 1) or 1))
        depth = max(1, int(reference_patterns.get("pattern_depth", 1) or 1))
        metadata = {str(k).lower(): v for k, v in reference_patterns.items()}
        flags = {str(k).lower(): v for k, v in (tile.model.flags or {}).items()}
        direction = metadata.get("direction", getattr(tile, "direction", None))
        variant = metadata.get("variant", getattr(tile, "variant", None))
        pattern_x = int(metadata.get("pattern_x", tile.x % width) or 0) % width
        pattern_y = int(metadata.get("pattern_y", tile.y % height) or 0) % height
        pattern_z = int(metadata.get("pattern_z", tile.floor % depth) or 0) % depth

        if direction is not None:
            direction_index = self._direction_index(direction)
            pattern_x = direction_index % width
        if variant is not None:
            variant_index = max(0, int(variant))
            pattern_x = variant_index % width
            pattern_y = (variant_index // width) % height
            pattern_z = (variant_index // (width * height)) % depth

        subtype = int(metadata.get("subtype", getattr(tile, "subtype", 0)) or 0)
        count = int(metadata.get("count", getattr(tile, "count", 1)) or 1)
        subtype_index: int | None = None
        if self._truthy(flags.get("liquidpool")) or self._truthy(flags.get("liquidcontainer")):
            subtype_index = self.LIQUID_SPRITE_SUBTYPE.get(subtype, 0)
        elif self._truthy(flags.get("cumulative")) or self._truthy(flags.get("stackable")):
            subtype_index = self.stackable_subtype(max(count, subtype))
        elif self._truthy(flags.get("hang")):
            hook = str(metadata.get("hook", direction or "")).lower()
            pattern_x = 1 if hook in {"south", "s", "1"} and width >= 2 else (
                2 if hook in {"east", "e", "2"} and width >= 3 else 0
            )
        return SpriteSelectionContext(
            animation_frame=max(0, int(animation_frame)),
            pattern_x=pattern_x,
            pattern_y=pattern_y,
            pattern_z=pattern_z,
            subtype_index=subtype_index,
            direction=direction,
            variant=int(variant) if variant is not None else None,
        )

    def resolve(
        self,
        reference: SpriteReference,
        context: SpriteSelectionContext,
    ) -> SpriteSelectionResult | None:
        if not reference.sprite_ids:
            return None
        width = max(1, int(reference.patterns.get("width", 1)))
        height = max(1, int(reference.patterns.get("height", 1)))
        depth = max(1, int(reference.patterns.get("depth", 1)))
        layers = max(1, int(reference.layers))
        frames = max(1, int(reference.frame_count))
        frame = context.animation_frame % frames
        layer = context.layer % layers
        pattern_x = context.pattern_x % width
        pattern_y = context.pattern_y % height
        pattern_z = context.pattern_z % depth
        if context.subtype_index is not None:
            index = max(0, int(context.subtype_index))
            source = "RME_SUBTYPE_DIRECT_INDEX"
        else:
            index = (
                (((frame * depth + pattern_z) * height + pattern_y) * width + pattern_x)
                * layers
                + layer
            )
            source = "RME_GAME_SPRITE_INDEX"
        index = index % len(reference.sprite_ids)
        return SpriteSelectionResult(
            sprite_index=index,
            sprite_id=int(reference.sprite_ids[index]),
            animation_frame=frame,
            layer=layer,
            pattern_x=pattern_x,
            pattern_y=pattern_y,
            pattern_z=pattern_z,
            selection_source=source,
        )

    def resolve_visible_layers(
        self,
        reference: SpriteReference,
        context: SpriteSelectionContext,
        decoded: list[DecodedSprite],
        include_all_layers: bool = False,
    ) -> list[DecodedSprite]:
        by_index = {index: sprite for index, sprite in enumerate(decoded)}
        # MapDrawer::BlitItem renders ordinary map items with layer 0. Extra
        # layers are outfit-specific and must be requested explicitly.
        layer_count = max(1, reference.layers) if include_all_layers else 1
        selected = []
        for layer in range(layer_count):
            result = self.resolve(
                reference,
                SpriteSelectionContext(**{**asdict(context), "layer": layer}),
            )
            if result and result.sprite_index in by_index:
                selected.append(by_index[result.sprite_index])
        return selected

    def stackable_subtype(self, count: int) -> int:
        if count <= 1:
            return 0
        if count <= 2:
            return 1
        if count <= 3:
            return 2
        if count <= 4:
            return 3
        if count < 10:
            return 4
        if count < 25:
            return 5
        if count < 50:
            return 6
        return 7

    def _direction_index(self, value: int | str) -> int:
        if isinstance(value, str):
            return self.DIRECTION_INDEX.get(value.lower(), int(value) if value.isdigit() else 0)
        return int(value)

    def _truthy(self, value: Any) -> bool:
        return value is True or str(value).lower() in {"1", "true", "yes"}
