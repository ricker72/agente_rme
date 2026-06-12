"""
Release info widget – shows the release name and version.
Data is obtained from ``DashboardDataProvider.get_release_info()``.
If the source files are missing, "Unknown" is displayed.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ReleaseInfoWidget(QWidget):
    """Displays the release name and version string."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._name_label = QLabel(self)
        self._version_label = QLabel(self)
        self._setup_ui()
        self.refresh({"name": "-", "version": "-"})

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        self._name_label.setStyleSheet("font-size: 14px; font-weight: 600;")
        self._version_label.setStyleSheet("font-size: 12px; color: #888;")
        layout.addWidget(self._name_label)
        layout.addWidget(self._version_label)
        self.setLayout(layout)

    def refresh(self, info: dict[str, str]) -> None:
        """Update the displayed name and version.

        Expected keys: ``name`` and ``version``. Missing keys default to "-".
        """
        name = info.get("name", "-")
        version = info.get("version", "-")
        self._name_label.setText(f"Release: {name}")
        self._version_label.setText(f"Version: {version}")
