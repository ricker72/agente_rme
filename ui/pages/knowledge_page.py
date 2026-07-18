"""Knowledge Explorer page."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

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
from ui.services.knowledge_service import KnowledgeService
from ui.services.null_services import NullKnowledgeService
from ui.widgets.knowledge_dataset_summary import KnowledgeDatasetSummary
from ui.widgets.knowledge_entry_viewer import KnowledgeEntryViewer
from ui.widgets.knowledge_filters_widget import KnowledgeFiltersWidget
from ui.widgets.knowledge_metrics_widget import KnowledgeMetricsWidget
from ui.widgets.knowledge_recommendation_panel import KnowledgeRecommendationPanel
from ui.widgets.knowledge_results_table import KnowledgeResultsTable
from ui.widgets.knowledge_search_panel import KnowledgeSearchPanel
from ui.widgets.knowledge_similarity_panel import KnowledgeSimilarityPanel


@dataclass(slots=True)
class KnowledgeSearchResult:
    """Worker search result payload."""

    query: KnowledgeQueryDTO
    results: list[KnowledgeResultDTO]
    metrics: KnowledgeMetricsDTO


class KnowledgeSearchWorker(QObject):
    """Run knowledge search outside the UI thread."""

    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        service: KnowledgeService,
        query: KnowledgeQueryDTO,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = service
        self._query = query

    @Slot()
    def run(self) -> None:
        """Execute the search request."""
        try:
            results = self._service.search(self._query)
            metrics = self._service.get_metrics()
            self.finished.emit(KnowledgeSearchResult(self._query, results, metrics))
        except Exception as exc:
            self.failed.emit(str(exc) or exc.__class__.__name__)


class KnowledgePage(QWidget):
    """Production Knowledge Explorer."""

    PAGE_ID = "knowledge"

    page_loaded = Signal(str)
    search_started = Signal(object)
    search_finished = Signal(object)

    def __init__(
        self,
        knowledge_service: KnowledgeService | None = None,
        event_bus: EventBus | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName(self.PAGE_ID)
        self.knowledge_service = knowledge_service or NullKnowledgeService()
        self.event_bus = event_bus
        self._thread: QThread | None = None
        self._worker: KnowledgeSearchWorker | None = None
        self._selected_entry: KnowledgeResultDTO | None = None
        self._build_ui()
        self._connect_signals()
        self._load_metrics()
        self.page_loaded.emit(self.PAGE_ID)

    def build_query(self) -> KnowledgeQueryDTO:
        """Build a KnowledgeQueryDTO from current UI state."""
        return KnowledgeQueryDTO(
            text=self.search_panel.query_text(),
            limit=25,
            entry_types=self.filters_widget.selected_types(),
        )

    def is_searching(self) -> bool:
        """Return True when search worker is active."""
        return self._thread is not None and self._thread.isRunning()

    @Slot()
    def on_search_clicked(self) -> None:
        """Start a non-blocking search."""
        if self.is_searching():
            return
        query = self.build_query()
        self.search_panel.search_button.setEnabled(False)
        self.search_started.emit(query)
        if self.event_bus is not None:
            self.event_bus.emit(
                KnowledgeQueryRequestedEvent(
                    request_id=query.text,
                    query=query.text,
                )
            )
        self._thread = QThread(self)
        self._worker = KnowledgeSearchWorker(self.knowledge_service, query)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_search_finished)
        self._worker.failed.connect(self._on_search_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()

    @Slot()
    def find_similar(self) -> None:
        """Find similar entries for the selected result."""
        if self._selected_entry is None:
            self.similarity_panel.update_results([])
            return
        try:
            results = self.knowledge_service.find_similar(
                self._selected_entry.title,
                self._selected_entry.entry_type,
            )
            self.similarity_panel.update_results(results)
        except Exception as exc:
            self._emit_service_error(str(exc) or exc.__class__.__name__)

    @Slot(object)
    def _on_search_finished(self, payload: object) -> None:
        result = payload if isinstance(payload, KnowledgeSearchResult) else None
        if result is None:
            self._on_search_failed("Invalid worker result")
            return
        self.results_table.update_results(result.results)
        self.recommendation_panel.update_recommendations(result.results)
        self.metrics_widget.update_metrics(result.metrics)
        self.dataset_summary.update_summary(result.metrics)
        self.search_panel.search_button.setEnabled(True)
        self.search_finished.emit(result.results)
        if self.event_bus is not None:
            self.event_bus.emit(
                KnowledgeQueryCompletedEvent(
                    request_id=result.query.text,
                    query=result.query.text,
                    result_count=len(result.results),
                )
            )
            if not result.metrics.success and result.metrics.error_message:
                self._emit_service_error(result.metrics.error_message)

    @Slot(str)
    def _on_search_failed(self, message: str) -> None:
        self.search_panel.search_button.setEnabled(True)
        self._emit_service_error(message)

    @Slot()
    def _cleanup_worker(self) -> None:
        self._worker = None
        self._thread = None

    @Slot(object)
    def _on_result_selected(self, payload: object) -> None:
        entry = payload if isinstance(payload, KnowledgeResultDTO) else None
        self._selected_entry = entry
        self.entry_viewer.display_entry(entry)

    def _load_metrics(self) -> None:
        try:
            metrics = self.knowledge_service.get_metrics()
            self.metrics_widget.update_metrics(metrics)
            self.dataset_summary.update_summary(metrics)
        except Exception as exc:
            self._emit_service_error(str(exc) or exc.__class__.__name__)

    def _emit_service_error(self, message: str) -> None:
        if self.event_bus is not None:
            self.event_bus.emit(
                ServiceErrorEvent(
                    service_name="knowledge",
                    operation="search",
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

        self.search_panel = KnowledgeSearchPanel(content)
        self.filters_widget = KnowledgeFiltersWidget(content)
        self.results_table = KnowledgeResultsTable(content)
        self.entry_viewer = KnowledgeEntryViewer(content)
        self.metrics_widget = KnowledgeMetricsWidget(content)
        self.dataset_summary = KnowledgeDatasetSummary(content)
        self.similarity_panel = KnowledgeSimilarityPanel(content)
        self.recommendation_panel = KnowledgeRecommendationPanel(content)

        layout.addWidget(self.search_panel)
        layout.addWidget(self.filters_widget)

        center = QHBoxLayout()
        center.addWidget(self.results_table, 2)
        center.addWidget(self.entry_viewer, 1)
        layout.addLayout(center)

        bottom = QGridLayout()
        bottom.addWidget(self.metrics_widget, 0, 0)
        bottom.addWidget(self.dataset_summary, 0, 1)
        bottom.addWidget(self.similarity_panel, 1, 0)
        bottom.addWidget(self.recommendation_panel, 1, 1)
        layout.addLayout(bottom)
        layout.addStretch()

        scroll_area.setWidget(content)
        outer.addWidget(scroll_area)

    def _connect_signals(self) -> None:
        self.search_panel.search_button.clicked.connect(self.on_search_clicked)
        self.results_table.result_selected.connect(self._on_result_selected)
        self.similarity_panel.find_button.clicked.connect(self.find_similar)
