"""Tests for the World Generation Studio page."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QEventLoop, QSettings, QTimer

from ui.event_bus import (
    EventBus,
    ServiceErrorEvent,
    WorldGeneratedEvent,
    WorldGenerationRequestedEvent,
)
from ui.models.world_dto import WorldDTO, WorldGenerationRequestDTO
from ui.pages.world_page import WorldGenerationWorker, WorldPage


class FakeWorldService:
    """Fast fake service for page tests."""

    def __init__(self, success: bool = True) -> None:
        self.success = success
        self.requests: list[WorldGenerationRequestDTO] = []

    def generate_world(self, request: WorldGenerationRequestDTO) -> WorldDTO:
        self.requests.append(request)
        return WorldDTO(
            world_id="w1",
            name=request.name,
            width=request.width,
            height=request.height,
            description="64 tiles generated",
            status="Generated" if self.success else "Core unavailable",
            success=self.success,
            error_message="" if self.success else "core down",
        )

    def get_recent_worlds(self) -> list[WorldDTO]:
        return []

    def get_world_summary(self, world_id: str) -> Any:
        return None


def _settings(path: Path) -> QSettings:
    return QSettings(str(path), QSettings.Format.IniFormat)


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


def test_world_page_creation(qapp_instance: object, tmp_path: Path) -> None:
    page = WorldPage(world_service=FakeWorldService(), settings=_settings(tmp_path / "s.ini"))
    assert page.objectName() == "world"
    assert page.generate_button.text() == "Generate"
    assert page.prompt_panel is not None


def test_world_page_builds_dto(qapp_instance: object, tmp_path: Path) -> None:
    page = WorldPage(world_service=FakeWorldService(), settings=_settings(tmp_path / "s.ini"))
    page.prompt_panel.set_prompt("Create an Issavi expansion for levels 300-500")
    page.settings_panel.theme_combo.setCurrentText("Issavi")
    request = page.build_request()
    assert isinstance(request, WorldGenerationRequestDTO)
    assert request.theme == "Issavi"
    assert request.width == 256
    assert any(item == "mode=Standard" for item in request.constraints)


def test_worker_execution_calls_service(qapp_instance: object) -> None:
    service = FakeWorldService()
    request = WorldGenerationRequestDTO(name="Test")
    worker = WorldGenerationWorker(service, request)
    payloads: list[object] = []
    worker.finished.connect(payloads.append)
    worker.run()
    assert service.requests == [request]
    assert payloads


def test_generate_workflow_updates_ui_and_history(qapp_instance: object, tmp_path: Path) -> None:
    service = FakeWorldService()
    events: list[object] = []
    bus = EventBus()
    bus.register(WorldGenerationRequestedEvent, events.append)
    bus.register(WorldGeneratedEvent, events.append)
    page = WorldPage(
        world_service=service,
        event_bus=bus,
        settings=_settings(tmp_path / "s.ini"),
    )
    page.prompt_panel.set_prompt("Create an Issavi expansion for levels 300-500")
    page.on_generate_clicked()
    _wait_until(lambda: not page.is_generating())

    assert service.requests
    assert page.summary_widget.status_value.text() == "Generated"
    assert page.metrics_widget.success_value.text() == "Yes"
    assert page.history_widget.list_widget.count() == 1
    assert any(isinstance(event, WorldGenerationRequestedEvent) for event in events)
    assert any(isinstance(event, WorldGeneratedEvent) for event in events)


def test_generate_failure_emits_service_error(qapp_instance: object, tmp_path: Path) -> None:
    events: list[object] = []
    bus = EventBus()
    bus.register(ServiceErrorEvent, events.append)
    page = WorldPage(
        world_service=FakeWorldService(success=False),
        event_bus=bus,
        settings=_settings(tmp_path / "s.ini"),
    )
    page.prompt_panel.set_prompt("Generate a Roshamuul hunting area")
    page.on_generate_clicked()
    _wait_until(lambda: not page.is_generating())
    assert page.metrics_widget.success_value.text() == "No"
    assert any(isinstance(event, ServiceErrorEvent) for event in events)
