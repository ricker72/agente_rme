"""
PMX-04R1 — Tile renderer with proper Tibia draw order.
Renders ground, borders, walls, bottom items, creatures, effects, and top items.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QPainter, QPen

from .appearance_models import ResolvedSprite
from .stack_renderer import StackRenderer


class TileRenderer:
    """Renders a single tile with all its layers in official Tibia draw order.

    Responsibilities:
    - drawGround()
    - drawGroundBorders()
    - drawWalls()
    - drawBottomItems()
    - drawCreatures()
    - drawTopItems()
    - drawEffects()
    """

    def __init__(self, stack_renderer: StackRenderer | None = None) -> None:
        self.stack_renderer = stack_renderer or StackRenderer()

    def render_tile(
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
        """Render a complete tile with all layers."""
        self.stack_renderer.render_stack(
            painter=painter,
            rect=rect,
            ground=ground,
            borders=borders,
            walls=walls,
            bottom_items=bottom_items,
            creatures=creatures,
            effects=effects,
            top_items=top_items,
            opacity=opacity,
        )

    def draw_ground(
        self,
        painter: QPainter,
        rect: QRectF,
        ground: ResolvedSprite,
    ) -> None:
        """Draw the ground layer of a tile."""
        self.stack_renderer.render_single(painter, rect, ground)

    def draw_ground_borders(
        self,
        painter: QPainter,
        rect: QRectF,
        borders: tuple[ResolvedSprite, ...],
    ) -> None:
        """Draw the ground border layer."""
        for border in borders:
            self.stack_renderer.render_single(painter, rect, border)

    def draw_walls(
        self,
        painter: QPainter,
        rect: QRectF,
        walls: tuple[ResolvedSprite, ...],
    ) -> None:
        """Draw the wall layer."""
        for wall in walls:
            self.stack_renderer.render_single(painter, rect, wall)

    def draw_bottom_items(
        self,
        painter: QPainter,
        rect: QRectF,
        items: tuple[ResolvedSprite, ...],
    ) -> None:
        """Draw bottom items (items on the ground)."""
        for item in items:
            self.stack_renderer.render_single(painter, rect, item)

    def draw_creatures(
        self,
        painter: QPainter,
        rect: QRectF,
        creatures: tuple[ResolvedSprite, ...],
    ) -> None:
        """Draw creatures on the tile."""
        for creature in creatures:
            self.stack_renderer.render_single(painter, rect, creature)

    def draw_effects(
        self,
        painter: QPainter,
        rect: QRectF,
        effects: tuple[ResolvedSprite, ...],
    ) -> None:
        """Draw effects on the tile."""
        for effect in effects:
            self.stack_renderer.render_single(painter, rect, effect)

    def draw_top_items(
        self,
        painter: QPainter,
        rect: QRectF,
        items: tuple[ResolvedSprite, ...],
    ) -> None:
        """Draw top items (items above creatures)."""
        for item in items:
            self.stack_renderer.render_single(painter, rect, item)

    def draw_empty_tile(
        self,
        painter: QPainter,
        rect: QRectF,
        color: QColor = QColor("#1a1d24"),
    ) -> None:
        """Draw an empty tile background."""
        painter.fillRect(rect, color)
        painter.setPen(QPen(QColor("#2a2d34"), 1))
        painter.drawRect(rect)