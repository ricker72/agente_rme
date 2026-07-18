"""RME-style transactional selection owned by Workspace Core."""

from __future__ import annotations

from enum import IntFlag
from typing import Iterable

from .actions import ActionIdentifier, ActionQueue, BatchAction
from .model import TileKey


class SelectionSessionMode(IntFlag):
    EXTERNAL = 0
    INTERNAL = 1
    SUBTHREAD = 2


class RMESelectionManager:
    selection_safe_action = True
    external_selection_mode = "BatchAction"

    def __init__(self, actions: ActionQueue) -> None:
        self.actions = actions
        self._positions: set[TileKey] = set()
        self._session_before: set[TileKey] | None = None
        self._session_working: set[TileKey] | None = None
        self._session_mode = SelectionSessionMode.EXTERNAL
        self.busy = False
        self.history: list[set[TileKey]] = []

    @property
    def positions(self) -> set[TileKey]:
        return self._positions

    def set_positions(
        self,
        positions: Iterable[TileKey],
        *,
        mode: SelectionSessionMode = SelectionSessionMode.EXTERNAL,
        label: str = "Select tiles",
    ) -> BatchAction | None:
        target = {tuple(int(value) for value in position) for position in positions}
        if target == self._positions:
            return None
        if mode & SelectionSessionMode.INTERNAL:
            self._replace_internal(target)
            return None
        action = self._selection_action(set(self._positions), target, label)
        self.actions.commit(action)
        return action

    def start(self, mode: SelectionSessionMode = SelectionSessionMode.EXTERNAL) -> None:
        if self.busy:
            raise RuntimeError("selection session already active")
        self.busy = True
        self._session_mode = mode
        self._session_before = set(self._positions)
        self._session_working = set(self._positions)

    def add(self, positions: Iterable[TileKey]) -> None:
        self._require_session()
        assert self._session_working is not None
        self._session_working.update(
            tuple(int(value) for value in position) for position in positions
        )

    def remove(self, positions: Iterable[TileKey]) -> None:
        self._require_session()
        assert self._session_working is not None
        self._session_working.difference_update(
            tuple(int(value) for value in position) for position in positions
        )

    def clear(self) -> None:
        if self.busy:
            assert self._session_working is not None
            self._session_working.clear()
        else:
            self.set_positions(set(), label="Unselect tiles")

    def commit(self, label: str = "Select tiles") -> BatchAction | None:
        self._require_session()
        assert self._session_before is not None and self._session_working is not None
        before = set(self._session_before)
        after = set(self._session_working)
        if before == after:
            self._session_before = set(after)
            return None
        if self._session_mode & SelectionSessionMode.INTERNAL:
            self._replace_internal(after)
            action = None
        elif self._session_mode & SelectionSessionMode.SUBTHREAD:
            action = self._selection_action(before, after, label)
        else:
            action = self._selection_action(before, after, label)
            self.actions.commit(action)
        self._session_before = set(after)
        return action

    def finish(self, label: str = "Select tiles") -> BatchAction | None:
        action = self.commit(label)
        self.busy = False
        self._session_before = None
        self._session_working = None
        self._session_mode = SelectionSessionMode.EXTERNAL
        return action

    def retain_existing(self, positions: Iterable[TileKey]) -> None:
        self.set_positions(
            self._positions & {tuple(position) for position in positions},
            mode=SelectionSessionMode.INTERNAL,
            label="Internal selection sync",
        )

    def audit(self) -> dict[str, object]:
        return {
            "rme_selection_ready": True,
            "selection_safe_action": True,
            "external_selection_mode": self.external_selection_mode,
            "internal_selection_mode": "no history",
            "subthread_selection_mode": "detached BatchAction",
            "selected_tile_count": len(self._positions),
            "busy": self.busy,
            "owner": "workspace_core",
        }

    def _selection_action(
        self, before: set[TileKey], after: set[TileKey], label: str
    ) -> BatchAction:
        before_snapshot = frozenset(before)
        after_snapshot = frozenset(after)
        identifier = (
            ActionIdentifier.SELECT
            if len(after_snapshot) >= len(before_snapshot)
            else ActionIdentifier.UNSELECT
        )
        return BatchAction(
            label=label,
            identifier=identifier,
            metadata={
                "selection_before": sorted(before_snapshot),
                "selection_after": sorted(after_snapshot),
                "selection_external": True,
            },
            redo_callback=lambda: self._replace_internal(set(after_snapshot)),
            undo_callback=lambda: self._replace_internal(set(before_snapshot)),
        )

    def _replace_internal(self, positions: set[TileKey]) -> None:
        self.history.append(set(self._positions))
        self._positions.clear()
        self._positions.update(positions)

    def _require_session(self) -> None:
        if not self.busy:
            raise RuntimeError("selection operation requires an active session")


__all__ = ["RMESelectionManager", "SelectionSessionMode"]
