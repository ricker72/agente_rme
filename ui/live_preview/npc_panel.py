"""
NPC panel.
"""

from .base_panel import TablePanel


class NpcPanel(TablePanel):
    def __init__(self) -> None:
        super().__init__("NPCs", ["name", "role", "coordinates", "floor", "accessibility"])
