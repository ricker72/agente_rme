"""Visual Critic Studio page."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from ui.event_bus import (
    CriticAnalysisRequestedEvent,
    CriticCompletedEvent,
    EventBus,
    ServiceErrorEvent,
)
from ui.models.critic_dto import CriticDTO, CriticRequestDTO, HeatmapDTO
from ui.services.critic_service import CriticService
from ui.services.null_services import NullCriticService
from ui.widgets.critic_analysis_panel import CriticAnalysisPanel
from ui.widgets.critic_heatmap_viewer import CriticHeatmapViewer
from ui.widgets.critic_issue_list import CriticIssueList
from ui.widgets.critic_recommendation_list import CriticRecommendationList
from ui.widgets.critic_report_summary import CriticReportSummary
from ui.widgets.critic_score_grid import CriticScoreGrid
from ui.widgets.critic_world_selector import CriticWorldSelector


@dataclass(slots=True)
class CriticAnalysisResult:
    """Worker result payload."""

    request: CriticRequestDTO
    report: CriticDTO
    heatmaps: list[HeatmapDTO]


class CriticAnalysisWorker(QObject):
    """Run critic analysis outside the UI thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        service: CriticService,
        request: CriticRequestDTO,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._request = request

    @Slot()
    def run(self) -> None:
        """Execute critic analysis."""
        try:
            report = self._service.analyze_world(self._request)
            heatmaps = self._service.get_heatmaps()
            self.finished.emit(CriticAnalysisResult(self._request, report, heatmaps))
        except Exception as exc:
            self.failed.emit(str(exc) or exc.__class__.__name__)


class CriticPage(QWidget):
    """Production Visual Critic Studio."""

    PAGE_ID = "critic"

    page_loaded = Signal(str)
    analysis_started = Signal(object)
    analysis_finished = Signal(object)

    def __init__(
        self,
        critic_service: CriticService | None = None,
        event_bus: EventBus | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(self.PAGE_ID)
        self.critic_service = critic_service or NullCriticService()
        self.event_bus = event_bus
        self._thread: QThread | None = None
        self._worker: CriticAnalysisWorker | None = None
        self._last_request: CriticRequestDTO | None = None
        self._build_ui()
        self._connect_signals()
        self.page_loaded.emit(self.PAGE_ID)

    def build_request(self) -> CriticRequestDTO:
        """Build the critic request from current UI state."""
        return CriticRequestDTO(
            world_id=self.world_selector.world_id(),
            analysis_profile=self.world_selector.analysis_profile(),
            checks=[
                "visual",
                "navigation",
                "density",
                "spawn",
                "hunt",
                "boss",
                "city",
                "decor",
                "pathfinding",
            ],
        )

    def is_analyzing(self) -> bool:
        """Return True when a worker thread is active."""
        return self._thread is not None and self._thread.isRunning()

    @Slot()
    def on_analyze_clicked(self) -> None:
        """Start non-blocking analysis."""
        if self.is_analyzing():
            return
        request = self.build_request()
        self._last_request = request
        self.action_panel.set_analyzing(True)
        self.analysis_started.emit(request)
        if self.event_bus is not None:
            self.event_bus.emit(
                CriticAnalysisRequestedEvent(
                    request_id=request.world_id,
                    world_id=request.world_id,
                )
            )

        self._thread = QThread(self)
        self._worker = CriticAnalysisWorker(self.critic_service, request)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_analysis_finished)
        self._worker.failed.connect(self._on_analysis_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()

    @Slot()
    def load_last_report(self) -> None:
        """Load the last critic report through the service."""
        try:
            report = self.critic_service.get_last_report()
            heatmaps = self.critic_service.get_heatmaps()
            self._apply_report(report, heatmaps)
        except Exception as exc:
            self._emit_service_error(str(exc) or exc.__class__.__name__)

    @Slot()
    def refresh_heatmaps(self) -> None:
        """Refresh heatmaps through the service."""
        try:
            self.heatmap_viewer.update_heatmaps(self.critic_service.get_heatmaps())
        except Exception as exc:
            self._emit_service_error(str(exc) or exc.__class__.__name__)

    @Slot(object)
    def _on_analysis_finished(self, payload: object) -> None:
        result = payload if isinstance(payload, CriticAnalysisResult) else None
        if result is None:
            self._on_analysis_failed("Invalid worker result")
            return
        self._apply_report(result.report, result.heatmaps)
        self.action_panel.set_analyzing(False)
        self.analysis_finished.emit(result.report)
        if self.event_bus is not None:
            self.event_bus.emit(
                CriticCompletedEvent(
                    analysis_id=result.report.analysis_id,
                    score=result.report.score,
                    issue_count=len(result.report.issues),
                )
            )
            if not result.report.success:
                self._emit_service_error(
                    result.report.error_message or result.report.summary
                )

    @Slot(str)
    def _on_analysis_failed(self, message: str) -> None:
        self.action_panel.set_analyzing(False)
        self._emit_service_error(message)

    @Slot()
    def _cleanup_worker(self) -> None:
        self._worker = None
        self._thread = None

    def _apply_report(self, report: CriticDTO, heatmaps: list[HeatmapDTO]) -> None:
        self.score_grid.update_scores(report)
        self.issue_list.update_issues(report.issues)
        self.recommendation_list.update_recommendations(report.suggestions)
        self.report_summary.update_report(report)
        self.heatmap_viewer.update_heatmaps(heatmaps)

    def _emit_service_error(self, message: str) -> None:
        if self.event_bus is not None:
            self.event_bus.emit(
                ServiceErrorEvent(
                    service_name="critic",
                    operation="analyze_world",
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

        self.world_selector = CriticWorldSelector(content)
        self.action_panel = CriticAnalysisPanel(content)
        self.score_grid = CriticScoreGrid(content)
        self.issue_list = CriticIssueList(content)
        self.recommendation_list = CriticRecommendationList(content)
        self.report_summary = CriticReportSummary(content)
        self.heatmap_viewer = CriticHeatmapViewer(content)

        layout.addWidget(self.world_selector)
        layout.addWidget(self.action_panel)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.score_grid, 2)
        side_grid = QGridLayout()
        side_grid.addWidget(self.report_summary, 0, 0)
        side_grid.addWidget(self.issue_list, 1, 0)
        side_grid.addWidget(self.recommendation_list, 2, 0)
        main_layout.addLayout(side_grid, 1)
        layout.addLayout(main_layout)

        layout.addWidget(self.heatmap_viewer)
        layout.addStretch()

        scroll_area.setWidget(content)
        outer.addWidget(scroll_area)

    def _connect_signals(self) -> None:
        self.action_panel.analyze_button.clicked.connect(self.on_analyze_clicked)
        self.action_panel.load_last_button.clicked.connect(self.load_last_report)
        self.action_panel.refresh_heatmaps_button.clicked.connect(self.refresh_heatmaps)
