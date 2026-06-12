"""Preview widget for generated worlds."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGroupBox, QLabel, QVBoxLayout, QWidget


class WorldPreviewWidget(QGroupBox):
    """Show generated preview image or a safe placeholder."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Preview", parent)
        self.preview_label = QLabel("No preview available", self)
        self._build_ui()

    def load_preview(self, path: str = "generated_preview.png") -> bool:
        """Load a preview image if it exists."""
        preview_path = Path(path)
        if not preview_path.is_file():
            self.show_placeholder()
            return False
        pixmap = QPixmap(str(preview_path))
        if pixmap.isNull():
            self.show_placeholder()
            return False
        self.preview_label.setPixmap(
            pixmap.scaledToWidth(320),
        )
        self.preview_label.setText("")
        return True

    def show_placeholder(self) -> None:
        """Show a non-crashing empty preview state."""
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText("No preview available")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.preview_label.setMinimumHeight(140)
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)
        self.show_placeholder()
