"""
Navigation Controller for Agente RME Studio.

Orchestrates page switching, emits ``PageChangedEvent`` on the event bus,
and persists the last-visited page via ``QSettings``.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QObject, QSettings
from PySide6.QtWidgets import QStackedWidget

from .event_bus import EventBus, PageChangedEvent
from .page_registry import PageRegistry


class NavigationController(QObject):
    """Central controller for workspace page navigation.

    Responsibilities:

    *   Register pages with the internal :class:`PageRegistry`.
    *   Switch the active page in a :class:`QStackedWidget`.
    *   Emit :class:`PageChangedEvent` on every navigation.
    *   Persist & restore the last page via ``QSettings``.
    """

    SETTINGS_KEY = "workspace/last_page"

    def __init__(
        self,
        workspace: QStackedWidget,
        event_bus: EventBus | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._workspace = workspace
        self._event_bus = event_bus
        self._registry = PageRegistry()
        self._page_to_index: dict[str, int] = {}

    # ── properties ───────────────────────────────────────────────────────

    @property
    def registry(self) -> PageRegistry:
        """Access the underlying page registry."""
        return self._registry

    @property
    def current_page_id(self) -> str | None:
        """Return the ID of the currently visible page, or ``None``."""
        widget = self._workspace.currentWidget()
        if widget is None:
            return None
        return widget.objectName() or None

    # ── page management ──────────────────────────────────────────────────

    def register_page(self, page_id: str, factory: Any) -> None:
        """Register a page and prepare its slot in the stack.

        The factory is **not** called here — lazy creation happens on
        first ``navigate_to()``.
        """
        self._registry.register_page(page_id, factory)

    def navigate_to(self, page_id: str) -> None:
        """Switch to the page identified by *page_id*.

        If the page has not been instantiated yet, it is created now
        (lazy load) and inserted into the ``QStackedWidget``.
        """
        page = self._registry.get_page(page_id)
        if page is None:
            return  # not registered — silently ignore

        # Capture previous page BEFORE modifying the stack
        previous = self.current_page_id or ""

        # Insert into the stack if this is the first navigation
        if page_id not in self._page_to_index:
            index = self._workspace.addWidget(page)
            self._page_to_index[page_id] = index
        else:
            index = self._page_to_index[page_id]
        self._workspace.setCurrentIndex(index)

        # Emit event
        if self._event_bus is not None:
            self._event_bus.emit(
                PageChangedEvent(previous_page=previous, current_page=page_id)
            )

        # Persist
        self._save_last_page(page_id)

    # ── session persistence ──────────────────────────────────────────────

    def save_last_page(self) -> None:
        """Persist the current page ID to ``QSettings``."""
        current = self.current_page_id
        if current:
            self._save_last_page(current)

    def restore_last_page(self, default: str = "dashboard") -> str:
        """Return the last-visited page ID from ``QSettings``.

        Falls back to *default* if no saved value exists.
        """
        settings = QSettings()
        result: str | None = settings.value(self.SETTINGS_KEY, default, type=str)  # type: ignore[assignment]
        return result or default

    def _save_last_page(self, page_id: str) -> None:
        settings = QSettings()
        settings.setValue(self.SETTINGS_KEY, page_id)

    # ── convenience ──────────────────────────────────────────────────────

    def registered_ids(self) -> list[str]:
        """Return all registered page IDs."""
        return self._registry.registered_ids()
