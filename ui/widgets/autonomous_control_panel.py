"""Control panel for Autonomous Designer Workspace."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QWidget


class AutonomousControlPanel(QGroupBox):
    """Autonomous run controls."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Controls", parent)
        self.start_button = QPushButton("Start", self)
        self.pause_button = QPushButton("Pause", self)
        self.resume_button = QPushButton("Resume", self)
        self.stop_button = QPushButton("Stop", self)
        self.export_button = QPushButton("Export Best Result", self)
        self._build_ui()

    def set_running(self, running: bool) -> None:
        """Reflect worker running state."""
        self.start_button.setEnabled(not running)
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.export_button.setEnabled(not running)

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        for button in [
            self.start_button,
            self.pause_button,
            self.resume_button,
            self.stop_button,
            self.export_button,
        ]:
            layout.addWidget(button)
        self.set_running(False)
