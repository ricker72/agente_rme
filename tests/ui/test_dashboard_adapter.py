"""Tests for DashboardAdapter."""

from __future__ import annotations

from ui.adapters.dashboard_adapter import DashboardAdapter
from ui.models.dashboard_dto import CertificationDTO, DashboardDTO, HealthStatusDTO, MetricsDTO


class FakeProvider:
    def refresh(self) -> None:
        return None

    def get_health_data(self) -> HealthStatusDTO:
        return HealthStatusDTO(status="ok")

    def get_metrics(self) -> MetricsDTO:
        return MetricsDTO(success_rate=100.0)

    def get_ga_certification(self) -> CertificationDTO:
        return CertificationDTO(version="1.0.0", certified=True)


def test_dashboard_adapter_returns_dto() -> None:
    adapter = DashboardAdapter(provider_factory=FakeProvider)
    dto = adapter.load_dashboard()
    assert isinstance(dto, DashboardDTO)
    assert dto.success is True
    assert dto.health.status == "ok"
    assert adapter.refresh_dashboard().success is True


def test_dashboard_adapter_failure_returns_safe_dto() -> None:
    def broken_provider() -> FakeProvider:
        raise RuntimeError("provider failed")

    dto = DashboardAdapter(provider_factory=broken_provider).load_dashboard()
    assert dto.success is False
    assert dto.status == "Core execution failed"
