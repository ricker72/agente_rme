"""
MAP-01C: NECRO Tile Selection
Tile selection functionality for OpenTibia mapping
"""

from typing import Tuple, List, Optional
from dataclasses import dataclass

from workspace_core.editor.selection import (
    RMESelectionManager as RMESelectionManager,
    SelectionSessionMode as SelectionSessionMode,
)

__all__ = [
    "RMESelectionManager",
    "Selection",
    "SelectionSessionMode",
    "TileSelector",
]


@dataclass
class Selection:
    """Represents a tile selection"""
    min_x: int
    min_y: int
    max_x: int
    max_y: int
    z: int = 7  # Default OpenTibia ground level

    @property
    def width(self) -> int:
        return self.max_x - self.min_x + 1

    @property
    def height(self) -> int:
        return self.max_y - self.min_y + 1

    @property
    def area(self) -> int:
        return self.width * self.height

    def contains(self, x: int, y: int, z: int = 7) -> bool:
        """Check if coordinate is within selection"""
        return (self.min_x <= x <= self.max_x and
                self.min_y <= y <= self.max_y and
                z == self.z)

    def get_coordinates(self) -> List[Tuple[int, int, int]]:
        """Get all coordinates in selection"""
        coords = []
        for x in range(self.min_x, self.max_x + 1):
            for y in range(self.min_y, self.max_y + 1):
                coords.append((x, y, self.z))
        return coords

class TileSelector:
    """Tile selection manager for NECRO project"""

    def __init__(self):
        self.selection: Optional[Selection] = None
        self.selecting = False
        self.selection_start_x = 0
        self.selection_start_y = 0
        self.current_z = 7

    def start_selection(self, x: int, y: int, z: int = 7):
        """Start new selection at coordinate"""
        self.selecting = True
        self.selection_start_x = x
        self.selection_start_y = y
        self.current_z = z
        self.selection = None

    def update_selection(self, x: int, y: int):
        """Update selection end point"""
        if not self.selecting:
            return

        # Determine selection bounds
        min_x = min(self.selection_start_x, x)
        max_x = max(self.selection_start_x, x)
        min_y = min(self.selection_start_y, y)
        max_y = max(self.selection_start_y, y)

        self.selection = Selection(min_x, min_y, max_x, max_y, self.current_z)

    def end_selection(self):
        """Finalize current selection"""
        self.selecting = False

    def clear_selection(self):
        """Clear current selection"""
        self.selection = None
        self.selecting = False

    def select_single_tile(self, x: int, y: int, z: int = 7):
        """Select single tile"""
        self.selection = Selection(x, y, x, y, z)
        self.selecting = False

    def get_selection_stats(self) -> dict:
        """Get statistics about current selection"""
        if not self.selection:
            return {
                'has_selection': False,
                'tile_count': 0,
                'coordinates': []
            }

        return {
            'has_selection': True,
            'tile_count': self.selection.area,
            'coordinates': self.selection.get_coordinates(),
            'bounds': {
                'min': (self.selection.min_x, self.selection.min_y, self.selection.z),
                'max': (self.selection.max_x, self.selection.max_y, self.selection.z),
                'width': self.selection.width,
                'height': self.selection.height
            }
        }

    def handle_mouse_event(self, event_type: str, x: int, y: int, z: int = 7) -> bool:
        """
        Handle mouse events for selection
        Returns True if event was handled by selection system
        """
        handled = False

        if event_type == 'MOUSEBUTTONDOWN' and not self.selecting:
            # Start new selection
            self.start_selection(x, y, z)
            handled = True

        elif event_type == 'MOUSEBUTTONUP' and self.selecting:
            # End selection
            self.update_selection(x, y)
            self.end_selection()
            handled = True

        elif event_type == 'MOUSEMOTION' and self.selecting:
            # Update selection
            self.update_selection(x, y)
            handled = True

        elif event_type == 'MOUSEBUTTONDOWN' and not self.selecting:
            # Single tile selection
            self.select_single_tile(x, y, z)
            handled = True

        return handled
