"""Score card for the Visual Critic Studio."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class CriticScoreCard(QFrame):
    """Render one critic score."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.title_label = QLabel(title, self)
        self.score_label = QLabel("-", self)
        self.status_label = QLabel("No data", self)
        self._build_ui()

    def update_score(self, score: float | None) -> None:
        """Update score display."""
        if score is None:
            self.score_label.setText("-")
            self.status_label.setText("No data")
            return
        value = max(0.0, min(100.0, score))
        self.score_label.setText(f"{value:.1f}")
        if value >= 85:
            status = "Excellent"
        elif value >= 70:
            status = "Good"
        elif value >= 50:
            status = "Needs work"
        else:
            status = "Critical"
        self.status_label.setText(status)

    def _build_ui(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        self.title_label.setStyleSheet("font-weight: 600;")
        self.score_label.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(self.title_label)
        layout.addWidget(self.score_label)
        layout.addWidget(self.status_label)
