"""Canonical editor behavior API for UI, AI and export consumers."""

from .actions import ActionIdentifier, ActionQueue, BatchAction, TileChange
from .copybuffer import CopyBuffer
from .brush_commands import BrushCommandResult, WorkspaceBrushCommands
from .model import EditableMap, EditableTile, TileCoord, TileKey, WorkspaceTile
from .mapping_engine import WorkspaceMappingEngine, WorkspaceMappingTransaction
from .selection import RMESelectionManager, SelectionSessionMode
from .workspace import EditorWorkspaceCore

__all__ = [
    "ActionIdentifier",
    "ActionQueue",
    "BatchAction",
    "BrushCommandResult",
    "CopyBuffer",
    "EditableMap",
    "EditableTile",
    "EditorWorkspaceCore",
    "RMESelectionManager",
    "SelectionSessionMode",
    "TileChange",
    "TileCoord",
    "TileKey",
    "WorkspaceTile",
    "WorkspaceBrushCommands",
    "WorkspaceMappingEngine",
    "WorkspaceMappingTransaction",
]
