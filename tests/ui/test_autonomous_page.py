"""Tests for Autonomous Designer Workspace page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QEventLoop, QTimer

from ui.event_bus import (
    AutonomousDesignCompletedEvent,
    AutonomousDesignStartedEvent,
    AutonomousIterationCompletedEvent,
    EventBus,
    ServiceErrorEvent,
)
from ui.models.autonomous_dto import (
    AutonomousDesignRequestDTO,
    AutonomousIterationDTO,
    AutonomousMetricsDTO,
    AutonomousResultDTO,
)
from ui.pages.autonomous_page import AutonomousDesignWorker, AutonomousPage


class FakeAutonomousService:
    """Fast fake service for page tests."""

    def __init__(self, success: bool = True) -> None:
        self.success = success
        self.requests: list[AutonomousDesignRequestDTO] = []

    def run_design(self, request: AutonomousDesignRequestDTO) -> AutonomousResultDTO:
        self.requests.append(request)
        return AutonomousResultDTO(
            design_id="d1",
            world_id=request.world_id,
            success=self.success,
            summary="Completed" if self.success else "Failed",
            error_message="" if self.success else "designer failed",
        )

    def get_iterations(self) -> list[AutonomousIterationDTO]:
        return [
            AutonomousIterationDTO(
                iteration_id="1",
                iteration_number=1,
                status="completed",
                progress=0.8,
                summary="Use Roshamuul corridor pattern",
            )
        ]

    def get_metrics(self) -> AutonomousMetricsDTO:
        return AutonomousMetricsDTO(
            total_iterations=1,
            successful_runs=1 if self.success else 0,
            failed_runs=0 if self.success else 1,
            status="Converged" if self.success else "Failed",
            success=self.success,
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


def test_autonomous_page_creation(qapp_instance: object) -> None:
    page = AutonomousPage(autonomous_service=FakeAutonomousService())
    assert page.objectName() == "autonomous"
    assert page.control_panel.start_button.text() == "Start"


def test_autonomous_page_builds_request(qapp_instance: object) -> None:
    page = AutonomousPage(autonomous_service=FakeAutonomousService())
    page.goal_panel.set_prompt("Create an Issavi + Roshamuul expansion")
    request = page.build_request()
    assert request.goal.startswith("Create an Issavi")
    assert request.max_iterations == 20
    assert "strategy=Balanced" in request.constraints


def test_worker_execution_calls_service(qapp_instance: object) -> None:
    service = FakeAutonomousService()
    request = AutonomousDesignRequestDTO(goal="Build")
    worker = AutonomousDesignWorker(service, request)
    payloads: list[object] = []
    worker.finished.connect(payloads.append)
    worker.run()
    assert service.requests == [request]
    assert payloads


def test_autonomous_qthread_workflow_and_events(qapp_instance: object) -> None:
    service = FakeAutonomousService()
    events: list[object] = []
    bus = EventBus()
    bus.register(AutonomousDesignStartedEvent, events.append)
    bus.register(AutonomousIterationCompletedEvent, events.append)
    bus.register(AutonomousDesignCompletedEvent, events.append)
    page = AutonomousPage(autonomous_service=service, event_bus=bus)
    page.goal_panel.set_prompt("Create a large endgame continent")
    page.start_design()
    _wait_until(lambda: not page.is_running())
    assert service.requests
    assert page.status_widget.state_value.text() == "Completed"
    assert page.iteration_table.rowCount() == 1
    assert page.decision_feed.list_widget.count() == 1
    assert any(isinstance(event, AutonomousDesignStartedEvent) for event in events)
    assert any(isinstance(event, AutonomousIterationCompletedEvent) for event in events)
    assert any(isinstance(event, AutonomousDesignCompletedEvent) for event in events)


def test_autonomous_service_error_event(qapp_instance: object) -> None:
    events: list[object] = []
    bus = EventBus()
    bus.register(ServiceErrorEvent, events.append)
    page = AutonomousPage(autonomous_service=FakeAutonomousService(success=False), event_bus=bus)
    page.goal_panel.set_prompt("Create a large endgame continent")
    page.start_design()
    _wait_until(lambda: not page.is_running())
    assert page.status_widget.state_value.text() == "Failed"
    assert any(isinstance(event, ServiceErrorEvent) for event in events)


def test_no_direct_core_imports_in_autonomous_page_or_widgets() -> None:
    targets = [
        Path("ui/pages/autonomous_page.py"),
        *Path("ui/widgets").glob("autonomous_*.py"),
    ]
    text = "\n".join(path.read_text(encoding="utf-8") for path in targets)
    assert "import core" not in text
    assert "from core" not in text
    assert "import agents" not in text
    assert "from agents" not in text
