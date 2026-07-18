"""Materialize resolved sprite references into Qt thumbnails when possible."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap

from .appearance_models import MaterializedSprite, ResolvedSprite
from .sprite_pixel_adapter import SpritePixelAdapter


class SpriteMaterializer:
    """Converts resolved sprite references to pixmaps with honest error states."""

    def __init__(
        self,
        pixel_sources: tuple[str, ...] = (),
        pixel_adapter: SpritePixelAdapter | None = None,
    ) -> None:
        self.pixel_sources = tuple(path for path in pixel_sources if Path(path).exists())
        self.pixel_adapter = pixel_adapter or SpritePixelAdapter()

    def materialize(
        self,
        resolved: ResolvedSprite,
        size: int = 32,
        frame: int = 0,
    ) -> tuple[QPixmap, MaterializedSprite]:
        cache_key = (
            resolved.item_id,
            resolved.primary_sprite_id or resolved.status,
            int(size),
            int(frame),
        )
        if resolved.status != "RESOLVED":
            status = resolved.status
            pixmap = self._warning_pixmap(size, "!")
            return (
                pixmap,
                MaterializedSprite(
                    resolved=resolved,
                    status=status,
                    size=size,
                    cache_key=cache_key,
                    warnings=(resolved.reason or "sprite unresolved",),
                ),
            )
        pixmap, decoded = self.pixel_adapter.render(resolved, size=size)
        if pixmap is not None and decoded.status == "REAL_SPRITE_RENDERED":
            return (
                pixmap,
                MaterializedSprite(
                    resolved=resolved,
                    status="REAL_SPRITE_RENDERED",
                    size=size,
                    cache_key=cache_key,
                    pixel_source=decoded.source_path,
                ),
            )
        source_state = self.pixel_adapter.source_state()
        if source_state == "PIXEL_SOURCE_CANDIDATE":
            pixmap = self._warning_pixmap(size, "ID")
            return (
                pixmap,
                MaterializedSprite(
                    resolved=resolved,
                    status="PIXEL_SOURCE_IDENTIFIED",
                    size=size,
                    cache_key=cache_key,
                    warnings=(decoded.reason or "pixel source candidate exists but decoder did not render",),
                ),
            )
        if not self.pixel_sources:
            pixmap = self._warning_pixmap(size, "PX")
            return (
                pixmap,
                MaterializedSprite(
                    resolved=resolved,
                    status="PIXEL_SOURCE_MISSING",
                    size=size,
                    cache_key=cache_key,
                    warnings=(
                        decoded.reason
                        or "resolved sprite IDs but catalog-content.json/Tibia.spr pixel source was not found",
                    ),
                ),
            )
        pixmap = self._warning_pixmap(size, "OK")
        return (
            pixmap,
            MaterializedSprite(
                resolved=resolved,
                status="SPRITE_PIXEL_DECODER_PENDING",
                size=size,
                cache_key=cache_key,
                pixel_source=self.pixel_sources[0],
                warnings=("pixel source detected but decoder is not implemented in PMX-03",),
            ),
        )

    def _warning_pixmap(self, size: int, label: str) -> QPixmap:
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.fillRect(QRect(0, 0, size, size), QColor("#2A2116"))
        painter.setPen(QPen(QColor("#D69E2E"), max(1, size // 12)))
        painter.drawRect(1, 1, size - 2, size - 2)
        painter.setPen(QPen(QColor("#FFE8A3"), 1))
        painter.drawText(QRect(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, label)
        painter.end()
        return pixmap
