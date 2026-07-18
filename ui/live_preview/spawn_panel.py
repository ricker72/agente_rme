"""
Spawn panel.
"""

from .base_panel import TablePanel


class SpawnPanel(TablePanel):
    def __init__(self) -> None:
        super().__init__("Spawns", ["monster", "coordinates", "radius", "floor"])
