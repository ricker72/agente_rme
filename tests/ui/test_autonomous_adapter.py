"""Tests for AutonomousAdapter."""

from __future__ import annotations

from pytest import MonkeyPatch

from ui.adapters import autonomous_adapter
from ui.adapters.autonomous_adapter import AutonomousAdapter
from ui.models.autonomous_dto import (
    AutonomousDesignRequestDTO,
    AutonomousMetricsDTO,
    AutonomousResultDTO,
)


class FakeDesignResult:
    success = True
    design_id = "d1"
    convergence_data = [0.1, 0.2]


class FakeDesigner:
    def generate(self, prompt: str, max_iterations: int = 20) -> FakeDesignResult:
        return FakeDesignResult()


def test_autonomous_adapter_returns_dto() -> None:
    adapter = AutonomousAdapter(designer_factory=FakeDesigner)
    dto = adapter.run_design(AutonomousDesignRequestDTO(world_id="w1", goal="build"))
    assert isinstance(dto, AutonomousResultDTO)
    assert dto.success is True
    assert len(adapter.get_iterations()) == 2


def test_autonomous_adapter_failure_returns_safe_dto(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(autonomous_adapter, "_IMPORT_ERROR", ImportError("auto missing"))
    monkeypatch.setattr(autonomous_adapter, "AutonomousWorldDesigner", None)
    dto = AutonomousAdapter().run_design(AutonomousDesignRequestDTO(world_id="w1"))
    assert dto.summary == "Core unavailable"
    assert dto.success is False
    assert "auto missing" in dto.error_message


def test_autonomous_metrics_missing_is_safe() -> None:
    metrics = AutonomousAdapter(metrics_path="missing.json").get_metrics()
    assert isinstance(metrics, AutonomousMetricsDTO)
    assert metrics.success is False
