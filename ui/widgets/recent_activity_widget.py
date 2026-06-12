"""
Recent activity widget – shows timestamps for the last export, critic run, knowledge build, and campaign.
Data is supplied by ``DashboardDataProvider.get_recent_activity()`` which returns a mapping.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class RecentActivityWidget(QWidget):
    """Vertical list of recent activity timestamps."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._labels: dict[str, QLabel] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        for key in ("export", "critic", "knowledge", "campaign"):
            lbl = QLabel(self)
            lbl.setObjectName(f"activity_{key}")
            lbl.setStyleSheet("font-size: 12px;")
            layout.addWidget(lbl)
            self._labels[key] = lbl
        self.setLayout(layout)
        # Initialise with placeholders
        self.refresh({})

    def refresh(self, activity: dict[str, str]) -> None:
        """Update displayed timestamps.

        ``activity`` is a mapping where keys are ``export``, ``critic``, ``knowledge``, ``campaign``
        and values are human‑readable timestamps (or ``"-"`` when unavailable).
        """
        for key, lbl in self._labels.items():
            ts = activity.get(key, "-")
            lbl.setText(f"{key.capitalize()}: {ts}")
