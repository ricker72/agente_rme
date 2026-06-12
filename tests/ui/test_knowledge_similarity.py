"""Tests for knowledge similarity and recommendations."""

from __future__ import annotations

from ui.models.knowledge_dto import KnowledgeResultDTO
from ui.widgets.knowledge_recommendation_panel import KnowledgeRecommendationPanel
from ui.widgets.knowledge_similarity_panel import KnowledgeSimilarityPanel


def test_similarity_panel_renders_results(qapp_instance: object) -> None:
    panel = KnowledgeSimilarityPanel()
    panel.update_results(
        [KnowledgeResultDTO(title="Roshamuul Boss", entry_type="Boss", relevance=0.82)]
    )
    assert panel.table.rowCount() == 1
    name = panel.table.item(0, 0)
    score = panel.table.item(0, 1)
    assert name is not None
    assert score is not None
    assert name.text() == "Roshamuul Boss"
    assert score.text() == "0.82"


def test_recommendation_panel_renders_examples(qapp_instance: object) -> None:
    panel = KnowledgeRecommendationPanel()
    panel.update_recommendations(
        [KnowledgeResultDTO(title="Library Spawn", entry_type="Spawn", relevance=0.9)]
    )
    assert "Reuse Library Spawn Spawn Strategy" in panel.list_widget.item(0).text()


def test_recommendation_panel_empty_state(qapp_instance: object) -> None:
    panel = KnowledgeRecommendationPanel()
    panel.update_recommendations([])
    assert panel.list_widget.item(0).text() == "No recommendations"
