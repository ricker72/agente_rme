"""
Status Card Widget for Agente RME Studio Dashboard.

A card widget that displays a status with title, value, and status indicator.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class StatusCard(QFrame):
    """A card widget displaying a status with title, value, and indicator."""

    STYLESHEET = """
        StatusCard {
            background-color: #1e1e2e;
            border-radius: 8px;
            border: 1px solid #313244;
            padding: 16px;
        }
        StatusCard:hover {
            border: 1px solid #585b70;
        }
    """

    TITLE_STYLESHEET = """
        QLabel {
            color: #a6adc8;
            font-size: 11px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
    """

    VALUE_STYLESHEET = """
        QLabel {
            color: #cdd6f4;
            font-size: 24px;
            font-weight: 700;
        }
    """

    STATUS_STYLESHEET = """
        QLabel {
            color: #89b4fa;
            font-size: 12px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
        }
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("status_card")
        self.setStyleSheet(self.STYLESHEET)
        self.setFixedHeight(100)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Text container
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        self._title_label = QLabel(self)
        self._title_label.setStyleSheet(self.TITLE_STYLESHEET)
        text_layout.addWidget(self._title_label)

        self._value_label = QLabel(self)
        self._value_label.setStyleSheet(self.VALUE_STYLESHEET)
        text_layout.addWidget(self._value_label)

        layout.addLayout(text_layout)
        layout.addStretch()

        # Status indicator
        self._status_label = QLabel(self)
        self._status_label.setStyleSheet(self.STATUS_STYLESHEET)
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._status_label)

    def set_title(self, title: str) -> None:
        """Set the status title."""
        self._title_label.setText(title)

    def set_value(self, value: str) -> None:
        """Set the status value."""
        self._value_label.setText(value)

    def set_status(self, status: str, status_type: str = "info") -> None:
        """Set the status text and type (healthy, warning, error, info)."""
        self._status_label.setText(status)

        color_map = {
            "healthy": "#a6e3a1",
            "warning": "#f9e2af",
            "error": "#f38ba8",
            "info": "#89b4fa",
        }

        bg_color = color_map.get(status_type, "#89b4fa")
        text_color = (
            "#1e1e2e" if status_type in ["healthy", "warning", "error"] else "#cdd6f4"
        )

        self._status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 4px;
                padding: 2px 8px;
                font-weight: 600;
                font-size: 12px;
            }}
        """)

    def update_status(
        self, title: str, value: str, status: str, status_type: str = "info"
    ) -> None:
        """Update all status card fields at once."""
        self.set_title(title)
        self.set_value(value)
        self.set_status(status, status_type)
