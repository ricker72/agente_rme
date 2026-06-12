"""
Tests for session restore via QSettings in the NavigationController.

Verifies that the last-visited page is persisted and restored correctly
across NavigationController instances.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QStackedWidget, QWidget

from ui.navigation import NavigationController


@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    app.setOrganizationName("TestOrg")
    app.setApplicationName("TestApp")
    return app


@pytest.fixture(autouse=True)
def clean_settings():
    """Clear relevant QSettings keys before and after each test."""
    settings = QSettings()
    settings.remove(NavigationController.SETTINGS_KEY)
    yield
    settings.remove(NavigationController.SETTINGS_KEY)


class _PageA(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page-a")


class _PageB(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page-b")


class TestSessionRestore:
    """Tests for workspace session persistence."""

    def _make_nav(self):
        ws = QStackedWidget()
        nav = NavigationController(workspace=ws)
        nav.register_page("a", _PageA)
        nav.register_page("b", _PageB)
        return nav

    def test_save_last_page(self):
        nav = self._make_nav()
        nav.navigate_to("a")
        nav.save_last_page()
        settings = QSettings()
        stored = settings.value(NavigationController.SETTINGS_KEY, type=str)
        assert stored == "page-a"

    def test_restore_last_page(self):
        nav = self._make_nav()
        nav.navigate_to("b")
        nav.save_last_page()

        nav2 = self._make_nav()
        restored = nav2.restore_last_page()
        assert restored == "page-b"

    def test_restore_default_when_empty(self):
        nav = self._make_nav()
        result = nav.restore_last_page(default="fallback")
        assert result == "fallback"

    def test_restore_default_when_corrupt(self):
        settings = QSettings()
        settings.setValue(NavigationController.SETTINGS_KEY, "corrupt_id")
        nav = self._make_nav()
        restored = nav.restore_last_page(default="a")
        # Corrupt value is returned as-is since it is a non-empty string
        assert restored == "corrupt_id"

    def test_auto_persist_on_navigate(self):
        """navigate_to should auto-persist the page_id to QSettings."""
        nav = self._make_nav()
        nav.navigate_to("a")
        settings = QSettings()
        stored = settings.value(NavigationController.SETTINGS_KEY, type=str)
        assert stored == "a"

    def test_navigate_switches_persisted_value(self):
        nav = self._make_nav()
        nav.navigate_to("a")
        nav.navigate_to("b")
        settings = QSettings()
        stored = settings.value(NavigationController.SETTINGS_KEY, type=str)
        assert stored == "b"
