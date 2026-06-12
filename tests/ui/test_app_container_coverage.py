from __future__ import annotations

from typing import Any, cast

from ui import app as app_module
from ui.app import RMEStudioApp
from ui.event_bus import EventBus
from ui.main_window import MainWindow
from ui.theme import ThemeManager


class FakeQApplication:
    def __init__(self, argv: list[str]) -> None:
        self.argv = argv
        self.stylesheet = ""
        self.exec_called = False
        self.name = ""
        self.org = ""
        self.version = ""

    def setApplicationName(self, value: str) -> None:
        self.name = value

    def setOrganizationName(self, value: str) -> None:
        self.org = value

    def setApplicationVersion(self, value: str) -> None:
        self.version = value

    def setStyleSheet(self, value: str) -> None:
        self.stylesheet = value

    def exec(self) -> int:
        self.exec_called = True
        return 7


class FakeMainWindow:
    def __init__(self, theme: ThemeManager, event_bus: EventBus) -> None:
        self.theme = theme
        self.event_bus = event_bus
        self.shown = False

    def show(self) -> None:
        self.shown = True


def test_rme_studio_app_constructs_container(monkeypatch: Any) -> None:
    monkeypatch.setattr(app_module, "QApplication", FakeQApplication)
    monkeypatch.setattr(app_module, "MainWindow", FakeMainWindow)

    app = RMEStudioApp(["studio"])

    assert isinstance(app.event_bus, EventBus)
    assert isinstance(app.theme, ThemeManager)
    assert isinstance(app.qt_app, FakeQApplication)
    assert isinstance(app.main_window, FakeMainWindow)
    assert app.qt_app.name == "Agente RME Studio"
    assert app.qt_app.org == "OpenTibiaBR"
    assert app.qt_app.version == "2.0.0"
    assert app.qt_app.stylesheet


def test_rme_studio_app_run_and_standalone(monkeypatch: Any) -> None:
    monkeypatch.setattr(app_module, "QApplication", FakeQApplication)
    monkeypatch.setattr(app_module, "MainWindow", FakeMainWindow)

    app = RMEStudioApp(["studio"])
    assert app.run() == 7
    assert cast(FakeMainWindow, app.main_window).shown is True
    assert cast(FakeQApplication, app.qt_app).exec_called is True

    assert RMEStudioApp.run_standalone(["studio"]) == 7


def test_app_module_imports_real_public_types() -> None:
    assert MainWindow is not None
    assert ThemeManager is not None
    assert EventBus is not None
