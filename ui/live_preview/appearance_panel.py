"""
Appearance inspection panel.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .base_panel import TablePanel


class AppearancePanel(TablePanel):
    """Consumes appearance catalogs."""

    def __init__(self) -> None:
        super().__init__("Appearances", ["id", "name", "category", "flags", "animation", "semantic_role"])

    def set_appearances(self, appearances: List[Dict[str, Any]]) -> None:
        self.set_rows(appearances)
