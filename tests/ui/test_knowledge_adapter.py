"""Tests for KnowledgeAdapter."""

from __future__ import annotations

from pytest import MonkeyPatch

from ui.adapters import knowledge_adapter
from ui.adapters.knowledge_adapter import KnowledgeAdapter
from ui.models.knowledge_dto import KnowledgeMetricsDTO, KnowledgeQueryDTO, KnowledgeResultDTO


class FakeEntry:
    id = "k1"
    name = "Issavi"
    entry_type = "hunt"
    source = "dataset"


class FakeMatch:
    entry = FakeEntry()
    score = 0.9
    match_type = "text"


class FakeQueryResult:
    matches = [FakeMatch()]


class FakeKnowledgeEngine:
    dataset = type("Dataset", (), {"entries": [FakeEntry()]})()

    def query_text(self, text: str, k: int = 5) -> FakeQueryResult:
        return FakeQueryResult()

    def find_similar_hunts(self, name: str, k: int = 5) -> list[dict[str, object]]:
        return [{"name": name, "score": 1.0, "entry_type": "hunt"}]


def test_knowledge_adapter_returns_dtos() -> None:
    adapter = KnowledgeAdapter(engine_factory=FakeKnowledgeEngine)
    results = adapter.search(KnowledgeQueryDTO(text="Issavi", limit=1))
    assert isinstance(results[0], KnowledgeResultDTO)
    assert results[0].title == "Issavi"
    assert isinstance(adapter.get_metrics(), KnowledgeMetricsDTO)
    assert adapter.get_metrics().success is True


def test_knowledge_adapter_failure_returns_safe_metrics(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(knowledge_adapter, "_IMPORT_ERROR", ImportError("knowledge missing"))
    monkeypatch.setattr(knowledge_adapter, "KnowledgeEngine", None)
    adapter = KnowledgeAdapter()
    assert adapter.search(KnowledgeQueryDTO(text="x")) == []
    assert adapter.get_metrics().status == "Core unavailable"
