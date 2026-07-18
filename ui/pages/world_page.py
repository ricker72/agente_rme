"""World Generation Studio page."""

from __future__ import annotations

import time
from dataclasses import dataclass

from PySide6.QtCore import QObject, QSettings, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QGridLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ui.event_bus import (
    EventBus,
    ServiceErrorEvent,
    WorldGeneratedEvent,
    WorldGenerationRequestedEvent,
)
from ui.models.world_dto import WorldDTO, WorldGenerationRequestDTO
from ui.services.null_services import NullWorldService
from ui.services.world_service import WorldService
from ui.widgets.generation_history_widget import (
    GenerationHistoryEntry,
    GenerationHistoryWidget,
)
from ui.widgets.generation_metrics_widget import GenerationMetricsWidget
from ui.widgets.generation_progress_widget import GenerationProgressWidget
from ui.widgets.generation_settings_panel import GenerationSettingsPanel
from ui.widgets.generation_summary_widget import GenerationSummaryWidget
from ui.widgets.world_preview_widget import WorldPreviewWidget
from ui.widgets.world_prompt_panel import WorldPromptPanel


@dataclass(slots=True)
class GenerationResult:
    """Worker result payload."""

    request: WorldGenerationRequestDTO
    world: WorldDTO
    duration_seconds: float


class WorldGenerationWorker(QObject):
    """Run world generation through WorldService outside the UI thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        service: WorldService,
        request: WorldGenerationRequestDTO,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._request = request

    @Slot()
    def run(self) -> None:
        """Execute the generation request."""
        started = time.perf_counter()
        try:
            world = self._service.generate_world(self._request)
            duration = time.perf_counter() - started
            self.finished.emit(GenerationResult(self._request, world, duration))
        except Exception as exc:
            self.failed.emit(str(exc) or exc.__class__.__name__)


class WorldPage(QWidget):
    """Production world generation studio."""

    PAGE_ID = "world"

    page_loaded = Signal(str)
    generation_started = Signal(object)
    generation_finished = Signal(object)

    def __init__(
        self,
        world_service: WorldService | None = None,
        event_bus: EventBus | None = None,
        settings: QSettings | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(self.PAGE_ID)
        self.world_service = world_service or NullWorldService()
        self.event_bus = event_bus
        self.settings = settings or QSettings("AgenteRME", "Studio")
        self._thread: QThread | None = None
        self._worker: WorldGenerationWorker | None = None
        self._last_request: WorldGenerationRequestDTO | None = None
        self._build_ui()
        self._connect_signals()
        self.page_loaded.emit(self.PAGE_ID)

    def build_request(self) -> WorldGenerationRequestDTO:
        """Build a WorldGenerationRequestDTO from current UI state."""
        prompt = self.prompt_panel.prompt()
        settings = self.settings_panel.settings()
        width, height = self.settings_panel.dimensions()
        name = self._world_name(prompt, settings.theme)
        return WorldGenerationRequestDTO(
            name=name,
            width=width,
            height=height,
            theme=settings.theme,
            constraints=[
                f"prompt={prompt}",
                f"level_min={settings.min_level}",
                f"level_max={settings.max_level}",
                f"mode={settings.mode}",
                f"size={settings.size}",
            ],
        )

    def is_generating(self) -> bool:
        """Return True when a worker thread is active."""
        return self._thread is not None and self._thread.isRunning()

    @Slot()
    def on_generate_clicked(self) -> None:
        """Start the non-blocking generation workflow."""
        if self.is_generating():
            return
        if not self.prompt_panel.is_valid() or not self.settings_panel.is_valid():
            self.progress_widget.complete(False, "Invalid generation input")
            return

        request = self.build_request()
        self._last_request = request
        self.generate_button.setEnabled(False)
        self.progress_widget.start()
        self.generation_started.emit(request)
        if self.event_bus is not None:
            self.event_bus.emit(
                WorldGenerationRequestedEvent(
                    request_id=request.name,
                    world_name=request.name,
                )
            )

        self._thread = QThread(self)
        self._worker = WorldGenerationWorker(self.world_service, request)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_generation_finished)
        self._worker.failed.connect(self._on_generation_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()

    @Slot(object)
    def _on_generation_finished(self, payload: object) -> None:
        result = payload if isinstance(payload, GenerationResult) else None
        if result is None:
            self._on_generation_failed("Invalid worker result")
            return
        settings = self.settings_panel.settings()
        level_range = f"{settings.min_level}-{settings.max_level}"
        world = result.world

        self.progress_widget.complete(world.success, world.status)
        self.summary_widget.update_summary(
            world,
            settings.theme,
            level_range,
            result.duration_seconds,
        )
        metrics = self.metrics_widget.build_metrics(
            world,
            result.duration_seconds,
            settings.mode,
        )
        self.metrics_widget.update_metrics(metrics)
        self.preview_widget.load_preview()
        self.history_widget.add_entry(
            GenerationHistoryEntry(
                name=world.name or result.request.name,
                theme=settings.theme,
                level_range=level_range,
                status=world.status,
                duration_seconds=result.duration_seconds,
            )
        )
        self.generate_button.setEnabled(True)
        self.generation_finished.emit(world)
        if self.event_bus is not None:
            self.event_bus.emit(
                WorldGeneratedEvent(
                    world_id=world.world_id,
                    world_name=world.name,
                    success=world.success,
                    message=world.status,
                )
            )
            if not world.success:
                self.event_bus.emit(
                    ServiceErrorEvent(
                        service_name="world",
                        operation="generate_world",
                        message=world.error_message or world.status,
                    )
                )

    @Slot(str)
    def _on_generation_failed(self, message: str) -> None:
        self.progress_widget.complete(False, "Generation failed")
        self.generate_button.setEnabled(True)
        if self.event_bus is not None:
            self.event_bus.emit(
                ServiceErrorEvent(
                    service_name="world",
                    operation="generate_world",
                    message=message,
                )
            )

    @Slot()
    def _cleanup_worker(self) -> None:
        self._worker = None
        self._thread = None

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        content = QWidget(scroll_area)
        layout = QVBoxLayout(content)
        layout.setSpacing(14)

        self.prompt_panel = WorldPromptPanel(content)
        self.settings_panel = GenerationSettingsPanel(content)
        self.generate_button = QPushButton("Generate", content)
        self.generate_button.setMinimumHeight(40)
        self.progress_widget = GenerationProgressWidget(content)
        self.summary_widget = GenerationSummaryWidget(content)
        self.metrics_widget = GenerationMetricsWidget(content)
        self.preview_widget = WorldPreviewWidget(content)
        self.history_widget = GenerationHistoryWidget(self.settings, content)

        layout.addWidget(self.prompt_panel)
        layout.addWidget(self.settings_panel)
        layout.addWidget(self.generate_button)
        layout.addWidget(self.progress_widget)

        result_grid = QGridLayout()
        result_grid.setSpacing(12)
        result_grid.addWidget(self.summary_widget, 0, 0)
        result_grid.addWidget(self.metrics_widget, 0, 1)
        result_grid.addWidget(self.preview_widget, 0, 2)
        layout.addLayout(result_grid)

        layout.addWidget(self.history_widget)
        layout.addStretch()

        scroll_area.setWidget(content)
        outer.addWidget(scroll_area)

    def _connect_signals(self) -> None:
        self.generate_button.clicked.connect(self.on_generate_clicked)

    @staticmethod
    def _world_name(prompt: str, theme: str) -> str:
        words = [word.strip(" ,.;:") for word in prompt.split() if word.strip(" ,.;:")]
        suffix = " ".join(words[:4]) if words else "Generated World"
        return f"{theme} - {suffix}"
