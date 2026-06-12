"""Tests for WorldAdapter."""

from __future__ import annotations

from pytest import MonkeyPatch

from ui.adapters import world_adapter
from ui.adapters.world_adapter import WorldAdapter
from ui.models.world_dto import WorldDTO, WorldGenerationRequestDTO, WorldSummaryDTO


class FakeWorld:
    width = 16
    height = 32
    world_id = "w1"

    def tile_count(self) -> int:
        return 42


class FakeWorldGenerator:
    def __init__(self, seed: int | None = None) -> None:
        self.seed = seed

    def generate(self, context: dict[str, object]) -> FakeWorld:
        return FakeWorld()


def test_world_adapter_returns_world_dto() -> None:
    adapter = WorldAdapter(generator_factory=FakeWorldGenerator)
    dto = adapter.generate_world(WorldGenerationRequestDTO(name="Test", seed=7))
    assert isinstance(dto, WorldDTO)
    assert dto.success is True
    assert dto.description == "42 tiles generated"
    assert isinstance(adapter.get_world_summary("w1"), WorldSummaryDTO)


def test_world_adapter_failure_returns_safe_dto(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(world_adapter, "_IMPORT_ERROR", ImportError("missing core"))
    monkeypatch.setattr(world_adapter, "WorldGenerator", None)
    dto = WorldAdapter().generate_world(WorldGenerationRequestDTO())
    assert dto.success is False
    assert dto.status == "Core unavailable"
    assert "missing core" in dto.error_message
