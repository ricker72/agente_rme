"""Campaign service DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CampaignRequestDTO:
    """Campaign generation request."""

    name: str = ""
    world_id: str = ""
    objective: str = ""
    stage_count: int = 0


@dataclass(slots=True)
class CampaignStageDTO:
    """Single campaign stage."""

    stage_id: str = ""
    title: str = ""
    objective: str = ""
    status: str = "pending"


@dataclass(slots=True)
class CampaignDTO:
    """Generated campaign data."""

    campaign_id: str = ""
    name: str = ""
    description: str = ""
    stages: list[CampaignStageDTO] = field(default_factory=list)
    status: str = "Service not connected"
    success: bool = False
    error_message: str = ""
