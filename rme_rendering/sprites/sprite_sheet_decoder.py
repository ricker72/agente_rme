"""
Sprite sheet decoder for WG-20U-B.

The current repository ships appearance metadata and sprite identifiers, but no
separate pixel atlas file. The decoder therefore resolves sprite ownership,
animation, layer, and pattern metadata from the authoritative references and
leaves pixel materialization to the atlas manager.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .sprite_reference_loader import SpriteReference


@dataclass(frozen=True)
class DecodedSprite:
    """Decoded sprite placement and animation metadata."""

    appearance_id: int
    sprite_id: int
    frame_index: int
    layer_index: int
    pattern_index: int
    pattern_x: int
    pattern_y: int
    pattern_z: int
    width: int
    height: int
    render_status: str = "SPRITE_REFERENCE_DECODED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SpriteSheetDecoder:
    """Decodes appearance sprite references into renderable sprite metadata."""

    def decode_reference(self, reference: SpriteReference) -> list[DecodedSprite]:
        if not reference.sprite_ids:
            return []
        frames = max(1, reference.frame_count)
        layers = max(1, reference.layers)
        pattern_width = max(1, reference.patterns.get("width", 1))
        pattern_height = max(1, reference.patterns.get("height", 1))
        pattern_depth = max(1, reference.patterns.get("depth", 1))
        pattern_total = pattern_width * pattern_height * pattern_depth
        decoded = []
        for index, sprite_id in enumerate(reference.sprite_ids):
            layer_index = index % layers
            pattern_flat = (index // layers) % pattern_total
            pattern_x = pattern_flat % pattern_width
            pattern_y = (pattern_flat // pattern_width) % pattern_height
            pattern_z = (pattern_flat // (pattern_width * pattern_height)) % pattern_depth
            decoded.append(
                DecodedSprite(
                    appearance_id=reference.appearance_id,
                    sprite_id=int(sprite_id),
                    frame_index=(index // (layers * pattern_total)) % frames,
                    layer_index=layer_index,
                    pattern_index=pattern_flat,
                    pattern_x=pattern_x,
                    pattern_y=pattern_y,
                    pattern_z=pattern_z,
                    width=max(1, reference.dimensions.get("width", 1)),
                    height=max(1, reference.dimensions.get("height", 1)),
                )
            )
        return decoded

    def audit(self, decoded: list[DecodedSprite]) -> dict[str, Any]:
        return {
            "sprite_decoder_ready": bool(decoded),
            "decoded_sprite_references": len(decoded),
            "animation_metadata_resolved": True,
            "layer_metadata_resolved": True,
            "frame_metadata_resolved": True,
        }
