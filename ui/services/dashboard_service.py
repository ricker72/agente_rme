"""Dashboard service contract."""

from __future__ import annotations

from typing import Protocol

from ui.models.dashboard_dto import DashboardDTO


class DashboardService(Protocol):
    """Contract for loading dashboard data."""

    def load_dashboard(self) -> DashboardDTO:
        """Load current dashboard data."""
        ...

    def refresh_dashboard(self) -> DashboardDTO:
        """Refresh and return dashboard data."""
        ...
