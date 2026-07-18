"""
Metric Card Widget for Agente RME Studio Dashboard.

A modern card widget that displays a single metric with title, value, and icon.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout


class MetricCard(QFrame):
    """A card widget displaying a metric with title and value."""

    STYLESHEET = """
        MetricCard {
            background-color: #1e1e2e;
            border-radius: 8px;
            border: 1px solid #313244;
            padding: 16px;
        }
        MetricCard:hover {
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
            font-size: 28px;
            font-weight: 700;
        }
    """

    ICON_STYLESHEET = """
        QLabel {
            color: #89b4fa;
            font-size: 20px;
            font-weight: bold;
        }
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("metric_card")
        self.setStyleSheet(self.STYLESHEET)
        self.setFixedHeight(100)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Icon container
        self._icon_label = QLabel(self)
        self._icon_label.setStyleSheet(self.ICON_STYLESHEET)
        self._icon_label.setFixedWidth(40)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._icon_label)

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

    def set_title(self, title: str) -> None:
        """Set the metric title."""
        self._title_label.setText(title)

    def set_value(self, value: str) -> None:
        """Set the metric value."""
        self._value_label.setText(value)

    def set_icon(self, icon_text: str) -> None:
        """Set the icon text (emoji or character)."""
        icon_map = {
            "world": "\U0001f30d",
            "book": "\U0001f4da",
            "star": "\u2b50",
            "check": "\u2705",
            "export": "\U0001f4e4",
            "campaign": "\U0001f4cb",
        }
        display_icon = icon_map.get(icon_text, icon_text)
        self._icon_label.setText(display_icon)

    def update_metric(self, title: str, value: str, icon: str = "") -> None:
        """Update all metric card fields at once."""
        self.set_title(title)
        self.set_value(value)
        if icon:
            self.set_icon(icon)
