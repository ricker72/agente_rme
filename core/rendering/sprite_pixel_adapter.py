"""Adapter between sprite resolver output and PMX-03R1 pixel decoder."""

from __future__ import annotations

from PySide6.QtGui import QPixmap

from .appearance_models import ResolvedSprite
from .sprite_pixel_decoder import DecodedSpritePixels, SpritePixelDecoder
from .sprite_pixel_source import SpritePixelSourceDiscovery


class SpritePixelAdapter:
    def __init__(
        self,
        discovery: SpritePixelSourceDiscovery | None = None,
        decoder: SpritePixelDecoder | None = None,
    ) -> None:
        self.discovery = discovery or SpritePixelSourceDiscovery()
        self.decoder = decoder or SpritePixelDecoder(self.discovery)
        self._source_state: str | None = None

    def render(self, resolved: ResolvedSprite, size: int = 32) -> tuple[QPixmap | None, DecodedSpritePixels]:
        sprite_id = resolved.primary_sprite_id
        if resolved.status != "RESOLVED" or sprite_id is None:
            return (
                None,
                DecodedSpritePixels(
                    sprite_id=0,
                    status=resolved.status,
                    reason=resolved.reason or "sprite reference is unresolved",
                ),
            )
        decoded = self.decoder.decode_sprite(sprite_id)
        if decoded.image is None or decoded.status != "REAL_SPRITE_RENDERED":
            return None, decoded
        pixmap = QPixmap.fromImage(decoded.image).scaled(size, size)
        return pixmap, decoded

    def source_state(self) -> str:
        if self._source_state is None:
            self._source_state = self.discovery.best_pixel_source_state()
        return self._source_state
