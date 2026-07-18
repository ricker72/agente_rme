"""
WG-20U playtest panel.
"""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtWidgets import QComboBox, QLabel, QPushButton

from .base_panel import LivePreviewPanel


class PlaytestPanel(LivePreviewPanel):
    """Player/GM/Ghost playtest controls and validation status."""

    modes = ["Player", "GM", "Ghost"]

    def __init__(self) -> None:
        super().__init__("Playtest")
        self.mode = QComboBox()
        self.mode.addItems(self.modes)
        self.status = QLabel("Traversal: UNKNOWN")
        self.walk_button = QPushButton("Walk")
        self.floor_button = QPushButton("Change Floors")
        self.layout.addWidget(self.mode)
        self.layout.addWidget(self.walk_button)
        self.layout.addWidget(self.floor_button)
        self.layout.addWidget(self.status)

    def set_data(self, data: Dict[str, Any]) -> None:
        self.status.setText(
            "Traversal: "
            f"{data.get('traversal_status', data.get('navigation_validation', 'UNKNOWN'))}"
        )
