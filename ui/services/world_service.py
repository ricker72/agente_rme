"""World service contract."""

from __future__ import annotations

from typing import Protocol

from ui.models.world_dto import WorldDTO, WorldGenerationRequestDTO, WorldSummaryDTO


class WorldService(Protocol):
    """Contract between UI pages and future world adapters."""

    def generate_world(self, request: WorldGenerationRequestDTO) -> WorldDTO:
        """Generate a world from a typed request."""
        ...

    def get_recent_worlds(self) -> list[WorldDTO]:
        """Return recent worlds."""
        ...

    def get_world_summary(self, world_id: str) -> WorldSummaryDTO:
        """Return a compact world summary."""
        ...
