"""
System Health Widget for Agente RME Studio Dashboard.

Displays health status indicators (healthy, warning, error) from health_report.json.
"""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout


class SystemHealthWidget(QFrame):
    """Widget displaying system health status indicators."""

    STYLESHEET = """
        SystemHealthWidget {
            background-color: #1e1e2e;
            border-radius: 8px;
            border: 1px solid #313244;
            padding: 16px;
        }
    """

    TITLE_STYLESHEET = """
        QLabel {
            color: #a6adc8;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
    """

    HEALTHY_STYLESHEET = """
        QLabel {
            background-color: #a6e3a1;
            color: #1e1e2e;
            border-radius: 4px;
            padding: 4px 8px;
            font-weight: 600;
        }
    """

    WARNING_STYLESHEET = """
        QLabel {
            background-color: #f9e2af;
            color: #1e1e2e;
            border-radius: 4px;
            padding: 4px 8px;
            font-weight: 600;
        }
    """

    ERROR_STYLESHEET = """
        QLabel {
            background-color: #f38ba8;
            color: #1e1e2e;
            border-radius: 4px;
            padding: 4px 8px;
            font-weight: 600;
        }
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("system_health_widget")
        self.setStyleSheet(self.STYLESHEET)
        self.setFixedHeight(120)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title
        self._title_label = QLabel("System Health", self)
        self._title_label.setStyleSheet(self.TITLE_STYLESHEET)
        layout.addWidget(self._title_label)

        # Status row
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)

        self._healthy_label = QLabel("HEALTHY: 0", self)
        self._healthy_label.setStyleSheet(self.HEALTHY_STYLESHEET)
        status_layout.addWidget(self._healthy_label)

        self._warning_label = QLabel("WARNING: 0", self)
        self._warning_label.setStyleSheet(self.WARNING_STYLESHEET)
        status_layout.addWidget(self._warning_label)

        self._error_label = QLabel("ERROR: 0", self)
        self._error_label.setStyleSheet(self.ERROR_STYLESHEET)
        status_layout.addWidget(self._error_label)

        status_layout.addStretch()
        layout.addLayout(status_layout)
        layout.addStretch()

    def update_health(self, healthy: int, warning: int, error: int) -> None:
        """Update health status display."""
        self._healthy_label.setText(f"HEALTHY: {healthy}")
        self._warning_label.setText(f"WARNING: {warning}")
        self._error_label.setText(f"ERROR: {error}")
