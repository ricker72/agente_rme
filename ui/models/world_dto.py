"""World service DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class WorldGenerationRequestDTO:
    """Input data for a future world generation adapter."""

    name: str = ""
    width: int = 0
    height: int = 0
    theme: str = ""
    seed: int | None = None
    constraints: list[str] = field(default_factory=list)


@dataclass(slots=True)
class WorldDTO:
    """UI-safe world snapshot."""

    world_id: str = ""
    name: str = ""
    width: int = 0
    height: int = 0
    description: str = ""
    status: str = "Service not connected"
    success: bool = False
    error_message: str = ""


@dataclass(slots=True)
class WorldSummaryDTO:
    """Compact world summary for lists and dashboards."""

    world_id: str = ""
    name: str = ""
    size_label: str = ""
    status: str = "Service not connected"
    updated_at: str = ""
    success: bool = False
    error_message: str = ""
