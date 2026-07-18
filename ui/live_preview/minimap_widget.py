"""
Semantic minimap for WG-20U.
"""

from __future__ import annotations

from typing import Any, Dict, List

from PySide6.QtCore import QRect, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter
from PySide6.QtWidgets import QWidget


class MinimapWidget(QWidget):
    """Semantic minimap with click navigation."""

    navigationRequested = Signal(int, int)

    semantic_colors = {
        "water": "#235B7A",
        "roads": "#6A5B45",
        "road": "#6A5B45",
        "buildings": "#77603F",
        "building": "#77603F",
        "nature": "#2E6B4F",
        "temple": "#D4AF37",
        "depot": "#7B87C9",
        "quest": "#8D5FBF",
        "boss": "#A84040",
        "npc": "#48A0A8",
        "spawn": "#9B4B4B",
    }

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(160, 120)
        self.tiles: List[Dict[str, Any]] = []

    def set_tiles(self, tiles: List[Dict[str, Any]]) -> None:
        self.tiles = tiles
        self.update()

    def set_sprite_render_models(self, models: List[Dict[str, Any]]) -> None:
        self.tiles = [
            {
                "x": model.get("coordinates", {}).get("x", 0),
                "y": model.get("coordinates", {}).get("y", 0),
                "semantic_role": model.get("render_status", "sprite"),
                "category": "sprite_rendered" if model.get("sprite_ids") else "missing_sprite",
            }
            for model in models
        ]
        self.update()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        self.navigationRequested.emit(
            int(event.position().x()),
            int(event.position().y()),
        )

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#161A22"))
        for tile in self.tiles:
            x = int(tile.get("x", 0)) % max(1, self.width())
            y = int(tile.get("y", 0)) % max(1, self.height())
            role = str(
                tile.get("semantic_role") or tile.get("category") or tile.get("role", "building")
            ).lower()
            if tile.get("sprite_ids"):
                color = QColor("#5CC8FF")
            elif tile.get("render_status") == "MISSING_SPRITE":
                color = QColor("#E05252")
            else:
                color = QColor(self.semantic_colors.get(role, "#1D2330"))
            painter.fillRect(QRect(x, y, 3, 3), color)
