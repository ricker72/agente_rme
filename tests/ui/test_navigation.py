"""
Tests for ui.navigation.NavigationController — targeting ≥ 80% coverage.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget

from ui.event_bus import EventBus, PageChangedEvent
from ui.navigation import NavigationController
from ui.page_registry import PageRegistry


# Ensure a QApplication exists with org/app names for QSettings
@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    app.setOrganizationName("TestOrg")
    app.setApplicationName("TestApp")
    return app


@pytest.fixture(autouse=True)
def _clean_settings():
    """Clear QSettings before and after each test."""
    settings = QSettings()
    settings.remove(NavigationController.SETTINGS_KEY)
    yield
    settings.remove(NavigationController.SETTINGS_KEY)


class _StubPage(QWidget):
    """Minimal stub page for tests."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("stub-page")


class _AnotherPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("another-page")


class TestNavigationController:
    """Comprehensive tests for NavigationController."""

    def _make(self, event_bus=None):
        ws = QStackedWidget()
        return NavigationController(workspace=ws, event_bus=event_bus)

    # ── basic navigation ────────────────────────────────────────────────

    def test_register_and_navigate(self):
        nav = self._make()
        nav.register_page("p1", _StubPage)
        nav.navigate_to("p1")
        assert nav.current_page_id == "stub-page"

    def test_navigate_unknown_is_noop(self):
        nav = self._make()
        nav.navigate_to("nonexistent")
        assert nav.current_page_id is None

    def test_navigate_switches_page(self):
        nav = self._make()
        nav.register_page("a", _StubPage)
        nav.register_page("b", _AnotherPage)
        nav.navigate_to("a")
        assert nav.current_page_id == "stub-page"
        nav.navigate_to("b")
        assert nav.current_page_id == "another-page"

    # ── lazy loading ────────────────────────────────────────────────────

    def test_lazy_load(self):
        nav = self._make()
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return _StubPage()

        nav.register_page("lazy", factory)
        assert call_count == 0
        nav.navigate_to("lazy")
        assert call_count == 1
        # Re-navigate should not re-instantiate
        nav.navigate_to("lazy")
        assert call_count == 1

    # ── event bus ───────────────────────────────────────────────────────

    def test_emits_page_changed(self):
        bus = EventBus()
        received = []
        bus.register(PageChangedEvent, lambda e: received.append(e))
        nav = self._make(event_bus=bus)
        nav.register_page("p", _StubPage)
        nav.navigate_to("p")
        assert len(received) == 1
        # current_page in event is the page_id string, not objectName
        assert received[0].current_page == "p"
        assert received[0].previous_page == ""

    def test_emits_previous_page(self):
        bus = EventBus()
        received = []
        bus.register(PageChangedEvent, lambda e: received.append(e))
        nav = self._make(event_bus=bus)
        nav.register_page("a", _StubPage)
        nav.register_page("b", _AnotherPage)
        nav.navigate_to("a")
        nav.navigate_to("b")
        assert len(received) == 2
        # previous_page is objectName of the previous widget
        assert received[1].previous_page == "stub-page"
        assert received[1].current_page == "b"

    def test_no_event_bus(self):
        nav = self._make(event_bus=None)
        nav.register_page("x", _StubPage)
        nav.navigate_to("x")  # should not raise
        assert nav.current_page_id == "stub-page"

    # ── session persistence ─────────────────────────────────────────────

    def test_save_and_restore_last_page(self):
        nav = self._make()
        nav.register_page("dash", _StubPage)
        nav.navigate_to("dash")
        nav.save_last_page()
        restored = nav.restore_last_page()
        # save_last_page uses current_page_id (objectName)
        assert restored == "stub-page"

    def test_restore_default(self):
        nav = self._make()
        # No saved value — should return default
        result = nav.restore_last_page(default="fallback")
        assert result == "fallback"

    # ── registry delegation ─────────────────────────────────────────────

    def test_registry_property(self):
        nav = self._make()
        assert isinstance(nav.registry, PageRegistry)

    def test_registered_ids(self):
        nav = self._make()
        nav.register_page("a", _StubPage)
        nav.register_page("b", _AnotherPage)
        assert nav.registered_ids() == ["a", "b"]

    # ── edge cases ──────────────────────────────────────────────────────

    def test_navigate_same_page_twice(self):
        nav = self._make()
        nav.register_page("s", _StubPage)
        nav.navigate_to("s")
        nav.navigate_to("s")
        assert nav.current_page_id == "stub-page"

    def test_no_page_selected(self):
        nav = self._make()
        assert nav.current_page_id is None

    def test_navigate_persists_to_settings(self):
        """navigate_to should auto-save the page_id to QSettings."""
        nav = self._make()
        nav.register_page("x", _StubPage)
        nav.navigate_to("x")
        settings = QSettings()
        stored = settings.value(NavigationController.SETTINGS_KEY, type=str)
        assert stored == "x"
