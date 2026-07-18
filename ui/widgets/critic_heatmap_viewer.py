"""Heatmap viewer for Visual Critic Studio."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget

from ui.models.critic_dto import HeatmapDTO


class CriticHeatmapViewer(QTabWidget):
    """Display critic heatmap PNGs with safe fallbacks."""

    DEFAULT_TABS = {
        "Density Heatmap": "density_heatmap.png",
        "Navigation Heatmap": "navigation_heatmap.png",
        "Spawn Heatmap": "spawn_heatmap.png",
        "Pathfinding Heatmap": "pathfinding_heatmap.png",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.labels: dict[str, QLabel] = {}
        self._build_ui()

    def update_heatmaps(self, heatmaps: list[HeatmapDTO]) -> None:
        """Update tab labels from heatmap DTOs."""
        by_title = {heatmap.title: heatmap for heatmap in heatmaps}
        by_id = {heatmap.heatmap_id: heatmap for heatmap in heatmaps}
        for title, default_path in self.DEFAULT_TABS.items():
            heatmap = by_title.get(title) or by_id.get(default_path)
            path = heatmap.heatmap_id if heatmap is not None else default_path
            self._load_into_label(title, path)

    def show_placeholders(self) -> None:
        """Show placeholder text in every tab."""
        for label in self.labels.values():
            label.setPixmap(QPixmap())
            label.setText("No heatmap available")

    def _build_ui(self) -> None:
        for title in self.DEFAULT_TABS:
            page = QWidget(self)
            layout = QVBoxLayout(page)
            label = QLabel("No heatmap available", page)
            label.setMinimumHeight(180)
            label.setWordWrap(True)
            layout.addWidget(label)
            self.labels[title] = label
            self.addTab(page, title)
        self.show_placeholders()

    def _load_into_label(self, title: str, path: str) -> bool:
        label = self.labels[title]
        candidate = Path(path)
        if not candidate.is_file():
            label.setPixmap(QPixmap())
            label.setText("No heatmap available")
            return False
        pixmap = QPixmap(str(candidate))
        if pixmap.isNull():
            label.setPixmap(QPixmap())
            label.setText("No heatmap available")
            return False
        label.setPixmap(pixmap.scaledToWidth(420))
        label.setText("")
        return True
