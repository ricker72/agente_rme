"""
RULE-39 visual validation authority panel.
"""

from __future__ import annotations

from typing import Any, Dict

from .base_panel import TablePanel


class VisualValidationPanel(TablePanel):
    """Displays reported-vs-rendered visual truth counts."""

    def __init__(self) -> None:
        super().__init__(
            "Visual Validation",
            [
                "metric",
                "reported",
                "rendered_symbolic",
                "rendered_appearance_backed",
                "sprite_rendered_tiles",
                "fallback_rendered",
                "missing_appearance",
                "missing_sprites",
                "status",
            ],
        )

    def set_validation(self, report: Dict[str, Any]) -> None:
        rows = []
        for metric in ["houses", "shops", "roads", "npcs", "spawns"]:
            rows.append(
                {
                    "metric": metric,
                    "reported": report.get(f"reported_{metric}", 0),
                    "rendered_symbolic": report.get("rendered_symbolic", 0),
                    "rendered_appearance_backed": report.get(
                        "rendered_appearance_backed",
                        report.get(
                            "appearance_backed_tiles",
                            report.get(f"rendered_{metric}", 0),
                        ),
                    ),
                    "sprite_rendered_tiles": report.get("sprite_rendered_tiles", 0),
                    "fallback_rendered": report.get("fallback_rendered", 0),
                    "missing_appearance": report.get("missing_appearance", 0),
                    "missing_sprites": report.get("missing_sprites", 0),
                    "status": report.get("certification_status", "PASS"),
                }
            )
        self.set_rows(rows)
