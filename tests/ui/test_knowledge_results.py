"""Tests for knowledge results and entry viewer."""

from __future__ import annotations

from ui.models.knowledge_dto import KnowledgeResultDTO
from ui.widgets.knowledge_entry_viewer import KnowledgeEntryViewer
from ui.widgets.knowledge_results_table import KnowledgeResultsTable


def _entry() -> KnowledgeResultDTO:
    return KnowledgeResultDTO(
        identifier="k1",
        title="Issavi Hunt",
        entry_type="Hunt",
        excerpt="A level 300 hunt.",
        tags=["level:300-500", "issavi"],
        source="dataset",
        relevance=0.91,
    )


def test_results_table_renders_rows(qapp_instance: object) -> None:
    table = KnowledgeResultsTable()
    table.update_results([_entry()])
    assert table.rowCount() == 1
    name = table.item(0, 0)
    level = table.item(0, 2)
    similarity = table.item(0, 4)
    assert name is not None
    assert level is not None
    assert similarity is not None
    assert name.text() == "Issavi Hunt"
    assert level.text() == "300-500"
    assert similarity.text() == "0.91"


def test_results_table_selection_emits_dto(qapp_instance: object) -> None:
    table = KnowledgeResultsTable()
    seen: list[object] = []
    table.result_selected.connect(seen.append)
    table.update_results([_entry()])
    table.selectRow(0)
    assert seen


def test_entry_viewer_displays_dto(qapp_instance: object) -> None:
    viewer = KnowledgeEntryViewer()
    viewer.display_entry(_entry())
    assert viewer.name_value.text() == "Issavi Hunt"
    assert viewer.level_range_value.text() == "300-500"
    assert "level:300-500" in viewer.tags_value.text()
