"""
Quick Action Card Widget for Agente RME Studio Dashboard.

Provides navigation buttons for common actions without executing core logic.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QVBoxLayout


class QuickActionCard(QFrame):
    """A card widget containing quick‑action buttons."""

    STYLESHEET = """
        QuickActionCard {
            background-color: #1e1e2e;
            border-radius: 8px;
            border: 1px solid #313244;
            padding: 16px;
        }
    """

    BUTTON_STYLESHEET = """
        QPushButton {
            background-color: #0e639c;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 500;
            min-width: 120px;
        }
        QPushButton:hover {
            background-color: #1177bb;
        }
    """

    # Signal emitted when a button is pressed; payload is the action identifier
    action_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("quick_action_card")
        self.setStyleSheet(self.STYLESHEET)
        self._build_ui()

    def _build_ui(self) -> None:
        """Construct the UI layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Title (non‑interactive label)
        title = QPushButton("Quick Actions", self)
        title.setEnabled(False)
        title.setStyleSheet(
            "background: none; border: none; color: #a6adc8; font-size: 14px; font-weight: 600;"
        )
        layout.addWidget(title)

        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self._generate_world_btn = QPushButton("Generate World", self)
        self._generate_world_btn.setStyleSheet(self.BUTTON_STYLESHEET)
        self._generate_world_btn.clicked.connect(
            lambda: self.action_requested.emit("generate_world")
        )
        btn_layout.addWidget(self._generate_world_btn)

        self._run_critic_btn = QPushButton("Run Critic", self)
        self._run_critic_btn.setStyleSheet(self.BUTTON_STYLESHEET)
        self._run_critic_btn.clicked.connect(
            lambda: self.action_requested.emit("run_critic")
        )
        btn_layout.addWidget(self._run_critic_btn)

        self._knowledge_explorer_btn = QPushButton("Knowledge Explorer", self)
        self._knowledge_explorer_btn.setStyleSheet(self.BUTTON_STYLESHEET)
        self._knowledge_explorer_btn.clicked.connect(
            lambda: self.action_requested.emit("knowledge_explorer")
        )
        btn_layout.addWidget(self._knowledge_explorer_btn)

        self._otbm_studio_btn = QPushButton("OTBM Studio", self)
        self._otbm_studio_btn.setStyleSheet(self.BUTTON_STYLESHEET)
        self._otbm_studio_btn.clicked.connect(
            lambda: self.action_requested.emit("otbm_studio")
        )
        btn_layout.addWidget(self._otbm_studio_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)
