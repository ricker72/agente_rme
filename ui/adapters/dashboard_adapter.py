"""Dashboard adapter backed by the existing dashboard data provider."""

from __future__ import annotations

import logging
from typing import Any, Callable

from ui.models.dashboard_dto import DashboardDTO
from ui.services.dashboard_data_provider import DashboardDataProvider

logger = logging.getLogger(__name__)


class DashboardAdapter:
    """Load dashboard DTOs through DashboardDataProvider."""

    def __init__(
        self,
        provider_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._provider_factory = provider_factory or DashboardDataProvider
        self._provider: DashboardDataProvider | None = None

    def load_dashboard(self) -> DashboardDTO:
        try:
            provider = self._get_provider()
            return DashboardDTO(
                health=provider.get_health_data(),
                metrics=provider.get_metrics(),
                certification=provider.get_ga_certification(),
                status="Loaded",
                success=True,
            )
        except Exception as exc:
            logger.exception("Dashboard adapter failed to load dashboard: %s", exc)
            return DashboardDTO(status="Core execution failed", success=False, error_message=str(exc))

    def refresh_dashboard(self) -> DashboardDTO:
        try:
            provider = self._get_provider()
            provider.refresh()
            return self.load_dashboard()
        except Exception as exc:
            logger.exception("Dashboard adapter failed to refresh dashboard: %s", exc)
            return DashboardDTO(status="Core execution failed", success=False, error_message=str(exc))

    def _get_provider(self) -> DashboardDataProvider:
        if self._provider is None:
            self._provider = self._provider_factory()
        return self._provider
