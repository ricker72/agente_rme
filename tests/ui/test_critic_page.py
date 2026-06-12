"""Tests for Visual Critic Studio page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QEventLoop, QTimer

from ui.event_bus import (
    CriticAnalysisRequestedEvent,
    CriticCompletedEvent,
    EventBus,
    ServiceErrorEvent,
)
from ui.models.critic_dto import CriticDTO, CriticIssueDTO, CriticRequestDTO, HeatmapDTO
from ui.pages.critic_page import CriticAnalysisWorker, CriticPage


class FakeCriticService:
    """Fast fake service for page tests."""

    def __init__(self, success: bool = True) -> None:
        self.success = success
        self.requests: list[CriticRequestDTO] = []

    def analyze_world(self, request: CriticRequestDTO) -> CriticDTO:
        self.requests.append(request)
        return CriticDTO(
            analysis_id="a1",
            score=81.0,
            issues=[
                CriticIssueDTO(
                    code="DENSITY",
                    severity="medium",
                    message="Increase spawn density in north hunt",
                )
            ],
            suggestions=["Add secondary route to boss arena"],
            summary="Analysis completed" if self.success else "Core unavailable",
            success=self.success,
            error_message="" if self.success else "critic down",
        )

    def get_last_report(self) -> CriticDTO:
        return CriticDTO(analysis_id="last", score=70.0, summary="Loaded", success=True)

    def get_heatmaps(self) -> list[HeatmapDTO]:
        return [HeatmapDTO(heatmap_id="missing.png", title="Density Heatmap")]


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


def test_critic_page_creation(qapp_instance: object) -> None:
    page = CriticPage(critic_service=FakeCriticService())
    assert page.objectName() == "critic"
    assert page.action_panel.analyze_button.text() == "Analyze Current World"


def test_critic_page_builds_dto(qapp_instance: object) -> None:
    page = CriticPage(critic_service=FakeCriticService())
    page.world_selector.world_id_edit.setText("world-1")
    request = page.build_request()
    assert request.world_id == "world-1"
    assert "pathfinding" in request.checks


def test_critic_worker_execution_calls_service(qapp_instance: object) -> None:
    service = FakeCriticService()
    request = CriticRequestDTO(world_id="world-1")
    worker = CriticAnalysisWorker(service, request)
    payloads: list[object] = []
    worker.finished.connect(payloads.append)
    worker.run()
    assert service.requests == [request]
    assert payloads


def test_critic_page_analyze_flow(qapp_instance: object) -> None:
    service = FakeCriticService()
    events: list[object] = []
    bus = EventBus()
    bus.register(CriticAnalysisRequestedEvent, events.append)
    bus.register(CriticCompletedEvent, events.append)
    page = CriticPage(critic_service=service, event_bus=bus)
    page.world_selector.world_id_edit.setText("world-1")
    page.on_analyze_clicked()
    _wait_until(lambda: not page.is_analyzing())
    assert service.requests
    assert page.score_grid.cards["Overall Score"].score_label.text() == "81.0"
    assert "DENSITY" in page.issue_list.list_widget.item(0).text()
    assert "Add secondary route" in page.recommendation_list.list_widget.item(0).text()
    assert any(isinstance(event, CriticAnalysisRequestedEvent) for event in events)
    assert any(isinstance(event, CriticCompletedEvent) for event in events)


def test_critic_page_service_error_event(qapp_instance: object) -> None:
    events: list[object] = []
    bus = EventBus()
    bus.register(ServiceErrorEvent, events.append)
    page = CriticPage(critic_service=FakeCriticService(success=False), event_bus=bus)
    page.on_analyze_clicked()
    _wait_until(lambda: not page.is_analyzing())
    assert any(isinstance(event, ServiceErrorEvent) for event in events)


def test_critic_page_load_last_report(qapp_instance: object) -> None:
    page = CriticPage(critic_service=FakeCriticService())
    page.load_last_report()
    assert page.report_summary.status_value.text() == "Loaded"


def test_no_direct_core_imports_in_critic_page_or_widgets() -> None:
    targets = [
        Path("ui/pages/critic_page.py"),
        *Path("ui/widgets").glob("critic_*.py"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in targets)
    assert "import core" not in text
    assert "from core" not in text
    assert "import agents" not in text
    assert "from agents" not in text
