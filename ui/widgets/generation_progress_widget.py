"""Progress display for world generation."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QLabel, QProgressBar, QVBoxLayout, QWidget


class GenerationProgressWidget(QGroupBox):
    """Show generation state without blocking the UI."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Progress", parent)
        self.progress_bar = QProgressBar(self)
        self.status_label = QLabel("Idle", self)
        self._build_ui()

    def start(self) -> None:
        """Show an active generation state."""
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Generating")

    def complete(self, success: bool, message: str) -> None:
        """Show a completed generation state."""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100 if success else 0)
        self.status_label.setText(message)

    def reset(self) -> None:
        """Return to the idle state."""
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_label.setText("Idle")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        self.reset()
