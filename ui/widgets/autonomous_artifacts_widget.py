"""Artifact status widget for Autonomous Designer Workspace."""

from __future__ import annotations

from PySide6.QtWidgets import QGroupBox, QListWidget, QVBoxLayout, QWidget

from ui.models.autonomous_dto import AutonomousResultDTO


class AutonomousArtifactsWidget(QGroupBox):
    """Display service-derived artifact availability."""

    ARTIFACTS = [
        "autonomous_history.json",
        "autonomous_decisions.json",
        "autonomous_iterations.json",
        "autonomous_metrics.json",
        "generated.otbm",
        "generated.lua",
        "preview.png",
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Artifacts", parent)
        self.list_widget = QListWidget(self)
        self._build_ui()

    def update_artifacts(self, result: AutonomousResultDTO | None) -> None:
        """Render artifact availability from service result status."""
        self.list_widget.clear()
        available = result is not None and result.success
        for artifact in self.ARTIFACTS:
            status = "Available" if available else "Unavailable"
            self.list_widget.addItem(f"{artifact}: {status}")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        self.update_artifacts(None)
