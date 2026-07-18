"""Aggregate owner for the canonical editable workspace state."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from workspace_core.planner_bridge import WorkspacePlannerBridge
from .actions import ActionQueue
from .copybuffer import CopyBuffer
from .brush_commands import WorkspaceBrushCommands
from .model import EditableMap
from .selection import RMESelectionManager


@dataclass
class EditorWorkspaceCore:
    """Single ownership root comparable to RME's Editor boundary."""

    editable_map: EditableMap = field(default_factory=EditableMap)
    action_memory_limit: int = 64 * 1024 * 1024
    copybuffer_history_limit: int = 32
    root: str | Path = "."

    def __post_init__(self) -> None:
        self.actions = ActionQueue(
            self.editable_map,
            memory_limit=self.action_memory_limit,
        )
        self.selection = RMESelectionManager(self.actions)
        self.copybuffer = CopyBuffer(self.copybuffer_history_limit)
        self.brush_commands = WorkspaceBrushCommands(self, self.root)
        self.planner = WorkspacePlannerBridge(self.root)

    def audit(self) -> dict[str, object]:
        return {
            "workspace_core_ready": True,
            "single_owner": True,
            "editable_map": self.editable_map.audit(),
            "actions": self.actions.audit(),
            "selection": self.selection.audit(),
            "copybuffer": self.copybuffer.audit(),
            "brush_commands": self.brush_commands.audit(),
            "planner": self.planner.audit(),
        }


__all__ = ["EditorWorkspaceCore"]
