"""Tests for Knowledge Explorer page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QEventLoop, QTimer

from ui.event_bus import (
    EventBus,
    KnowledgeQueryCompletedEvent,
    KnowledgeQueryRequestedEvent,
    ServiceErrorEvent,
)
from ui.models.knowledge_dto import (
    KnowledgeMetricsDTO,
    KnowledgeQueryDTO,
    KnowledgeResultDTO,
)
from ui.pages.knowledge_page import KnowledgePage, KnowledgeSearchWorker


class FakeKnowledgeService:
    """Fast fake service for page tests."""

    def __init__(self, fail_metrics: bool = False) -> None:
        self.fail_metrics = fail_metrics
        self.queries: list[KnowledgeQueryDTO] = []
        self.similarity_requests: list[tuple[str, str]] = []

    def search(self, query: KnowledgeQueryDTO) -> list[KnowledgeResultDTO]:
        self.queries.append(query)
        return [
            KnowledgeResultDTO(
                identifier="k1",
                title="Issavi Hunt",
                entry_type="Hunt",
                excerpt="A level 300-500 hunt.",
                tags=["level:300-500", "issavi"],
                source="dataset",
                relevance=0.95,
            )
        ]

    def find_similar(self, name: str, entry_type: str) -> list[KnowledgeResultDTO]:
        self.similarity_requests.append((name, entry_type))
        return [
            KnowledgeResultDTO(
                title="Falcon Hunt",
                entry_type=entry_type,
                source="dataset",
                relevance=0.81,
            )
        ]

    def get_metrics(self) -> KnowledgeMetricsDTO:
        if self.fail_metrics:
            return KnowledgeMetricsDTO(
                status="Core unavailable",
                success=False,
                error_message="metrics failed",
            )
        return KnowledgeMetricsDTO(
            total_entries=3,
            indexed_sources=1,
            status="Loaded",
            success=True,
        )


def _wait_until(predicate: Any, timeout_ms: int = 2000) -> None:
    loop = QEventLoop()
    deadline = QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(loop.quit)
    poller = QTimer()
    poller.setInterval(10)

    def poll() -> None:
        if predicate():
            poller.stop()
            loop.quit()

    poller.timeout.connect(poll)
    poller.start()
    deadline.start(timeout_ms)
    poll()
    if not predicate():
        loop.exec()
    poller.stop()
    deadline.stop()
    assert predicate()


def test_knowledge_page_creation(qapp_instance: object) -> None:
    page = KnowledgePage(knowledge_service=FakeKnowledgeService())
    assert page.objectName() == "knowledge"
    assert page.search_panel.search_button.text() == "Search"


def test_knowledge_page_builds_query(qapp_instance: object) -> None:
    page = KnowledgePage(knowledge_service=FakeKnowledgeService())
    page.search_panel.query_edit.setText("Issavi Hunt")
    page.filters_widget.set_selected_types(["Hunt"])
    query = page.build_query()
    assert query.text == "Issavi Hunt"
    assert query.entry_types == ["Hunt"]


def test_worker_execution_calls_service(qapp_instance: object) -> None:
    service = FakeKnowledgeService()
    query = KnowledgeQueryDTO(text="Issavi")
    worker = KnowledgeSearchWorker(service, query)
    payloads: list[object] = []
    worker.finished.connect(payloads.append)
    worker.run()
    assert service.queries == [query]
    assert payloads


def test_knowledge_search_flow_updates_ui_and_events(qapp_instance: object) -> None:
    service = FakeKnowledgeService()
    events: list[object] = []
    bus = EventBus()
    bus.register(KnowledgeQueryRequestedEvent, events.append)
    bus.register(KnowledgeQueryCompletedEvent, events.append)
    page = KnowledgePage(knowledge_service=service, event_bus=bus)
    page.search_panel.query_edit.setText("Issavi Hunt")
    page.on_search_clicked()
    _wait_until(lambda: not page.is_searching())
    assert service.queries
    assert page.results_table.rowCount() == 1
    assert page.metrics_widget.dataset_entries_value.text() == "3"
    assert "Reuse Issavi Hunt" in page.recommendation_panel.list_widget.item(0).text()
    assert any(isinstance(event, KnowledgeQueryRequestedEvent) for event in events)
    assert any(isinstance(event, KnowledgeQueryCompletedEvent) for event in events)


def test_similarity_flow_uses_selected_entry(qapp_instance: object) -> None:
    service = FakeKnowledgeService()
    page = KnowledgePage(knowledge_service=service)
    result = service.search(KnowledgeQueryDTO(text="Issavi"))[0]
    page.results_table.update_results([result])
    page.results_table.selectRow(0)
    page.find_similar()
    assert service.similarity_requests == [("Issavi Hunt", "Hunt")]
    assert page.similarity_panel.table.rowCount() == 1


def test_service_error_event_on_failed_metrics(qapp_instance: object) -> None:
    events: list[object] = []
    bus = EventBus()
    bus.register(ServiceErrorEvent, events.append)
    page = KnowledgePage(knowledge_service=FakeKnowledgeService(fail_metrics=True), event_bus=bus)
    page.search_panel.query_edit.setText("x")
    page.on_search_clicked()
    _wait_until(lambda: not page.is_searching())
    assert any(isinstance(event, ServiceErrorEvent) for event in events)


def test_no_direct_core_imports_in_knowledge_page_or_widgets() -> None:
    targets = [
        Path("ui/pages/knowledge_page.py"),
        *Path("ui/widgets").glob("knowledge_*.py"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in targets)
    assert "import core" not in text
    assert "from core" not in text
    assert "import agents" not in text
    assert "from agents" not in text
