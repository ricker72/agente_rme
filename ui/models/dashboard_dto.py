"""Dashboard service DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class HealthStatusDTO:
    """DTO for system health status data."""

    status: str = "Unavailable"
    healthy_checks: int = 0
    total_checks: int = 0


@dataclass(slots=True)
class MetricsDTO:
    """DTO for system metrics data."""

    success_rate: float = 0.0
    worlds_generated: int = 0
    exports_generated: int = 0


@dataclass(slots=True)
class CertificationDTO:
    """DTO for GA certification data."""

    version: str = "Unknown"
    certified: bool = False
    release_status: str = "Unknown"


@dataclass(slots=True)
class DashboardDTO:
    """Aggregated dashboard data returned by DashboardService."""

    health: HealthStatusDTO = field(default_factory=HealthStatusDTO)
    metrics: MetricsDTO = field(default_factory=MetricsDTO)
    certification: CertificationDTO = field(default_factory=CertificationDTO)
    recent_worlds: list[str] = field(default_factory=list)
    status: str = "Service not connected"
    success: bool = False
    error_message: str = ""
