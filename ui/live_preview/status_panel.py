"""
WG-20U status panel.
"""

from PySide6.QtWidgets import QLabel

from .base_panel import LivePreviewPanel


class StatusPanel(LivePreviewPanel):
    def __init__(self) -> None:
        super().__init__("Status")
        self.status = QLabel("RME_LIKE_LIVE_PREVIEW_READY")
        self.status.setWordWrap(True)
        self.layout.addWidget(self.status)

    def set_status(self, text: str) -> None:
        self.status.setText(text)
        self.status.setToolTip(text)
