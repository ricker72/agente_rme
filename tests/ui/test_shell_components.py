from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QPushButton

from ui.console import ConsolePanel
from ui.event_bus import (
    ApplicationClosingEvent,
    ApplicationStartedEvent,
    ConsoleMessageEvent,
    EventBus,
    ServiceStateChangedEvent,
    StatusMessageEvent,
)
from ui.main_window import MainWindow
from ui.sidebar import Sidebar
from ui.statusbar import StatusBar
from ui.titlebar import TitleBar, TitleBarButton


def test_titlebar_constructs_and_emits_control_signals(qapp_instance: Any) -> None:
    titlebar = TitleBar()
    seen: list[str] = []
    titlebar.minimise_signal.connect(lambda: seen.append("min"))
    titlebar.maximise_signal.connect(lambda: seen.append("max"))
    titlebar.close_signal.connect(lambda: seen.append("close"))

    titlebar.set_title("Coverage Shell")
    buttons = titlebar.findChildren(TitleBarButton)
    assert titlebar.objectName() == "TitleBar"
    assert titlebar.height() == 32
    assert len(buttons) == 3

    for button in buttons:
        button.click()

    titlebar.mousePressEvent(None)
    titlebar.mouseMoveEvent(None)
    titlebar.mouseReleaseEvent(None)
    assert seen == ["min", "max", "close"]


def test_sidebar_constructs_buttons_and_emits_navigation(qapp_instance: Any) -> None:
    sidebar = Sidebar()
    emitted: list[str] = []
    sidebar.page_changed.connect(emitted.append)

    buttons = {
        button.objectName().replace("SidebarButton_", ""): button
        for button in sidebar.findChildren(QPushButton)
    }
    assert sidebar.objectName() == "Sidebar"
    assert sidebar.width() == 48
    assert set(buttons) == {page_id for page_id, _icon, _tooltip in Sidebar.ICONS}

    buttons["dashboard"].click()
    buttons["settings"].click()
    assert emitted == ["dashboard", "settings"]
    assert buttons["otbm"].toolTip() == "OTBM"


def test_statusbar_manual_and_event_bus_updates(qapp_instance: Any) -> None:
    bus = EventBus()
    statusbar = StatusBar(event_bus=bus)

    statusbar.set_status("Booted")
    assert statusbar.currentMessage() == "Booted"

    statusbar.set_service_state("Builder", "running")
    assert statusbar._service_label.text() == "Builder: running"

    bus.emit(StatusMessageEvent(message="From bus", timeout_ms=1))
    assert statusbar.currentMessage() == "From bus"
    assert statusbar._clear_timer.isActive()
    statusbar._clear_timed_message()
    assert statusbar.currentMessage() == ""

    bus.emit(ServiceStateChangedEvent(service_name="Critic", state="idle"))
    assert statusbar._service_label.text() == "Critic: idle"


def test_console_renders_messages_and_colours(qapp_instance: Any) -> None:
    bus = EventBus()
    console = ConsolePanel(event_bus=bus)
    assert console.isReadOnly()
    assert console.maximumBlockCount() == ConsolePanel.MAX_BLOCKS
    assert console._colour_for_level("info").name().lower() == "#6a9955"
    assert console._colour_for_level("missing").name().lower() == "#cccccc"

    console.log("Ready", source="shell")
    bus.emit(ConsoleMessageEvent(level="error", message="Failed", source="svc"))
    text = console.toPlainText()
    assert "INFO  [shell] Ready" in text
    assert "ERROR [svc] Failed" in text

    console.clear_console()
    assert console.toPlainText() == ""


def test_main_window_safe_startup_navigation_and_shutdown(qapp_instance: Any) -> None:
    qapp_instance.setOrganizationName("UITestOrg")
    qapp_instance.setApplicationName("UITestShell")
    QSettings().clear()

    bus = EventBus()
    events: list[object] = []
    bus.register(ApplicationStartedEvent, events.append)
    bus.register(ApplicationClosingEvent, events.append)

    window = MainWindow(event_bus=bus)
    try:
        assert window.workspace.count() >= 1
        assert window.navigation is not None
        assert "dashboard" in window.navigation.registered_ids()
        assert window.console is window._console
        assert window.status_bar is window._status_bar
        assert window.sidebar is window._sidebar
        assert window.title_bar is window._title_bar

        window._on_page_changed("settings")
        assert window.navigation.current_page_id == "settings"
        window._on_page_changed("unknown")
        assert window.navigation.current_page_id == "settings"

        window._toggle_maximised()
        assert window.isMaximized()
        window._toggle_maximised()
        assert not window.isMaximized()

        window._close_app()
        assert any(isinstance(event, ApplicationStartedEvent) for event in events)
        assert any(isinstance(event, ApplicationClosingEvent) for event in events)
    finally:
        window.close()


def test_main_window_handles_missing_navigation_branches(qapp_instance: Any) -> None:
    window = MainWindow()
    try:
        window._nav = None
        window._register_pages()
        window._restore_session()
        window._on_page_changed("dashboard")
        window._close_app()
    finally:
        window.close()
