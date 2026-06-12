"""
Page Registry for Agente RME Studio.

Allows registering pages by ID and retrieving them.
Supports lazy loading: pages are created only when first accessed.
"""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import QWidget


PageFactory = Callable[[], QWidget]


class PageRegistry:
    """Registry for workspace pages with lazy-loading support.

    Pages are registered with a unique string ID and a factory callable.
    The factory is invoked only when the page is first requested via
    ``get_page()``, enabling deferred construction.
    """

    def __init__(self) -> None:
        self._factories: dict[str, PageFactory] = {}
        self._instances: dict[str, QWidget] = {}

    # ── registration ─────────────────────────────────────────────────────

    def register_page(self, page_id: str, factory: PageFactory) -> None:
        """Register a page under *page_id*.

        Args:
            page_id: Unique identifier for the page (e.g. ``"dashboard"``).
            factory: Zero-argument callable that returns a ``QWidget``.

        Raises:
            ValueError: If *page_id* is already registered.
        """
        if page_id in self._factories:
            raise ValueError(f"A page with id '{page_id}' is already registered.")
        self._factories[page_id] = factory

    # ── retrieval ────────────────────────────────────────────────────────

    def get_page(self, page_id: str) -> QWidget | None:
        """Return the page instance for *page_id*, creating it if necessary.

        Returns ``None`` if *page_id* has not been registered.
        """
        if page_id not in self._factories:
            return None

        if page_id not in self._instances:
            self._instances[page_id] = self._factories[page_id]()

        return self._instances[page_id]

    # ── inspection ───────────────────────────────────────────────────────

    def is_registered(self, page_id: str) -> bool:
        """Return ``True`` if *page_id* has been registered."""
        return page_id in self._factories

    def is_loaded(self, page_id: str) -> bool:
        """Return ``True`` if the page for *page_id* has been instantiated."""
        return page_id in self._instances

    def registered_ids(self) -> list[str]:
        """Return a sorted list of all registered page IDs."""
        return sorted(self._factories.keys())

    def loaded_ids(self) -> list[str]:
        """Return a sorted list of IDs whose pages have been instantiated."""
        return sorted(self._instances.keys())

    # ── lifecycle ────────────────────────────────────────────────────────

    def unregister_page(self, page_id: str) -> None:
        """Remove a page registration and discard its instance if loaded."""
        self._factories.pop(page_id, None)
        self._instances.pop(page_id, None)

    def clear(self) -> None:
        """Remove all registrations and instances."""
        self._factories.clear()
        self._instances.clear()
