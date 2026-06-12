"""Autonomous design service DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class AutonomousDesignRequestDTO:
    """Request for a future autonomous design adapter."""

    world_id: str = ""
    goal: str = ""
    max_iterations: int = 0
    constraints: list[str] = field(default_factory=list)


@dataclass(slots=True)
class AutonomousIterationDTO:
    """Single autonomous design iteration."""

    iteration_id: str = ""
    iteration_number: int = 0
    status: str = "Service not connected"
    progress: float = 0.0
    summary: str = ""
    error_message: str = ""


@dataclass(slots=True)
class AutonomousResultDTO:
    """Final autonomous design result."""

    design_id: str = ""
    world_id: str = ""
    success: bool = False
    summary: str = "Service not connected"
    iterations: list[AutonomousIterationDTO] = field(default_factory=list)
    error_message: str = ""


@dataclass(slots=True)
class AutonomousMetricsDTO:
    """Autonomous service metrics."""

    total_iterations: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    status: str = "Service not connected"
    success: bool = False
    error_message: str = ""
