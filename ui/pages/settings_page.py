"""
Settings placeholder page for Agente RME Studio.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class SettingsPage(QWidget):
    """Placeholder settings page."""

    PAGE_ID = "settings"

    page_loaded = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(self.PAGE_ID)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        label = QLabel("Settings", self)
        label.setStyleSheet("font-size: 24px; font-weight: 600; padding: 24px;")
        layout.addWidget(label)
        layout.addStretch()
        self.page_loaded.emit(self.PAGE_ID)
