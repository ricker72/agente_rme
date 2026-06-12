"""
Dashboard Page for Agente RME Studio.

Provides a real-time overview using MetricCard, SystemHealthWidget,
QuickActionCard, RecentProjectsWidget, and integrates data via
DashboardDataProvider. Dark theme only.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
)

# Widgets
from ui.widgets.metric_card import MetricCard
from ui.widgets.quick_action_card import QuickActionCard
from ui.widgets.recent_projects_widget import RecentProjectsWidget
from ui.widgets.system_health_widget import SystemHealthWidget

# Services
from ui.services.dashboard_data_provider import DashboardDataProvider

# Theme
from ui.theme import ThemeManager


class DashboardPage(QWidget):
    """Dashboard page displaying system overview and quick actions."""

    PAGE_ID = "dashboard"

    # Emitted when a quick action button is pressed
    navigation_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName(self.PAGE_ID)

        # Theme
        self._theme_manager = ThemeManager()
        self.setStyleSheet(self._theme_manager.global_stylesheet())

        # Data provider
        self.data_provider = DashboardDataProvider()
        self.data_provider.data_updated.connect(self._on_data_updated)

        # Build UI
        self._build_ui()

    # --------------------------------------------------------------------- #
    # UI Construction
    # --------------------------------------------------------------------- #
    def _build_ui(self) -> None:
        """Construct the dashboard layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(24)

        # ----------------------------------------------------------------- #
        # Top Area – Application Overview and Metric Cards
        # ----------------------------------------------------------------- #
        overview_label = QLabel("Application Overview", self)
        overview_label.setStyleSheet(
            "font-size: 20px; font-weight: 600; color: #cdd6f4; margin-bottom: 8px;"
        )
        main_layout.addWidget(overview_label)

        # Cards Grid (2 rows x 3 columns)
        cards_grid = QGridLayout()
        cards_grid.setSpacing(16)

        # Define metric cards (title, placeholder value, icon)
        metrics_info = [
            ("System Health", "OK", "health"),
            ("Knowledge Base", "0 items", "book"),
            ("Critic Engine", "Idle", "star"),
            ("OTBM Engine", "Idle", "export"),
            ("Autonomous Designer", "Ready", "campaign"),
            ("Last Export", "Never", "export"),
        ]

        self.metric_cards: list[MetricCard] = []
        for idx, (title, value, icon) in enumerate(metrics_info):
            card = MetricCard(self)
            card.update_metric(title, value, icon)
            self.metric_cards.append(card)
            row = idx // 3
            col = idx % 3
            cards_grid.addWidget(card, row, col)

        main_layout.addLayout(cards_grid)

        # ----------------------------------------------------------------- #
        # Second Section – Recent Activity
        # ----------------------------------------------------------------- #
        recent_activity_label = QLabel("Recent Activity", self)
        recent_activity_label.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #cdd6f4; margin-top: 24px;"
        )
        main_layout.addWidget(recent_activity_label)

        # Use RecentProjectsWidget as a placeholder for recent activity list
        self.recent_projects_widget = RecentProjectsWidget(self)
        main_layout.addWidget(self.recent_projects_widget)

        # ----------------------------------------------------------------- #
        # Third Section – Quick Actions
        # ----------------------------------------------------------------- #
        quick_actions_label = QLabel("Quick Actions", self)
        quick_actions_label.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #cdd6f4; margin-top: 24px;"
        )
        main_layout.addWidget(quick_actions_label)

        self.quick_actions_widget = QuickActionCard(self)
        self.quick_actions_widget.action_requested.connect(self._on_quick_action)
        main_layout.addWidget(self.quick_actions_widget)

        # ----------------------------------------------------------------- #
        # Fourth Section – System Status
        # ----------------------------------------------------------------- #
        system_status_label = QLabel("System Status", self)
        system_status_label.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #cdd6f4; margin-top: 24px;"
        )
        main_layout.addWidget(system_status_label)

        self.system_health_widget = SystemHealthWidget(self)
        main_layout.addWidget(self.system_health_widget)

        # Add stretch to push content to top
        main_layout.addStretch()

    # --------------------------------------------------------------------- #
    # Data handling
    # --------------------------------------------------------------------- #
    def _on_data_updated(self, data: dict) -> None:
        """Update UI elements when the data provider emits new data."""
        health = data.get("health", {})
        metrics = data.get("metrics", {})
        ga_cert = data.get("ga_cert", {})

        # Update System Health widget
        self.system_health_widget.update_health(
            healthy=health.get("healthy", 0),
            warning=health.get("warning", 0),
            error=health.get("error", 0),
        )

        # Update metric cards with real data where applicable
        # Mapping: index -> (value source, optional key)
        mapping = {
            0: ("health", None),  # System Health – show overall status
            1: ("knowledge", "datasets"),  # Knowledge Base – number of datasets
            2: ("critic", "status"),  # Critic Engine – status string
            3: ("otbm", "status"),  # OTBM Engine – status string
            4: ("autonomous", "status"),  # Autonomous Designer – status
            5: ("export", "last_export"),  # Last Export – timestamp
        }

        for idx, (source, key) in mapping.items():
            card = self.metric_cards[idx]
            if source == "health":
                status = "OK" if health.get("error", 0) == 0 else "ISSUES"
                card.update_metric("System Health", status, "health")
            elif source == "knowledge":
                count = ga_cert.get("knowledge_datasets", 0)
                card.update_metric("Knowledge Base", f"{count} items", "book")
            elif source == "critic":
                status = metrics.get("critic_status", "Idle")
                card.update_metric("Critic Engine", status, "star")
            elif source == "otbm":
                status = metrics.get("otbm_status", "Idle")
                card.update_metric("OTBM Engine", status, "export")
            elif source == "autonomous":
                status = metrics.get("autonomous_status", "Ready")
                card.update_metric("Autonomous Designer", status, "campaign")
            elif source == "export":
                ts = ga_cert.get("last_export_timestamp", "Never")
                card.update_metric("Last Export", ts, "export")

        # Populate recent projects widget with placeholder data
        self.recent_projects_widget.clear_projects()
        recent = ga_cert.get("recent_projects", [])
        for proj in recent[:5]:
            self.recent_projects_widget.add_project(proj)

    # --------------------------------------------------------------------- #
    # Quick action handling
    # --------------------------------------------------------------------- #
    def _on_quick_action(self, action: str) -> None:
        """Relay quick action requests as navigation events."""
        self.navigation_requested.emit(action)
