"""Autonomous design service contract."""

from __future__ import annotations

from typing import Protocol

from ui.models.autonomous_dto import (
    AutonomousDesignRequestDTO,
    AutonomousIterationDTO,
    AutonomousMetricsDTO,
    AutonomousResultDTO,
)


class AutonomousService(Protocol):
    """Contract between UI pages and future autonomous adapters."""

    def run_design(self, request: AutonomousDesignRequestDTO) -> AutonomousResultDTO:
        """Run an autonomous design request."""
        ...

    def get_iterations(self) -> list[AutonomousIterationDTO]:
        """Return autonomous design iterations."""
        ...

    def get_metrics(self) -> AutonomousMetricsDTO:
        """Return autonomous service metrics."""
        ...
