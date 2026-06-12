"""
Tests for ui.page_registry.PageRegistry.
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QApplication, QWidget

from ui.page_registry import PageRegistry


@pytest.fixture(scope="session", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class _StubPage(QWidget):
    """Lightweight stub page for testing."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("stub")


class TestPageRegistry:
    """Unit tests for the PageRegistry."""

    def test_register_and_get(self):
        registry = PageRegistry()
        registry.register_page("test", _StubPage)
        page = registry.get_page("test")
        assert page is not None
        assert page.objectName() == "stub"

    def test_get_unknown_returns_none(self):
        registry = PageRegistry()
        assert registry.get_page("nonexistent") is None

    def test_lazy_creation(self):
        registry = PageRegistry()
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return _StubPage()

        registry.register_page("lazy", factory)
        assert call_count == 0
        registry.get_page("lazy")
        assert call_count == 1
        registry.get_page("lazy")
        assert call_count == 1  # not called again

    def test_duplicate_raises(self):
        registry = PageRegistry()
        registry.register_page("dup", _StubPage)
        with pytest.raises(ValueError):
            registry.register_page("dup", _StubPage)

    def test_is_registered(self):
        registry = PageRegistry()
        assert not registry.is_registered("a")
        registry.register_page("a", _StubPage)
        assert registry.is_registered("a")

    def test_is_loaded(self):
        registry = PageRegistry()
        registry.register_page("b", _StubPage)
        assert not registry.is_loaded("b")
        registry.get_page("b")
        assert registry.is_loaded("b")

    def test_registered_ids(self):
        registry = PageRegistry()
        registry.register_page("c", _StubPage)
        registry.register_page("a", _StubPage)
        assert registry.registered_ids() == ["a", "c"]

    def test_loaded_ids(self):
        registry = PageRegistry()
        registry.register_page("x", _StubPage)
        registry.register_page("y", _StubPage)
        registry.get_page("x")
        assert registry.loaded_ids() == ["x"]

    def test_unregister(self):
        registry = PageRegistry()
        registry.register_page("rem", _StubPage)
        assert registry.is_registered("rem")
        registry.unregister_page("rem")
        assert not registry.is_registered("rem")

    def test_clear(self):
        registry = PageRegistry()
        registry.register_page("d", _StubPage)
        registry.get_page("d")
        registry.clear()
        assert registry.registered_ids() == []
        assert registry.loaded_ids() == []

    def test_get_unregistered_idempotent(self):
        registry = PageRegistry()
        # Multiple calls for unknown id return None each time
        assert registry.get_page("nope") is None
        assert registry.get_page("nope") is None
