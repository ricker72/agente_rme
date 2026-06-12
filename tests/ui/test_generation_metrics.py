"""Tests for generation metrics rendering."""

from __future__ import annotations

from ui.models.world_dto import WorldDTO
from ui.widgets.generation_metrics_widget import GenerationMetrics, GenerationMetricsWidget
from ui.widgets.generation_summary_widget import GenerationSummaryWidget


def test_metrics_rendering(qapp_instance: object) -> None:
    widget = GenerationMetricsWidget()
    metrics = GenerationMetrics(
        duration_seconds=2.5,
        success=True,
        generated_regions=2,
        generated_hunts=1,
        generated_cities=1,
    )
    widget.update_metrics(metrics)
    assert widget.duration_value.text() == "2.50s"
    assert widget.success_value.text() == "Yes"
    assert widget.regions_value.text() == "2"


def test_metrics_build_from_world(qapp_instance: object) -> None:
    widget = GenerationMetricsWidget()
    world = WorldDTO(width=256, success=True)
    metrics = widget.build_metrics(world, 1.0, "Expansion")
    assert metrics.generated_regions == 2
    assert metrics.generated_hunts == 1
    assert metrics.generated_cities == 1


def test_summary_rendering(qapp_instance: object) -> None:
    widget = GenerationSummaryWidget()
    world = WorldDTO(name="World", description="42 tiles generated", status="Generated")
    widget.update_summary(world, "Issavi", "300-500", 1.5)
    assert widget.name_value.text() == "World"
    assert widget.tile_count_value.text() == "42"
    assert widget.duration_value.text() == "1.50s"
