"""
Recent Projects Widget for Agente RME Studio Dashboard.

Displays a list of recently accessed projects.
"""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QListWidget, QListWidgetItem


class RecentProjectsWidget(QFrame):
    """Widget displaying recent projects list."""

    STYLESHEET = """
        RecentProjectsWidget {
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
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
    """

    ITEM_STYLESHEET = """
        QListWidget {
            background-color: #252526;
            border: 1px solid #313244;
        }
        QListWidgetItem {
            padding: 4px 8px;
        }
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("recent_projects_widget")
        self.setStyleSheet(self.STYLESHEET)
        self.setFixedHeight(150)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title
        self._title_label = QLabel("Recent Projects", self)
        self._title_label.setStyleSheet(self.TITLE_STYLESHEET)
        layout.addWidget(self._title_label)

        # Projects list
        self._projects_list = QListWidget(self)
        self._projects_list.setStyleSheet(self.ITEM_STYLESHEET)
        layout.addWidget(self._projects_list)

    def add_project(self, project_name: str) -> None:
        """Add a project to the list."""
        item = QListWidgetItem(project_name)
        self._projects_list.addItem(item)

    def clear_projects(self) -> None:
        """Clear all projects from the list."""
        self._projects_list.clear()
