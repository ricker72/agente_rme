"""Tests for CriticAdapter."""

from __future__ import annotations

from pytest import MonkeyPatch

from ui.adapters import critic_adapter
from ui.adapters.critic_adapter import CriticAdapter
from ui.models.critic_dto import CriticDTO, CriticRequestDTO


class FakeScore:
    value = 88.5


class FakeResult:
    overall_score = FakeScore()
    issues: list[object] = []
    recommendations: list[object] = []


class FakeCriticEngine:
    def analyze_dict(self, data: dict[str, object], map_name: str = "") -> FakeResult:
        return FakeResult()


def test_critic_adapter_returns_dto() -> None:
    dto = CriticAdapter(engine_factory=FakeCriticEngine).analyze_world(
        CriticRequestDTO(world_id="w1")
    )
    assert isinstance(dto, CriticDTO)
    assert dto.success is True
    assert dto.score == 88.5


def test_critic_adapter_failure_returns_safe_dto(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(critic_adapter, "_IMPORT_ERROR", ImportError("critic missing"))
    monkeypatch.setattr(critic_adapter, "CriticEngine", None)
    dto = CriticAdapter().analyze_world(CriticRequestDTO())
    assert dto.success is False
    assert dto.summary == "Core unavailable"
    assert "critic missing" in dto.error_message
