"""Tests for knowledge search and filters widgets."""

from __future__ import annotations

from ui.widgets.knowledge_filters_widget import KnowledgeFiltersWidget
from ui.widgets.knowledge_search_panel import KnowledgeSearchPanel


def test_search_panel_query_and_clear(qapp_instance: object) -> None:
    panel = KnowledgeSearchPanel()
    panel.query_edit.setText("Issavi Hunt")
    assert panel.query_text() == "Issavi Hunt"
    panel.clear()
    assert panel.query_text() == ""


def test_search_panel_examples(qapp_instance: object) -> None:
    panel = KnowledgeSearchPanel()
    panel.example_combo.setCurrentText("Falcon City")
    assert panel.query_text() == "Falcon City"


def test_filters_selected_types(qapp_instance: object) -> None:
    widget = KnowledgeFiltersWidget()
    widget.set_selected_types(["City", "Hunt"])
    assert widget.selected_types() == ["City", "Hunt"]
