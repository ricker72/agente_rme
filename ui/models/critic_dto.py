"""Critic service DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class CriticRequestDTO:
    """Input data for a future critic adapter."""

    world_id: str = ""
    analysis_profile: str = "default"
    checks: list[str] = field(default_factory=list)


@dataclass(slots=True)
class CriticIssueDTO:
    """Single critic finding."""

    code: str = ""
    message: str = ""
    severity: str = "info"


@dataclass(slots=True)
class CriticDTO:
    """Critic analysis result."""

    analysis_id: str = ""
    score: float = 0.0
    issues: list[CriticIssueDTO] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    summary: str = "Service not connected"
    success: bool = False
    error_message: str = ""


@dataclass(slots=True)
class HeatmapDTO:
    """UI-safe heatmap metadata."""

    heatmap_id: str = ""
    title: str = ""
    width: int = 0
    height: int = 0
    values: list[float] = field(default_factory=list)
