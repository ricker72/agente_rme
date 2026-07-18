"""Autonomous Designer Workspace page."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

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
from ui.services.autonomous_service import AutonomousService
from ui.services.null_services import NullAutonomousService
from ui.widgets.autonomous_artifacts_widget import AutonomousArtifactsWidget
from ui.widgets.autonomous_chart_viewer import AutonomousChartViewer
from ui.widgets.autonomous_constraints_panel import AutonomousConstraintsPanel
from ui.widgets.autonomous_control_panel import AutonomousControlPanel
from ui.widgets.autonomous_decision_feed import AutonomousDecisionFeed
from ui.widgets.autonomous_goal_panel import AutonomousGoalPanel
from ui.widgets.autonomous_iteration_table import AutonomousIterationTable
from ui.widgets.autonomous_metrics_widget import AutonomousMetricsWidget
from ui.widgets.autonomous_status_widget import AutonomousStatusWidget


@dataclass(slots=True)
class AutonomousRunPayload:
    """Worker result payload."""

    request: AutonomousDesignRequestDTO
    result: AutonomousResultDTO
    iterations: list[AutonomousIterationDTO]
    metrics: AutonomousMetricsDTO


class AutonomousDesignWorker(QObject):
    """Run autonomous design outside the UI thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        service: AutonomousService,
        request: AutonomousDesignRequestDTO,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._request = request

    @Slot()
    def run(self) -> None:
        """Execute the autonomous design request."""
        try:
            result = self._service.run_design(self._request)
            iterations = self._service.get_iterations()
            metrics = self._service.get_metrics()
            self.finished.emit(
                AutonomousRunPayload(self._request, result, iterations, metrics)
            )
        except Exception as exc:
            self.failed.emit(str(exc) or exc.__class__.__name__)


class AutonomousPage(QWidget):
    """Production Autonomous Designer Workspace."""

    PAGE_ID = "autonomous"

    page_loaded = Signal(str)
    run_started = Signal(object)
    run_finished = Signal(object)

    def __init__(
        self,
        autonomous_service: AutonomousService | None = None,
        event_bus: EventBus | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(self.PAGE_ID)
        self.autonomous_service = autonomous_service or NullAutonomousService()
        self.event_bus = event_bus
        self._thread: QThread | None = None
        self._worker: AutonomousDesignWorker | None = None
        self._build_ui()
        self._connect_signals()
        self._load_service_state()
        self.page_loaded.emit(self.PAGE_ID)

    def build_request(self) -> AutonomousDesignRequestDTO:
        """Build an AutonomousDesignRequestDTO from the UI state."""
        goal = self.goal_panel.settings()
        constraints = self.constraints_panel.constraints()
        return AutonomousDesignRequestDTO(
            world_id="autonomous-design",
            goal=goal.prompt,
            max_iterations=goal.max_iterations,
            constraints=[
                f"target_score={goal.target_score}",
                f"world_size={constraints.world_size}",
                f"strategy={constraints.strategy}",
                f"level_min={constraints.min_level}",
                f"level_max={constraints.max_level}",
                f"use_knowledge={constraints.use_knowledge}",
                f"use_blueprints={constraints.use_blueprints}",
                f"use_visual_critic={constraints.use_visual_critic}",
                f"use_evolution={constraints.use_evolution}",
            ],
        )

    def is_running(self) -> bool:
        """Return True when the worker thread is active."""
        return self._thread is not None and self._thread.isRunning()

    @Slot()
    def start_design(self) -> None:
        """Start non-blocking autonomous design."""
        if self.is_running():
            return
        if not self.goal_panel.is_valid() or not self.constraints_panel.is_valid():
            self.status_widget.update_status("Invalid", "Check goal and constraints")
            return

        request = self.build_request()
        self.control_panel.set_running(True)
        self.status_widget.update_status("Running", request.goal)
        self.run_started.emit(request)
        if self.event_bus is not None:
            self.event_bus.emit(
                AutonomousDesignStartedEvent(
                    design_id=request.world_id,
                    world_id=request.world_id,
                )
            )

        self._thread = QThread(self)
        self._worker = AutonomousDesignWorker(self.autonomous_service, request)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_design_finished)
        self._worker.failed.connect(self._on_design_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()

    @Slot()
    def export_best_result(self) -> None:
        """Emit a UI-only export status until service export is available."""
        self.status_widget.update_status("Export requested", "Export best result is pending service support")

    @Slot(object)
    def _on_design_finished(self, payload: object) -> None:
        result = payload if isinstance(payload, AutonomousRunPayload) else None
        if result is None:
            self._on_design_failed("Invalid worker result")
            return
        target = self.goal_panel.settings().target_score
        self._apply_result(result, target)
        self.control_panel.set_running(False)
        self.run_finished.emit(result.result)
        if self.event_bus is not None:
            for iteration in result.iterations:
                self.event_bus.emit(
                    AutonomousIterationCompletedEvent(
                        design_id=result.result.design_id,
                        iteration_number=iteration.iteration_number,
                        success=iteration.status.lower() != "error",
                        message=iteration.summary,
                    )
                )
            self.event_bus.emit(
                AutonomousDesignCompletedEvent(
                    design_id=result.result.design_id,
                    world_id=result.result.world_id,
                    success=result.result.success,
                    message=result.result.summary,
                )
            )
            if not result.result.success:
                self._emit_service_error(
                    result.result.error_message or result.result.summary
                )

    @Slot(str)
    def _on_design_failed(self, message: str) -> None:
        self.control_panel.set_running(False)
        self.status_widget.update_status("Failed", message)
        self._emit_service_error(message)

    @Slot()
    def _cleanup_worker(self) -> None:
        self._worker = None
        self._thread = None

    def _apply_result(self, payload: AutonomousRunPayload, target_score: int) -> None:
        self.status_widget.update_status(
            "Completed" if payload.result.success else "Failed",
            payload.result.summary,
        )
        self.metrics_widget.update_metrics(payload.metrics, target_score)
        self.iteration_table.update_iterations(payload.iterations)
        self.decision_feed.update_from_iterations(payload.iterations)
        self.chart_viewer.refresh_charts()
        self.artifacts_widget.update_artifacts(payload.result)

    def _load_service_state(self) -> None:
        try:
            metrics = self.autonomous_service.get_metrics()
            iterations = self.autonomous_service.get_iterations()
            self.metrics_widget.update_metrics(metrics, self.goal_panel.settings().target_score)
            self.iteration_table.update_iterations(iterations)
            self.decision_feed.update_from_iterations(iterations)
        except Exception as exc:
            self._emit_service_error(str(exc) or exc.__class__.__name__)

    def _emit_service_error(self, message: str) -> None:
        if self.event_bus is not None:
            self.event_bus.emit(
                ServiceErrorEvent(
                    service_name="autonomous",
                    operation="run_design",
                    message=message,
                )
            )

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        content = QWidget(scroll_area)
        layout = QVBoxLayout(content)
        layout.setSpacing(14)

        self.goal_panel = AutonomousGoalPanel(content)
        self.constraints_panel = AutonomousConstraintsPanel(content)
        self.control_panel = AutonomousControlPanel(content)
        self.status_widget = AutonomousStatusWidget(content)
        self.metrics_widget = AutonomousMetricsWidget(content)
        self.iteration_table = AutonomousIterationTable(content)
        self.decision_feed = AutonomousDecisionFeed(content)
        self.chart_viewer = AutonomousChartViewer(content)
        self.artifacts_widget = AutonomousArtifactsWidget(content)

        top = QHBoxLayout()
        left = QVBoxLayout()
        left.addWidget(self.goal_panel)
        left.addWidget(self.constraints_panel)
        left.addWidget(self.control_panel)
        top.addLayout(left, 1)

        center = QVBoxLayout()
        center.addWidget(self.status_widget)
        center.addWidget(self.metrics_widget)
        center.addWidget(self.chart_viewer)
        top.addLayout(center, 1)

        right = QVBoxLayout()
        right.addWidget(self.decision_feed)
        right.addWidget(self.artifacts_widget)
        top.addLayout(right, 1)

        layout.addLayout(top)
        bottom = QGridLayout()
        bottom.addWidget(self.iteration_table, 0, 0)
        layout.addLayout(bottom)
        layout.addStretch()

        scroll_area.setWidget(content)
        outer.addWidget(scroll_area)

    def _connect_signals(self) -> None:
        self.control_panel.start_button.clicked.connect(self.start_design)
        self.control_panel.export_button.clicked.connect(self.export_best_result)
