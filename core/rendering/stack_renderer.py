"""
PMX-04R1 — Stack renderer that renders the complete item stack for each tile.
Maintains official Tibia draw order: Ground → Border → Walls → Items → Creatures → Effects → Top Items.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QPixmap

from .appearance_models import ResolvedSprite
from .sprite_cache_lru import LRUSpriteCache


class StackRenderer:
    """Renders the complete item stack for a single tile.

    Official Tibia draw order:
    Ground → Border → Walls → Items → Creatures → Effects → Top Items
    """

    # Layer order constants (lower = drawn first)
    LAYER_GROUND = 0
    LAYER_BORDER = 1
    LAYER_WALL = 2
    LAYER_BOTTOM_ITEM = 3
    LAYER_CREATURE = 4
    LAYER_EFFECT = 5
    LAYER_TOP_ITEM = 6

    def __init__(self, sprite_cache: LRUSpriteCache | None = None) -> None:
        self.sprite_cache = sprite_cache or LRUSpriteCache()

    def render_stack(
        self,
        painter: QPainter,
        rect: QRectF,
        ground: ResolvedSprite | None = None,
        borders: tuple[ResolvedSprite, ...] = (),
        walls: tuple[ResolvedSprite, ...] = (),
        bottom_items: tuple[ResolvedSprite, ...] = (),
        creatures: tuple[ResolvedSprite, ...] = (),
        effects: tuple[ResolvedSprite, ...] = (),
        top_items: tuple[ResolvedSprite, ...] = (),
        opacity: float = 1.0,
    ) -> None:
        """Render the complete item stack for a tile in correct draw order."""
        if opacity < 1.0:
            painter.save()
            painter.setOpacity(opacity)

        # Layer 0: Ground
        if ground is not None:
            self._render_sprite(painter, rect, ground)

        # Layer 1: Borders
        for border in borders:
            self._render_sprite(painter, rect, border)

        # Layer 2: Walls
        for wall in walls:
            self._render_sprite(painter, rect, wall)

        # Layer 3: Bottom Items
        for item in bottom_items:
            self._render_sprite(painter, rect, item)

        # Layer 4: Creatures
        for creature in creatures:
            self._render_sprite(painter, rect, creature)

        # Layer 5: Effects
        for effect in effects:
            self._render_sprite(painter, rect, effect)

        # Layer 6: Top Items
        for top_item in top_items:
            self._render_sprite(painter, rect, top_item)

        if opacity < 1.0:
            painter.restore()

    def render_single(
        self,
        painter: QPainter,
        rect: QRectF,
        sprite: ResolvedSprite,
        opacity: float = 1.0,
    ) -> None:
        """Render a single sprite at the given rect."""
        if opacity < 1.0:
            painter.save()
            painter.setOpacity(opacity)

        self._render_sprite(painter, rect, sprite)

        if opacity < 1.0:
            painter.restore()

    def _render_sprite(
        self,
        painter: QPainter,
        rect: QRectF,
        sprite: ResolvedSprite,
    ) -> None:
        """Render a single resolved sprite at the given rectangle."""
        pixmap, _ = self.sprite_cache.get(sprite, size=int(rect.width()))
        if pixmap is None or pixmap.isNull():
            return

        # Scale to fit the tile rect
        scaled = pixmap.scaled(
            int(rect.width()),
            int(rect.height()),
        )
        painter.drawPixmap(int(rect.x()), int(rect.y()), scaled)

    def get_sprite_pixmap(
        self,
        sprite: ResolvedSprite,
        size: int = 32,
    ) -> QPixmap:
        """Get the pixmap for a sprite at the given size."""
        pixmap, _ = self.sprite_cache.get(sprite, size=size)
        if pixmap is None or pixmap.isNull():
            return QPixmap(size, size)
        return pixmap