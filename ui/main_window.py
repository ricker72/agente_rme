"""
Main application window for Agente RME Studio.

Assembles the title bar, sidebar, workspace area, console panel,
and status bar into the final window layout.

Integrates the NavigationController for page management with lazy loading
and session restore via QSettings.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .console import ConsolePanel
from .event_bus import (
    ApplicationStartedEvent,
    ApplicationClosingEvent,
    EventBus,
)
from .navigation import NavigationController
from .sidebar import Sidebar
from .statusbar import StatusBar
from .theme import ThemeManager
from .titlebar import TitleBar


class MainWindow(QMainWindow):
    """Root window of Agente RME Studio."""

    def __init__(
        self,
        theme: ThemeManager | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        super().__init__()
        self._theme = theme or ThemeManager()
        self._event_bus = event_bus

        # Remove native title bar
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)

        # Navigation controller (created before _build_ui so pages can register)
        self._nav: NavigationController | None = None

        self._build_ui()
        self._register_pages()
        self._connect_signals()
        self._apply_styles()
        self._restore_session()

        if self._event_bus is not None:
            self._event_bus.emit(
                ApplicationStartedEvent(timestamp=__import__("time").time())
            )

    # ── layout ──────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Title bar
        self._title_bar = TitleBar(self, self._theme)
        root_layout.addWidget(self._title_bar)

        # Body: sidebar + workspace + console
        body = QWidget(self)
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar(self, self._theme)
        body_layout.addWidget(self._sidebar)

        # Vertical splitter: workspace (top) / console (bottom)
        splitter = QSplitter(Qt.Orientation.Vertical, self)
        splitter.setHandleWidth(1)

        # Workspace area — QStackedWidget managed by NavigationController
        self._workspace = QStackedWidget(self)
        self._workspace.setObjectName("Workspace")

        # Console
        self._console = ConsolePanel(self, self._theme, self._event_bus)

        splitter.addWidget(self._workspace)
        splitter.addWidget(self._console)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        body_layout.addWidget(splitter)
        root_layout.addWidget(body, 1)

        # Status bar
        self._status_bar = StatusBar(self, self._theme, self._event_bus)
        self.setStatusBar(self._status_bar)

        # Default geometry
        self.resize(1280, 800)

        # Create navigation controller
        self._nav = NavigationController(
            workspace=self._workspace,
            event_bus=self._event_bus,
            parent=self,
        )

    # ── page registration (lazy loaded) ──────────────────────────────────

    def _register_pages(self) -> None:
        """Register all workspace page factories with the navigation controller.

        Pages are **not** instantiated here — they are created on first
        navigation (lazy loading).
        """
        if self._nav is None:
            return

        from .pages.dashboard_page import DashboardPage
        from .pages.world_page import WorldPage
        from .pages.architect_page import ArchitectPage
        from .pages.critic_page import CriticPage
        from .pages.knowledge_page import KnowledgePage
        from .pages.campaign_page import CampaignPage
        from .pages.otbm_page import OTBMPage
        from .pages.autonomous_page import AutonomousPage
        from .pages.settings_page import SettingsPage

        self._nav.register_page("dashboard", DashboardPage)
        self._nav.register_page("world", WorldPage)
        self._nav.register_page("architect", ArchitectPage)
        self._nav.register_page("critic", CriticPage)
        self._nav.register_page("knowledge", KnowledgePage)
        self._nav.register_page("campaign", CampaignPage)
        self._nav.register_page("otbm", OTBMPage)
        self._nav.register_page("autonomous", AutonomousPage)
        self._nav.register_page("settings", SettingsPage)

    # ── signal wiring ───────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._title_bar.minimise_signal.connect(self.showMinimized)
        self._title_bar.maximise_signal.connect(self._toggle_maximised)
        self._title_bar.close_signal.connect(self._close_app)

        # Sidebar → NavigationController
        self._sidebar.page_changed.connect(self._on_page_changed)

    # ── styling ─────────────────────────────────────────────────────────

    def _apply_styles(self) -> None:
        p = self._theme.palette
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {p.background};
            }}
            QStackedWidget#Workspace {{
                background-color: {p.workspace_background};
                border: none;
            }}
            """
        )

    # ── session restore ─────────────────────────────────────────────────

    def _restore_session(self) -> None:
        """Restore the last-visited page from QSettings."""
        if self._nav is None:
            return
        last_page = self._nav.restore_last_page(default="dashboard")
        # Only navigate if the page is registered
        if last_page in self._nav.registered_ids():
            self._nav.navigate_to(last_page)
        else:
            self._nav.navigate_to("dashboard")

    # ── slots ───────────────────────────────────────────────────────────

    @Slot()
    def _toggle_maximised(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    @Slot()
    def _close_app(self) -> None:
        if self._event_bus is not None:
            self._event_bus.emit(
                ApplicationClosingEvent(timestamp=__import__("time").time())
            )
        # Persist current page before closing
        if self._nav is not None:
            self._nav.save_last_page()
        self.close()

    @Slot()
    def _on_page_changed(self, page_id: str) -> None:
        """Handle sidebar button clicks by delegating to the nav controller."""
        if self._nav is not None:
            self._nav.navigate_to(page_id)

    # ── public properties ───────────────────────────────────────────────

    @property
    def console(self) -> ConsolePanel:
        """Access the console panel directly."""
        return self._console

    @property
    def status_bar(self) -> StatusBar:
        """Access the status bar directly."""
        return self._status_bar

    @property
    def sidebar(self) -> Sidebar:
        """Access the sidebar directly."""
        return self._sidebar

    @property
    def workspace(self) -> QStackedWidget:
        """Access the workspace stack."""
        return self._workspace

    @property
    def title_bar(self) -> TitleBar:
        """Access the custom title bar."""
        return self._title_bar

    @property
    def navigation(self) -> NavigationController | None:
        """Access the navigation controller."""
        return self._nav
