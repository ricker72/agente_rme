"""Critic service contract."""

from __future__ import annotations

from typing import Protocol

from ui.models.critic_dto import CriticDTO, CriticRequestDTO, HeatmapDTO


class CriticService(Protocol):
    """Contract between UI pages and future critic adapters."""

    def analyze_world(self, request: CriticRequestDTO) -> CriticDTO:
        """Analyze a world from a typed request."""
        ...

    def get_last_report(self) -> CriticDTO:
        """Return the most recent critic report."""
        ...

    def get_heatmaps(self) -> list[HeatmapDTO]:
        """Return available critic heatmaps."""
        ...
