from __future__ import annotations

import time
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable

from core.editor.editable_map import EditableMap, EditableTile, Position


class ActionIdentifier(str, Enum):
    MOVE = "move"
    SELECT = "select"
    UNSELECT = "unselect"
    DELETE_TILES = "delete_tiles"
    CUT_TILES = "cut_tiles"
    DRAW = "draw"
    ERASE = "erase"
    BORDERIZE = "borderize"
    RANDOMIZE = "randomize"
    PASTE_TILES = "paste_tiles"
    REPLACE_ITEMS = "replace_items"
    CHANGE_PROPERTIES = "change_properties"
    LUA_SCRIPT = "lua_script"
    AI_REPAIR = "ai_repair"


@dataclass(frozen=True)
class TileChange:
    position: Position
    before: EditableTile | None
    after: EditableTile | None


@dataclass
class EditorAction:
    label: str
    changes: list[TileChange] = field(default_factory=list)
    identifier: ActionIdentifier = ActionIdentifier.DRAW
    timestamp_ms: int = field(default_factory=lambda: int(time.monotonic() * 1000))
    metadata: dict[str, object] = field(default_factory=dict)
    redo_callback: Callable[[], None] | None = field(default=None, repr=False)
    undo_callback: Callable[[], None] | None = field(default=None, repr=False)

    def redo(self, editable_map: EditableMap) -> None:
        for change in self.changes:
            editable_map.set_tile(change.after, change.position)
        if self.redo_callback is not None:
            self.redo_callback()

    def undo(self, editable_map: EditableMap) -> None:
        for change in reversed(self.changes):
            editable_map.set_tile(change.before, change.position)
        if self.undo_callback is not None:
            self.undo_callback()

    @property
    def positions(self) -> tuple[Position, ...]:
        return tuple(change.position for change in self.changes)

    def memory_size(self) -> int:
        return sum(
            32
            + 8 * len(change.before.stack_ids() if change.before else [])
            + 8 * len(change.after.stack_ids() if change.after else [])
            for change in self.changes
        )

    def empty(self) -> bool:
        return not self.changes and self.redo_callback is None and self.undo_callback is None


@dataclass
class BatchAction(EditorAction):
    child_labels: tuple[str, ...] = ()


class EditTransaction(AbstractContextManager["EditTransaction"]):
    def __init__(
        self,
        queue: "ActionQueue",
        label: str,
        identifier: ActionIdentifier,
    ) -> None:
        self.queue = queue
        self.label = label
        self.identifier = identifier
        self.actions: list[EditorAction] = []
        self.committed = False

    def add(self, action: EditorAction) -> EditorAction:
        if self.committed:
            raise RuntimeError("transaction already committed")
        self.actions.append(action)
        return action

    def set_stack(self, position: Position, item_ids: Iterable[int]) -> EditorAction:
        return self.add(self.queue.make_stack_action(self.label, position, item_ids))

    def commit(self) -> BatchAction:
        if self.committed:
            raise RuntimeError("transaction already committed")
        batch = self.queue.make_batch(self.label, self.identifier, self.actions)
        self.queue.commit(batch)
        self.committed = True
        return batch

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        if exc_type is None and not self.committed:
            self.commit()
        return False


class ActionQueue:
    def __init__(self, editable_map: EditableMap, memory_limit: int = 64 * 1024 * 1024) -> None:
        self.editable_map = editable_map
        self.undo_stack: list[EditorAction] = []
        self.redo_stack: list[EditorAction] = []
        self.memory_limit = max(1024, int(memory_limit))
        self.memory_size = 0

    def commit(self, action: EditorAction) -> None:
        if action.empty():
            return
        applied: list[TileChange] = []
        try:
            for change in action.changes:
                self.editable_map.set_tile(change.after, change.position)
                applied.append(change)
            if action.redo_callback is not None:
                action.redo_callback()
        except Exception:
            if action.undo_callback is not None:
                action.undo_callback()
            for change in reversed(applied):
                self.editable_map.set_tile(change.before, change.position)
            raise
        self.undo_stack.append(action)
        self.memory_size = max(
            0,
            self.memory_size - sum(item.memory_size() for item in self.redo_stack),
        )
        self.redo_stack.clear()
        self.memory_size += action.memory_size()
        self._trim_to_memory_limit()

    def undo(self) -> bool:
        return self.undo_action() is not None

    def undo_action(self) -> EditorAction | None:
        if not self.undo_stack:
            return None
        action = self.undo_stack.pop()
        action.undo(self.editable_map)
        self.redo_stack.append(action)
        return action

    def redo(self) -> bool:
        return self.redo_action() is not None

    def redo_action(self) -> EditorAction | None:
        if not self.redo_stack:
            return None
        action = self.redo_stack.pop()
        action.redo(self.editable_map)
        self.undo_stack.append(action)
        return action

    def make_stack_action(self, label: str, position: Position, item_ids: Iterable[int]) -> EditorAction:
        before = self.editable_map.snapshot_tile(position)
        temp = EditableMap(self.editable_map.item_catalog)
        if before:
            temp.set_tile(before)
        temp.set_stack(position, item_ids)
        after = temp.snapshot_tile(position)
        return EditorAction(label=label, changes=[TileChange(position=position, before=before, after=after)])

    def transaction(
        self,
        label: str,
        identifier: ActionIdentifier = ActionIdentifier.DRAW,
    ) -> EditTransaction:
        return EditTransaction(self, label, identifier)

    def make_batch(
        self,
        label: str,
        identifier: ActionIdentifier,
        actions: Iterable[EditorAction],
    ) -> BatchAction:
        action_list = list(actions)
        first_before: dict[Position, EditableTile | None] = {}
        last_after: dict[Position, EditableTile | None] = {}
        order: list[Position] = []
        for action in action_list:
            for change in action.changes:
                if change.position not in first_before:
                    first_before[change.position] = change.before.copy() if change.before else None
                    order.append(change.position)
                last_after[change.position] = change.after.copy() if change.after else None
        changes = [
            TileChange(position, first_before[position], last_after[position])
            for position in order
        ]
        redo_callbacks = [action.redo_callback for action in action_list if action.redo_callback]
        undo_callbacks = [action.undo_callback for action in action_list if action.undo_callback]

        def redo_callbacks_in_order() -> None:
            for callback in redo_callbacks:
                callback()

        def undo_callbacks_in_reverse() -> None:
            for callback in reversed(undo_callbacks):
                callback()

        return BatchAction(
            label=label,
            changes=changes,
            identifier=identifier,
            child_labels=tuple(action.label for action in action_list),
            metadata={"child_action_count": len(action_list)},
            redo_callback=redo_callbacks_in_order if redo_callbacks else None,
            undo_callback=undo_callbacks_in_reverse if undo_callbacks else None,
        )

    def clear(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.memory_size = 0

    def _trim_to_memory_limit(self) -> None:
        while len(self.undo_stack) > 1 and self.memory_size > self.memory_limit:
            removed = self.undo_stack.pop(0)
            self.memory_size = max(0, self.memory_size - removed.memory_size())

    def audit(self) -> dict[str, object]:
        return {
            "action_queue_ready": True,
            "undo_depth": len(self.undo_stack),
            "redo_depth": len(self.redo_stack),
            "dirty_tile_count": len(self.editable_map.modified),
            "batch_actions_ready": True,
            "atomic_commit_ready": True,
            "transaction_context_ready": True,
            "memory_size": self.memory_size,
            "memory_limit": self.memory_limit,
            "action_identifiers": [identifier.value for identifier in ActionIdentifier],
        }
