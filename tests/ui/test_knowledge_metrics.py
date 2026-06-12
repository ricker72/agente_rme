"""Tests for knowledge metrics widgets."""

from __future__ import annotations

from ui.models.knowledge_dto import KnowledgeMetricsDTO
from ui.widgets.knowledge_dataset_summary import KnowledgeDatasetSummary
from ui.widgets.knowledge_metrics_widget import KnowledgeMetricsWidget


def test_metrics_widget_renders_values(qapp_instance: object) -> None:
    widget = KnowledgeMetricsWidget()
    widget.update_metrics(KnowledgeMetricsDTO(total_entries=12, status="Loaded", success=True))
    assert widget.dataset_entries_value.text() == "12"
    assert widget.coverage_value.text() == "100%"
    assert widget.status_value.text() == "Loaded"


def test_dataset_summary_renders_values(qapp_instance: object) -> None:
    widget = KnowledgeDatasetSummary()
    widget.update_summary(
        KnowledgeMetricsDTO(total_entries=8, indexed_sources=2, status="Loaded")
    )
    assert "8 entries" in widget.summary_label.text()
    assert "2 sources" in widget.summary_label.text()
