"""
Quest panel.
"""

from .base_panel import TablePanel


class QuestPanel(TablePanel):
    def __init__(self) -> None:
        super().__init__("Quests", ["quest_name", "stages", "storage_range", "coordinates", "reachability"])
