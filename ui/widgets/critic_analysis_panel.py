"""Action panel for Visual Critic Studio."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QWidget


class CriticAnalysisPanel(QGroupBox):
    """Expose critic analysis actions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Actions", parent)
        self.analyze_button = QPushButton("Analyze Current World", self)
        self.load_last_button = QPushButton("Load Last Critic Report", self)
        self.refresh_heatmaps_button = QPushButton("Refresh Heatmaps", self)
        self._build_ui()

    def set_analyzing(self, analyzing: bool) -> None:
        """Disable analyze while worker is running."""
        self.analyze_button.setEnabled(not analyzing)

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.addWidget(self.analyze_button)
        layout.addWidget(self.load_last_button)
        layout.addWidget(self.refresh_heatmaps_button)
