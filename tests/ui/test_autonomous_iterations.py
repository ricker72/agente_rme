"""Tests for autonomous iteration table and artifacts."""

from __future__ import annotations

from ui.models.autonomous_dto import AutonomousIterationDTO, AutonomousResultDTO
from ui.widgets.autonomous_artifacts_widget import AutonomousArtifactsWidget
from ui.widgets.autonomous_iteration_table import AutonomousIterationTable


def test_iteration_table_rendering(qapp_instance: object) -> None:
    table = AutonomousIterationTable()
    table.update_iterations(
        [
            AutonomousIterationDTO(
                iteration_number=1,
                progress=0.5,
                status="completed",
                summary="First pass",
            )
        ]
    )
    assert table.rowCount() == 1
    item = table.item(0, 0)
    assert item is not None
    assert item.text() == "1"


def test_artifacts_widget_status(qapp_instance: object) -> None:
    widget = AutonomousArtifactsWidget()
    widget.update_artifacts(AutonomousResultDTO(success=True))
    assert "Available" in widget.list_widget.item(0).text()
    widget.update_artifacts(None)
    assert "Unavailable" in widget.list_widget.item(0).text()
