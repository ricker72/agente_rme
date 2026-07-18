"""
WG-20U PySide6 live preview main window.
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys
import time
import importlib
from pathlib import Path
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QObject, QSettings, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from .data_provider import LivePreviewDataProvider
from ..safe_io import SafeIOError, atomic_write_text
from .theme import stylesheet


class RuntimeLoadWorker(QObject):
    """Loads visual runtime data outside the UI thread."""

    loaded = Signal(object, object)
    failed = Signal(str)

    def __init__(self, workspace_root: Optional[Path]) -> None:
        super().__init__()
        self.workspace_root = workspace_root

    def run(self) -> None:
        try:
            provider = LivePreviewDataProvider(self.workspace_root)
            result = provider.load()
            self.loaded.emit(provider, result)
        except Exception as exc:  # pragma: no cover - exercised through UI failure path
            self.failed.emit(f"{type(exc).__name__}: {exc}")


class LivePreviewMainWindow(QMainWindow):
    """First real visual runtime environment for Agente RME AI."""

    MAX_LOG_ENTRIES = 5000

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        super().__init__()
        sys.modules.pop("core.wg20u", None)
        self.workspace_root = workspace_root
        self.provider = LivePreviewDataProvider(workspace_root)
        sys.modules.pop("core.wg20u", None)
        self.app_started_at = time.perf_counter()
        self.settings = QSettings("RMEAIStudio", "RMEAIStudio")
        self.app_metadata = self._load_app_metadata()
        self.log_entries: List[Dict[str, str]] = []
        self.logs_paused = False
        self.logs_auto_scroll = True
        self.load_thread: Optional[QThread] = None
        self.load_worker: Optional[RuntimeLoadWorker] = None
        self.preview_initialized = False
        self.operations_collapsed = False
        self.page_factories: Dict[int, Callable[[], QWidget]] = {}
        self.preview_panel_factories: Dict[str, Callable[[], QWidget]] = {}
        self.preview_panel_widgets: Dict[str, QWidget] = {}
        self.setWindowTitle(f"RME AI Studio {self.app_metadata['version']} - Safe Mode")
        self.setMinimumSize(1180, 720)
        self.resize(1600, 900)
        self.setStyleSheet(stylesheet())
        self._build_ui()
        self._restore_layout_state()
        self._set_runtime_loaded(False)
        self._notify("Safe Mode active. Runtime data is not loaded.", "info")
        self._append_log("Safe Mode booted without loading WG-20U core datasets.")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self._update_engineering_status)
        self.metrics_timer.start(5000)
        self._unload_runtime_core_modules()

    def _load_app_metadata(self) -> Dict[str, str]:
        root = Path(self.workspace_root or Path(__file__).resolve().parent.parent.parent)
        version = "0.0.0"
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib

                with pyproject.open("rb") as handle:
                    version = tomllib.load(handle).get("project", {}).get("version", version)
            except Exception:
                version = "0.0.0"
        commit = "UNKNOWN"
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0:
                commit = result.stdout.strip() or commit
        except Exception:
            commit = "UNAVAILABLE"
        return {
            "name": "RME AI Studio",
            "version": version,
            "build": os.environ.get("RME_AI_BUILD", "dev-local"),
            "commit": commit,
            "environment": os.environ.get("RME_AI_ENV", "Development"),
            "python": platform.python_version(),
            "platform": platform.platform(),
        }

    def _unload_runtime_core_modules(self) -> None:
        for name in list(sys.modules):
            if name == "core.wg20u" or name.startswith("core.wg20u."):
                sys.modules.pop(name, None)

    def refresh(self) -> None:
        if not self.provider.loaded:
            return
        if not self.preview_initialized:
            self._update_engineering_status()
            return
        events = self.provider.event_stream()
        if hasattr(self, "generation_trace"):
            self.generation_trace.set_events(events)
        if hasattr(self, "event_trace"):
            self.event_trace.set_events(events)
        if events and hasattr(self, "reasoning_panel"):
            self.reasoning_panel.set_reasoning(events[-1])
        if hasattr(self, "connectivity_panel"):
            self.connectivity_panel.set_data(self.provider.connectivity_data())
        if hasattr(self, "critic_panel"):
            self.critic_panel.set_data(self.provider.critic_data())
        if hasattr(self, "playtest_panel"):
            self.playtest_panel.set_data(self.provider.playtest_data())
        if hasattr(self, "visual_validation_panel"):
            self.visual_validation_panel.set_validation(self.provider.validation_report())
        if hasattr(self, "brush_panel"):
            self.brush_panel.set_audit(
                self.provider.datasets.get("WG20TE_SEMANTIC_BRUSH_RESOLUTION_AUDIT.json", {})
            )
        if hasattr(self, "appearance_panel"):
            self.appearance_panel.set_appearances(self.provider.appearance_sample())
        self.status_panel.set_status("Runtime data loaded. AI proposes; human approves; engineering verifies.")
        self.statusBar().showMessage("Runtime data refreshed from authoritative artifacts.", 3000)
        self._update_engineering_status()

    def _build_ui(self) -> None:
        self._build_editor_menu()
        self._build_toolbar()
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        self.notification = QLabel()
        self.notification.setObjectName("Notification")
        self.notification.setWordWrap(True)
        root.addWidget(self.notification)

        self.workspace_splitter = QSplitter(Qt.Orientation.Vertical)
        root.addWidget(self.workspace_splitter, 1)

        body = QSplitter(Qt.Orientation.Horizontal)
        body.setChildrenCollapsible(False)
        self.shell_splitter = body

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("StudioSidebar")
        self.sidebar.setMinimumWidth(240)
        self.sidebar.setMaximumWidth(320)
        self.sidebar.setWordWrap(True)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for label, tooltip in [
            ("Dashboard", "Open engineering status dashboard"),
            ("Live Preview", "Open lazy Live Preview workspace"),
            ("Runtime", "Inspect runtime and provider state"),
            ("Settings", "Configure desktop, OpenTibia, AI, paths, and developer options"),
            ("Logs", "Search, filter, copy, and export log output"),
            ("Diagnostics", "Inspect performance and desktop diagnostics"),
            ("About", "Show branding, version, build, and environment information"),
            ("Release Notes", "Review release notes for this UI baseline"),
            ("Known Issues", "Review open issues and limitations"),
            ("Future Modules", "Preview future RME AI Studio module placeholders"),
            ("Compatibility", "Review OpenTibia compatibility scope"),
            ("Export Review", "Safe export review lane"),
            ("Human Approval", "Human approval and engineering certification lane"),
            ("Mapping Workspace", "Open the UX-03 dockable OpenTibia mapping workspace"),
        ]:
            self.sidebar.addItem(self._nav_item(label, tooltip))
        self.sidebar.currentRowChanged.connect(self._navigate)

        self.stack = QStackedWidget()
        self.dashboard_page = self._build_dashboard_page()
        self.preview_page = self._placeholder_page(
            "Live Preview",
            "Preview modules are mounted lazily to keep Safe Mode startup light.",
        )
        self.runtime_page = self._lazy_placeholder("Runtime")
        self.settings_page = self._lazy_placeholder("Settings")
        self.logs_page = self._lazy_placeholder("Logs")
        self.diagnostics_page = self._lazy_placeholder("Diagnostics")
        self.about_page = self._lazy_placeholder("About")
        self.release_notes_page = self._lazy_placeholder("Release Notes")
        self.known_issues_page = self._lazy_placeholder("Known Issues")
        self.future_modules_page = self._lazy_placeholder("Future Modules")
        self.compatibility_page = self._lazy_placeholder("Compatibility")
        self.export_page = self._lazy_placeholder("Export Review")
        self.approval_page = self._lazy_placeholder("Human Approval")
        self.mapping_workspace_page = self._lazy_placeholder("Mapping Workspace")
        pages = [
            self.dashboard_page,
            self.preview_page,
            self.runtime_page,
            self.settings_page,
            self.logs_page,
            self.diagnostics_page,
            self.about_page,
            self.release_notes_page,
            self.known_issues_page,
            self.future_modules_page,
            self.compatibility_page,
            self.export_page,
            self.approval_page,
            self.mapping_workspace_page,
        ]
        for page in pages:
            self.stack.addWidget(page)
        self.page_factories = {
            2: self._build_runtime_page,
            3: self._build_settings_page,
            4: self._build_logs_page,
            5: self._build_diagnostics_page,
            6: self._build_about_page,
            7: self._build_release_notes_page,
            8: self._build_known_issues_page,
            9: self._build_future_modules_page,
            10: lambda: self._placeholder_page(
                "Compatibility",
                "OpenTibia-only compatibility checks for RME, OTBM, Canary, TFS, OTServBR, and OTClient.",
            ),
            11: lambda: self._placeholder_page(
                "Export Review",
                "Safe review lane for export evidence. No certification is shown until execution evidence exists.",
            ),
            12: lambda: self._placeholder_page(
                "Human Approval",
                "AI proposes changes here. Human approval remains required before engineering certification.",
            ),
            13: self._build_mapping_workspace_page,
        }

        body.addWidget(self.sidebar)
        body.addWidget(self.stack)
        body.setSizes([300, 1280])
        body.setStretchFactor(1, 1)

        self.operations_panel = QWidget()
        self.operations_panel.setObjectName("OperationsPanel")
        self.operations_panel.setMinimumHeight(120)
        operations_layout = QVBoxLayout(self.operations_panel)
        operations_layout.setContentsMargins(0, 0, 0, 0)
        operations_layout.setSpacing(6)
        operations_header = QHBoxLayout()
        self.operations_toggle = QPushButton("Hide Operations")
        self.operations_toggle.setObjectName("OperationsToggle")
        self.operations_toggle.clicked.connect(self.toggle_operations)
        operations_title = QLabel("Operations Console")
        operations_title.setObjectName("PanelTitle")
        operations_header.addWidget(operations_title)
        operations_header.addStretch(1)
        operations_header.addWidget(self.operations_toggle)
        self.log_panel = QPlainTextEdit()
        self.log_panel.setObjectName("ConsoleLog")
        self.log_panel.setReadOnly(True)
        self.log_panel.document().setMaximumBlockCount(self.MAX_LOG_ENTRIES)
        self.log_panel.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.log_panel.setMinimumHeight(120)
        self.log_panel.setPlaceholderText("Safe Mode console")
        operations_layout.addLayout(operations_header)
        operations_layout.addWidget(self.log_panel, 1)

        self.workspace_splitter.addWidget(body)
        self.workspace_splitter.addWidget(self.operations_panel)
        self.workspace_splitter.setChildrenCollapsible(False)
        self.workspace_splitter.setStretchFactor(0, 1)
        self.workspace_splitter.setStretchFactor(1, 0)
        self.workspace_splitter.setSizes([720, 42])
        self.statusBar().showMessage("Safe Mode active")
        self.setCentralWidget(central)
        self.operations_collapsed = True
        self.log_panel.setVisible(False)
        self.operations_toggle.setText("Show Operations")
        self.operations_panel.setMinimumHeight(36)
        self.operations_panel.setMaximumHeight(42)
        self.operations_panel.hide()
        self.sidebar.setCurrentRow(13)
        QTimer.singleShot(0, self._apply_initial_layout_sizes)

    def _build_editor_menu(self) -> None:
        menu_bar = self.menuBar()
        menu_bar.setObjectName("RMEEditorMenu")
        menus: Dict[str, QMenu] = {}
        for title in ["File", "Edit", "Map", "Select", "View", "Window", "Floor", "Scripts", "AI", "Help"]:
            menu = menu_bar.addMenu(title)
            menu.setObjectName(f"RMEEditorMenu_{title}")
            menus[title] = menu

        dashboard_action = QAction("Engineering Dashboard", self)
        dashboard_action.setObjectName("ViewEngineeringDashboardAction")
        dashboard_action.triggered.connect(self.open_engineering_dashboard)
        menus["View"].addAction(dashboard_action)
        operations_action = QAction("Operations Console", self)
        operations_action.setObjectName("ViewOperationsConsoleAction")
        operations_action.triggered.connect(self.open_operations_console)
        menus["View"].addAction(operations_action)

    def open_engineering_dashboard(self) -> None:
        self._ensure_lazy_page(0)
        self.sidebar.setVisible(True)
        self.sidebar.setCurrentRow(0)

    def open_operations_console(self) -> None:
        if self.operations_collapsed:
            self.toggle_operations()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Mapping")
        toolbar.setObjectName("StudioToolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(toolbar)

        style = self.style()
        actions = [
            ("New", "Ctrl+N", style.standardIcon(style.StandardPixmap.SP_FileIcon), self.open_new_project_wizard),
            ("Open", "Ctrl+O", style.standardIcon(style.StandardPixmap.SP_DialogOpenButton), lambda: self.statusBar().showMessage("Open Project", 2000)),
            ("Save", "Ctrl+S", style.standardIcon(style.StandardPixmap.SP_DialogSaveButton), lambda: self.statusBar().showMessage("Save Project", 2000)),
            ("Undo", "Ctrl+Z", style.standardIcon(style.StandardPixmap.SP_ArrowBack), lambda: self.statusBar().showMessage("Undo", 2000)),
            ("Redo", "Ctrl+Y", style.standardIcon(style.StandardPixmap.SP_ArrowForward), lambda: self.statusBar().showMessage("Redo", 2000)),
            ("Cut", "Ctrl+X", style.standardIcon(style.StandardPixmap.SP_DialogDiscardButton), lambda: self.statusBar().showMessage("Cut", 2000)),
            ("Copy", "Ctrl+C", style.standardIcon(style.StandardPixmap.SP_FileDialogContentsView), lambda: self.statusBar().showMessage("Copy", 2000)),
            ("Paste", "Ctrl+V", style.standardIcon(style.StandardPixmap.SP_DialogApplyButton), lambda: self.statusBar().showMessage("Paste", 2000)),
            ("Brush", "B", style.standardIcon(style.StandardPixmap.SP_FileDialogDetailedView), lambda: self.sidebar.setCurrentRow(13)),
            ("Erase", "E", style.standardIcon(style.StandardPixmap.SP_TrashIcon), lambda: self.statusBar().showMessage("Erase", 2000)),
            ("Select", "S", style.standardIcon(style.StandardPixmap.SP_DirHomeIcon), lambda: self.sidebar.setCurrentRow(13)),
            ("Floor", "F", style.standardIcon(style.StandardPixmap.SP_ArrowUp), lambda: self.statusBar().showMessage("Floor 7", 2000)),
            ("Zoom", "Z", style.standardIcon(style.StandardPixmap.SP_ComputerIcon), lambda: self.statusBar().showMessage("Zoom 100%", 2000)),
        ]
        for text, shortcut, icon, callback in actions:
            action = QAction(icon, text, self)
            action.setShortcut(QKeySequence(shortcut))
            action.setToolTip(f"{text} ({shortcut})")
            action.triggered.connect(callback)
            toolbar.addAction(action)
        toolbar.addSeparator()
        self.environment_label = QLabel(
            f"{self.app_metadata['environment']} | v{self.app_metadata['version']} | {self.app_metadata['build']}"
        )
        self.environment_label.setObjectName("EnvironmentIndicator")
        toolbar.addWidget(self.environment_label)

    def _nav_item(self, label: str, tooltip: str) -> QListWidgetItem:
        item = QListWidgetItem(label)
        item.setToolTip(tooltip)
        item.setData(Qt.ItemDataRole.UserRole, label)
        icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileIcon)
        if label == "Dashboard":
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon)
        elif label == "Live Preview":
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogDetailedView)
        elif label in {"Runtime", "Diagnostics"}:
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_BrowserReload)
        elif label in {"Settings"}:
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogContentsView)
        elif label in {"Logs", "Release Notes", "Known Issues"}:
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_FileDialogInfoView)
        elif label == "Mapping Workspace":
            icon = self.style().standardIcon(self.style().StandardPixmap.SP_DirHomeIcon)
        item.setIcon(icon)
        return item

    def _build_mapping_workspace_page(self) -> QWidget:
        from .mapping_workspace import OpenTibiaMappingWorkspacePage

        page = OpenTibiaMappingWorkspacePage(self.workspace_root)
        recent = self._recent_necro_project_context()
        if recent and hasattr(page, "load_necro_project_context"):
            page.load_necro_project_context(recent)
        return page

    def _recent_necro_project_context(self) -> Optional[Dict[str, object]]:
        projects_root = self._project_workspace_root()
        recent_path = projects_root / "recent_projects.json"
        if not recent_path.exists():
            return None
        try:
            import json

            payload = json.loads(recent_path.read_text(encoding="utf-8"))
            projects = payload.get("projects", [])
            if not projects:
                return None
            project = projects[0]
            project_root = Path(str(project.get("path", projects_root / "NECRO")))
            return {
                "project_root": project_root,
                "config": {
                    "project_name": project.get("project_name", "Necro"),
                    "town_name": project.get("town_name", "Necro"),
                    "temple": project.get("temple", {"x": 1000, "y": 1000, "z": 7}),
                    "map_width": 4096,
                    "map_height": 4096,
                },
            }
        except Exception as exc:
            self._append_log(f"Recent NECRO context unavailable: {type(exc).__name__}: {exc}")
            return None

    def _project_workspace_root(self) -> Path:
        from .app_paths import get_user_projects_root

        return get_user_projects_root(self.workspace_root)

    def open_new_project_wizard(self, use_defaults: bool = False):
        from ui.project_wizard import NecroNewProjectWizard, NecroProjectCreator, default_necro_config

        projects_root = self._project_workspace_root()
        if use_defaults:
            result = NecroProjectCreator(projects_root=projects_root).create_project(default_necro_config())
        else:
            wizard = NecroNewProjectWizard(projects_root, self)
            if wizard.exec() != wizard.DialogCode.Accepted:
                self._append_log("New Project wizard canceled.")
                return None
            result = wizard.create_project()

        self._ensure_lazy_page(13)
        self.sidebar.setCurrentRow(13)
        self.stack.setCurrentIndex(13)
        page = self.stack.widget(13)
        if hasattr(page, "load_necro_project_context"):
            page.load_necro_project_context(result)
        self._append_log(f"PROJECT-01B NECRO project initialized at {result.get('project_root')}.")
        self.statusBar().showMessage("New world initialized. Ready for editing.", 5000)
        return result

    def _build_dashboard_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        title = QLabel("RME AI Studio")
        title.setObjectName("PageTitle")
        version = QLabel(
            f"Version {self.app_metadata['version']} | Build {self.app_metadata['build']} | "
            f"Commit {self.app_metadata['commit']} | {self.app_metadata['environment']}"
        )
        version.setObjectName("SubtleText")
        version.setWordWrap(True)
        subtitle = QLabel(
            "Safe Mode base. OpenTibia scope only. Runtime data loads only after explicit action."
        )
        subtitle.setWordWrap(True)

        actions = QHBoxLayout()
        self.load_button = QPushButton("Load runtime data")
        self.load_button.setToolTip("Loads authoritative WG-20U artifacts in a worker thread.")
        self.load_button.clicked.connect(self.load_runtime_data)
        self.refresh_button = QPushButton("Refresh panels")
        self.refresh_button.clicked.connect(self._refresh_requested)
        self.refresh_button.setEnabled(False)
        actions.addWidget(self.load_button)
        actions.addWidget(self.refresh_button)
        actions.addStretch(1)

        self.loading = QProgressBar()
        self.loading.setRange(0, 1)
        self.loading.setValue(0)
        self.loading.setTextVisible(True)
        self.loading.setFormat("Runtime idle")

        cards = QGridLayout()
        self.safe_mode_card = self._status_card("Safe Mode", "ACTIVE")
        self.runtime_card = self._status_card("Runtime Core", "NOT LOADED")
        self.scope_card = self._status_card("Project Scope", "OpenTibia only")
        self.approval_card = self._status_card("Governance", "Human approval required")
        self.provider_card = self._status_card("Provider", "NOT LOADED")
        self.preview_card = self._status_card("Preview", "NOT INITIALIZED")
        self.memory_card = self._status_card("Memory Usage", "PENDING")
        self.cpu_card = self._status_card("CPU Usage", "PENDING")
        self.thread_card = self._status_card("Thread Status", "UI thread active")
        self.wg_card = self._status_card("WG Status", "PRESERVED")
        self.ep_card = self._status_card("EP Status", "PRESERVED")
        self.ph_card = self._status_card("PH Status", "PRESERVED")
        self.validation_card = self._status_card("Last Validation", "UX-01R5C pending human approval")
        self.project_card = self._status_card("Current Project", str(Path(self.workspace_root or Path.cwd()).name))
        self.world_card = self._status_card("Current World", "No world loaded in Safe Mode")
        for index, card in enumerate(
            [
                self.safe_mode_card,
                self.runtime_card,
                self.provider_card,
                self.preview_card,
                self.scope_card,
                self.validation_card,
                self.wg_card,
                self.ep_card,
                self.ph_card,
                self.memory_card,
                self.cpu_card,
                self.thread_card,
                self.project_card,
                self.world_card,
                self.approval_card,
            ]
        ):
            cards.addWidget(card, index // 3, index % 3)

        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(subtitle)
        layout.addLayout(actions)
        layout.addWidget(self.loading)
        layout.addLayout(cards)
        layout.addStretch(1)
        return page

    def _build_preview_page(self) -> QWidget:
        from .floor_selector import FloorSelector
        from .generation_trace_widget import GenerationTraceWidget
        from .minimap_widget import MinimapWidget
        from .status_panel import StatusPanel
        from .viewport_factory import create_rme_viewport

        page = QWidget()
        root = QHBoxLayout(page)
        root.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("PreviewSplitter")
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter)

        left = QWidget()
        left.setObjectName("WorkspacePanel")
        left.setMinimumWidth(240)
        left.setMaximumWidth(420)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(6, 6, 6, 6)
        dashboard_button = QPushButton("Dashboard")
        dashboard_button.setToolTip("Return to the Safe Mode dashboard.")
        dashboard_button.clicked.connect(lambda: self.sidebar.setCurrentRow(0))
        self.floor_selector = FloorSelector()
        self.minimap = MinimapWidget()
        self.status_panel = StatusPanel()
        left_layout.addWidget(dashboard_button)
        left_layout.addWidget(self.floor_selector)
        left_layout.addWidget(self.minimap)
        left_layout.addWidget(self.status_panel)

        self.viewport = create_rme_viewport()
        self.viewport.setMinimumWidth(600)
        self.viewport.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.floor_selector.floorChanged.connect(self.viewport.set_floor)
        self.viewport.tileSelected.connect(self._on_tile_selected)

        tabs = QTabWidget()
        tabs.setObjectName("IntelligenceTabs")
        tabs.setMinimumWidth(280)
        tabs.setMaximumWidth(520)
        tabs.setUsesScrollButtons(True)
        tabs.setElideMode(Qt.TextElideMode.ElideRight)
        tabs.tabBar().setExpanding(False)
        tabs.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.intelligence_tabs = tabs
        self.generation_trace = GenerationTraceWidget()
        self.preview_panel_widgets = {"Trace": self.generation_trace}
        self.preview_panel_factories = {
            "Events": self._preview_panel_factory("event_trace", ".event_trace_panel", "EventTracePanel"),
            "Reasoning": self._preview_panel_factory("reasoning_panel", ".reasoning_panel", "ReasoningPanel"),
            "Tile": self._preview_panel_factory("tile_inspector", ".tile_inspector", "TileInspector"),
            "Connectivity": self._preview_panel_factory("connectivity_panel", ".connectivity_panel", "ConnectivityPanel"),
            "Brush": self._preview_panel_factory("brush_panel", ".brush_panel", "BrushPanel"),
            "Appearance": self._preview_panel_factory("appearance_panel", ".appearance_panel", "AppearancePanel"),
            "NPC": self._preview_panel_factory("npc_panel", ".npc_panel", "NpcPanel"),
            "Quest": self._preview_panel_factory("quest_panel", ".quest_panel", "QuestPanel"),
            "Spawn": self._preview_panel_factory("spawn_panel", ".spawn_panel", "SpawnPanel"),
            "Critic": self._preview_panel_factory("critic_panel", ".critic_panel", "CriticPanel"),
            "Playtest": self._preview_panel_factory("playtest_panel", ".playtest_panel", "PlaytestPanel"),
            "Visual Truth": self._preview_panel_factory("visual_validation_panel", ".visual_validation_panel", "VisualValidationPanel"),
        }

        tabs.addTab(self.generation_trace, "Trace")
        for label in self.preview_panel_factories:
            tabs.addTab(
                self._placeholder_page(
                    label,
                    f"{label} panel will mount when selected to preserve Safe Mode performance.",
                ),
                label,
            )
        tabs.currentChanged.connect(self._ensure_preview_tab)

        splitter.addWidget(left)
        splitter.addWidget(self.viewport)
        splitter.addWidget(tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([300, 940, 360])
        self.preview_splitter = splitter
        return page

    def _preview_panel_factory(self, attribute: str, module_name: str, class_name: str) -> Callable[[], QWidget]:
        def build() -> QWidget:
            module = importlib.import_module(module_name, package=__package__)
            widget = getattr(module, class_name)()
            setattr(self, attribute, widget)
            return widget

        return build

    def _ensure_preview_tab(self, index: int) -> None:
        if not hasattr(self, "intelligence_tabs") or index < 0:
            return
        label = self.intelligence_tabs.tabText(index)
        if label in self.preview_panel_widgets:
            return
        factory = self.preview_panel_factories.get(label)
        if factory is None:
            return
        widget = factory()
        old_widget = self.intelligence_tabs.widget(index)
        self.intelligence_tabs.removeTab(index)
        self.intelligence_tabs.insertTab(index, widget, label)
        self.intelligence_tabs.setCurrentIndex(index)
        if old_widget is not None:
            old_widget.deleteLater()
        self.preview_panel_widgets[label] = widget
        if self.provider.loaded:
            self.refresh()
        self._append_log(f"Preview panel mounted lazily: {label}", "DEBUG")

    def _ensure_preview_tab_by_label(self, label: str) -> None:
        if not hasattr(self, "intelligence_tabs"):
            return
        for index in range(self.intelligence_tabs.count()):
            if self.intelligence_tabs.tabText(index) == label:
                self._ensure_preview_tab(index)
                return

    def _on_tile_selected(self, x: int, y: int, z: int) -> None:
        self._ensure_preview_tab_by_label("Tile")
        self.tile_inspector.set_tile(self.provider.tile_data(x, y, z))
        self._append_log(f"Tile selected: x={x}, y={y}, z={z}")
        self.statusBar().showMessage(f"Selected tile {x},{y},{z}", 2500)

    def _build_runtime_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        header = QLabel("Runtime Center")
        header.setObjectName("PageTitle")
        intro = QLabel("Safe runtime visibility without loading OpenTibia or WG-20U provider data at startup.")
        intro.setWordWrap(True)
        self.runtime_state = QPlainTextEdit()
        self.runtime_state.setReadOnly(True)
        self.runtime_state.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.runtime_state.setMinimumHeight(260)
        layout.addWidget(header)
        layout.addWidget(intro)
        layout.addWidget(self.runtime_state, 1)
        return page

    def _build_settings_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        header = QLabel("Settings Center")
        header.setObjectName("PageTitle")
        layout.addWidget(header)
        sections = {
            "General": ["Restore desktop layout", "Confirm before loading runtime data"],
            "Appearance": ["Dark professional theme", "High contrast focus outline"],
            "Performance": ["Lazy preview initialization", "Console auto-scroll"],
            "OpenTibia": ["RME compatibility mode", "OTBM-safe UI operations"],
            "Export": ["Human approval required before export certification"],
            "AI": ["AI proposes; human approves; engineering certifies"],
            "Paths": ["Workspace root", "Recent project"],
            "Updates": ["Release notes visible before baseline freeze"],
            "Developer": ["Diagnostics page enabled", "Runtime page enabled"],
        }
        for section, options in sections.items():
            panel = QFrame()
            panel.setObjectName("LivePreviewPanel")
            form = QFormLayout(panel)
            title = QLabel(section)
            title.setObjectName("PanelTitle")
            form.addRow(title)
            for option in options:
                checkbox = QCheckBox(option)
                checkbox.setChecked(True)
                checkbox.setToolTip(f"{section}: {option}")
                form.addRow(checkbox)
            layout.addWidget(panel)
        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    def _build_logs_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        header = QLabel("Logging Center")
        header.setObjectName("PageTitle")
        controls = QHBoxLayout()
        self.log_filter = QComboBox()
        self.log_filter.addItems(["ALL", "INFO", "WARNING", "ERROR", "SUCCESS", "DEBUG"])
        self.log_filter.currentTextChanged.connect(self._refresh_logs_page)
        self.log_search = QLineEdit()
        self.log_search.setPlaceholderText("Search logs")
        self.log_search.textChanged.connect(self._refresh_logs_page)
        self.pause_logs = QCheckBox("Pause")
        self.pause_logs.toggled.connect(self._set_logs_paused)
        self.auto_scroll_logs = QCheckBox("Auto-scroll")
        self.auto_scroll_logs.setChecked(True)
        self.auto_scroll_logs.toggled.connect(self._set_logs_auto_scroll)
        copy_button = QPushButton("Copy selected")
        copy_button.clicked.connect(self._copy_selected_log)
        export_button = QPushButton("Export log")
        export_button.clicked.connect(self._export_log)
        for widget in [
            self.log_filter,
            self.log_search,
            self.pause_logs,
            self.auto_scroll_logs,
            copy_button,
            export_button,
        ]:
            controls.addWidget(widget)
        self.logs_list = QListWidget()
        self.logs_list.setWordWrap(True)
        self.logs_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(header)
        layout.addLayout(controls)
        layout.addWidget(self.logs_list, 1)
        return page

    def _build_diagnostics_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        header = QLabel("Diagnostics")
        header.setObjectName("PageTitle")
        self.diagnostics_state = QPlainTextEdit()
        self.diagnostics_state.setReadOnly(True)
        self.diagnostics_state.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(header)
        layout.addWidget(self.diagnostics_state, 1)
        return page

    def _build_about_page(self) -> QWidget:
        lines = [
            f"{self.app_metadata['name']}",
            f"Version: {self.app_metadata['version']}",
            f"Build: {self.app_metadata['build']}",
            f"Commit: {self.app_metadata['commit']}",
            f"Environment: {self.app_metadata['environment']}",
            f"Python: {self.app_metadata['python']}",
            f"Platform: {self.app_metadata['platform']}",
            "",
            "Scope: OpenTibia engineering environment for RME, OTBM, Canary, TFS, OTServBR, and OTClient workflows.",
            "Principle: AI proposes. Human approves. Engineering certifies.",
        ]
        return self._text_page("About", "\n".join(lines))

    def _build_release_notes_page(self) -> QWidget:
        return self._text_page(
            "Release Notes",
            "\n".join(
                [
                    "UX-02 Professional Desktop Experience",
                    "- Added dynamic branding and environment indicator.",
                    "- Added Runtime, Settings, Logs, Diagnostics, About, Release Notes, Known Issues, and Future Modules pages.",
                    "- Added engineering status dashboard metrics.",
                    "- Added logging center with filter/search/export/copy/pause/autoscroll.",
                    "- Preserved Safe Mode, lazy runtime provider loading, and lazy preview initialization.",
                ]
            ),
        )

    def _build_known_issues_page(self) -> QWidget:
        return self._text_page(
            "Known Issues",
            "\n".join(
                [
                    "No SUCCESS or CERTIFIED status is claimed without direct execution evidence.",
                    "",
                    "Open observations:",
                    "- Live Preview module initialization remains memory-heavy compared with Safe Mode startup.",
                    "- CPU metrics depend on psutil availability.",
                    "- Future module pages are safe placeholders and do not execute module-specific workflows.",
                    "- Desktop baseline freeze requires human approval after evidence review.",
                ]
            ),
        )

    def _build_future_modules_page(self) -> QWidget:
        modules = [
            "Blueprint Intelligence",
            "World Generation",
            "Knowledge Base",
            "Critic Engine",
            "Campaign Generator",
            "Asset Browser",
            "NPC Studio",
            "Quest Studio",
            "Spawn Studio",
            "Export Center",
        ]
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        header = QLabel("Future Modules")
        header.setObjectName("PageTitle")
        layout.addWidget(header)
        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        for index, name in enumerate(modules):
            card = self._status_card(name, "Prepared placeholder. No runtime module loaded.")
            grid.addWidget(card, index // 2, index % 2)
        layout.addWidget(grid_container)
        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    def _text_page(self, title: str, text: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        header = QLabel(title)
        header.setObjectName("PageTitle")
        body = QPlainTextEdit()
        body.setReadOnly(True)
        body.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        body.setPlainText(text)
        layout.addWidget(header)
        layout.addWidget(body, 1)
        return page

    def _build_console_page(self) -> QWidget:
        return self._placeholder_page(
            "Console",
            "Live log is pinned below the workspace and mirrors navigation, loading, refresh, and selection feedback.",
        )

    def _placeholder_page(self, title: str, message: str) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        header = QLabel(title)
        header.setObjectName("PageTitle")
        body = QLabel(message)
        body.setWordWrap(True)
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(header)
        layout.addWidget(body)
        layout.addStretch(1)
        scroll.setWidget(container)
        return scroll

    def _lazy_placeholder(self, title: str) -> QWidget:
        return self._placeholder_page(
            title,
            f"{title} will mount on first navigation. Safe Mode keeps startup lightweight.",
        )

    def _ensure_lazy_page(self, index: int) -> None:
        factory = self.page_factories.pop(index, None)
        if factory is None:
            return
        current = self.stack.widget(index)
        page = factory()
        self.stack.removeWidget(current)
        current.deleteLater()
        self.stack.insertWidget(index, page)
        page_attribute = {
            2: "runtime_page",
            3: "settings_page",
            4: "logs_page",
            5: "diagnostics_page",
            6: "about_page",
            7: "release_notes_page",
            8: "known_issues_page",
            9: "future_modules_page",
            10: "compatibility_page",
            11: "export_page",
            12: "approval_page",
            13: "mapping_workspace_page",
        }.get(index)
        if page_attribute:
            setattr(self, page_attribute, page)
        if index == 4:
            self._refresh_logs_page()
        self._update_engineering_status()
        item = self.sidebar.item(index)
        label = item.text() if item else f"Page {index}"
        self._append_log(f"Page mounted lazily: {label}", "DEBUG")

    def _status_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setObjectName("LivePreviewPanel")
        layout = QVBoxLayout(card)
        label = QLabel(title)
        label.setObjectName("PanelTitle")
        status = QLabel(value)
        status.setWordWrap(True)
        layout.addWidget(label)
        layout.addWidget(status)
        card.status_label = status  # type: ignore[attr-defined]
        return card

    def _navigate(self, index: int) -> None:
        if index < 0:
            return
        if index == 1:
            self._ensure_preview_page()
            self.notification.hide()
            self.sidebar.setVisible(False)
            self.shell_splitter.setSizes([0, max(1, self.width())])
            if hasattr(self, "preview_splitter"):
                self.preview_splitter.setSizes([300, max(600, self.width() - 660), 360])
        elif index == 13:
            self._ensure_lazy_page(index)
            self.notification.hide()
            self.sidebar.setVisible(False)
            self.shell_splitter.setSizes([0, max(1, self.width())])
            if hasattr(self, "preview_splitter"):
                self.preview_splitter.setSizes([300, max(600, self.width() - 660), 360])
        else:
            self._ensure_lazy_page(index)
            self.notification.show()
            self.sidebar.setVisible(True)
            self.shell_splitter.setSizes([300, max(1, self.width() - 300)])
        self.stack.setCurrentIndex(index)
        item = self.sidebar.item(index)
        label = item.text() if item else f"Page {index}"
        self._append_log(f"Navigation: {label}")
        self.statusBar().showMessage(f"Opened {label}", 2000)

    def load_runtime_data(self) -> None:
        if self.load_thread is not None:
            self._notify("Runtime data is already loading.", "warning")
            return
        self._set_loading(True)
        self._append_log("Runtime load requested by user action.")
        self.load_thread = QThread(self)
        self.load_worker = RuntimeLoadWorker(self.workspace_root)
        self.load_worker.moveToThread(self.load_thread)
        self.load_thread.started.connect(self.load_worker.run)
        self.load_worker.loaded.connect(self._runtime_loaded)
        self.load_worker.failed.connect(self._runtime_failed)
        self.load_worker.loaded.connect(self.load_thread.quit)
        self.load_worker.failed.connect(self.load_thread.quit)
        self.load_thread.finished.connect(self._cleanup_load_worker)
        self.load_thread.start()

    def _runtime_loaded(self, provider: LivePreviewDataProvider, result: object) -> None:
        self.provider = provider
        self._ensure_preview_page()
        self._set_runtime_loaded(True)
        self._set_loading(False)
        self._notify("Runtime data loaded from authoritative artifacts.", "info")
        self._append_log(f"Runtime load completed: {result}", "SUCCESS")
        self.refresh()

    def _runtime_failed(self, message: str) -> None:
        self._set_loading(False)
        self._notify(f"Runtime load failed: {message}", "error")
        self._append_log(f"ERROR: Runtime load failed: {message}")

    def _cleanup_load_worker(self) -> None:
        if self.load_worker is not None:
            self.load_worker.deleteLater()
        if self.load_thread is not None:
            self.load_thread.deleteLater()
        self.load_worker = None
        self.load_thread = None

    def _refresh_requested(self) -> None:
        self.refresh()
        self._append_log("Manual refresh requested.")

    def _set_loading(self, loading: bool) -> None:
        self.load_button.setEnabled(not loading)
        self.refresh_button.setEnabled((not loading) and self.provider.loaded)
        self.loading.setRange(0, 0 if loading else 1)
        self.loading.setValue(0 if loading else 1)
        self.loading.setFormat("Loading runtime data..." if loading else "Runtime ready" if self.provider.loaded else "Runtime idle")
        self.statusBar().showMessage("Loading runtime data..." if loading else "Safe Mode active")

    def toggle_operations(self) -> None:
        self.operations_collapsed = not self.operations_collapsed
        self.operations_panel.setVisible(not self.operations_collapsed)
        self.log_panel.setVisible(not self.operations_collapsed)
        self.operations_toggle.setText("Show Operations" if self.operations_collapsed else "Hide Operations")
        if self.operations_collapsed:
            self.operations_panel.setMinimumHeight(36)
            self.operations_panel.setMaximumHeight(42)
            self.workspace_splitter.setSizes([max(1, self.height() - 42), 42])
            self._append_log("Operations console collapsed.")
        else:
            self.operations_panel.setMinimumHeight(120)
            self.operations_panel.setMaximumHeight(16777215)
            self.workspace_splitter.setSizes([max(1, self.height() - 180), 180])
            self._append_log("Operations console expanded.")

    def _apply_initial_layout_sizes(self) -> None:
        operations_height = 42 if self.operations_collapsed else 180
        self.workspace_splitter.setSizes([max(1, self.height() - operations_height), operations_height])
        if self.sidebar.isVisible():
            self.shell_splitter.setSizes([300, max(1, self.width() - 300)])
        else:
            self.shell_splitter.setSizes([0, max(1, self.width())])
        if hasattr(self, "preview_splitter"):
            self.preview_splitter.setSizes([300, max(600, self.width() - 660), 360])

    def _set_runtime_loaded(self, loaded: bool) -> None:
        self.refresh_button.setEnabled(loaded)
        self.runtime_card.status_label.setText("LOADED" if loaded else "NOT LOADED")  # type: ignore[attr-defined]
        self.provider_card.status_label.setText("LOADED" if loaded else "NOT LOADED")  # type: ignore[attr-defined]
        if self.preview_initialized:
            self.status_panel.set_status(
                "Runtime loaded" if loaded else "Safe Mode active. Runtime data not loaded."
            )
        self._update_engineering_status()

    def _ensure_preview_page(self) -> None:
        if self.preview_initialized:
            return
        preview = self._build_preview_page()
        self.stack.removeWidget(self.preview_page)
        self.preview_page.deleteLater()
        self.preview_page = preview
        self.stack.insertWidget(1, self.preview_page)
        self.preview_initialized = True
        preview_sizes = self.settings.value("previewSplitterSizes")
        if preview_sizes:
            self.preview_splitter.restoreState(preview_sizes)
        self._append_log("Live Preview page mounted lazily.")

    def _notify(self, message: str, level: str) -> None:
        self.notification.setText(message)
        self.notification.setProperty("level", level)
        self.notification.style().unpolish(self.notification)
        self.notification.style().polish(self.notification)
        if hasattr(self, "sidebar") and self.sidebar.currentRow() == 13:
            self.notification.hide()
        else:
            self.notification.show()

    def _append_log(self, message: str, category: str = "INFO") -> None:
        self._append_log_entry(message, category)

    def _append_log_entry(self, message: str, category: str = "INFO") -> None:
        entry = {
            "category": category,
            "message": message,
            "elapsed": f"{time.perf_counter() - self.app_started_at:.2f}s",
        }
        self.log_entries.append(entry)
        if len(self.log_entries) > self.MAX_LOG_ENTRIES:
            del self.log_entries[: len(self.log_entries) - self.MAX_LOG_ENTRIES]
        line = f"[{entry['elapsed']}] [{category}] {message}"
        self.log_panel.appendPlainText(line)
        if (
            hasattr(self, "logs_list")
            and not self.logs_paused
            and hasattr(self, "logs_page")
            and self.stack.currentWidget() is self.logs_page
        ):
            self._refresh_logs_page()

    def _refresh_logs_page(self) -> None:
        if not hasattr(self, "logs_list"):
            return
        category = self.log_filter.currentText() if hasattr(self, "log_filter") else "ALL"
        query = self.log_search.text().lower() if hasattr(self, "log_search") else ""
        self.logs_list.clear()
        for entry in self.log_entries:
            if category != "ALL" and entry["category"] != category:
                continue
            line = f"[{entry['elapsed']}] [{entry['category']}] {entry['message']}"
            if query and query not in line.lower():
                continue
            self.logs_list.addItem(line)
        if self.logs_auto_scroll and self.logs_list.count():
            self.logs_list.scrollToBottom()

    def _set_logs_paused(self, paused: bool) -> None:
        self.logs_paused = paused
        self._append_log_entry("Logs paused." if paused else "Logs resumed.", "DEBUG")

    def _set_logs_auto_scroll(self, enabled: bool) -> None:
        self.logs_auto_scroll = enabled
        self._append_log_entry(f"Log auto-scroll {'enabled' if enabled else 'disabled'}.", "DEBUG")

    def _copy_selected_log(self) -> None:
        item = self.logs_list.currentItem() if hasattr(self, "logs_list") else None
        if item is not None:
            QApplication.clipboard().setText(item.text())
            self._append_log_entry("Selected log copied to clipboard.", "SUCCESS")

    def _export_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export log", "rme_ai_studio.log", "Log Files (*.log);;Text Files (*.txt)")
        if not path:
            return
        self._export_log_to_path(Path(path))

    def _export_log_to_path(self, path: Path) -> None:
        lines = [f"[{e['elapsed']}] [{e['category']}] {e['message']}" for e in self.log_entries]
        try:
            atomic_write_text(path, "\n".join(lines) + "\n")
        except SafeIOError as exc:
            self._append_log_entry(f"Log export failed: {exc}", "ERROR")
            self._notify("Log export failed; existing file was preserved.", "error")
            return
        self._append_log_entry(f"Log exported to {path}", "SUCCESS")

    def _update_engineering_status(self) -> None:
        memory = "UNAVAILABLE"
        cpu = "UNAVAILABLE"
        threads = "UI thread active"
        try:
            import psutil

            process = psutil.Process()
            memory = f"{process.memory_info().rss / (1024 * 1024):.2f} MB"
            cpu = f"{process.cpu_percent(interval=None):.1f}%"
            threads = f"{process.num_threads()} process threads"
        except Exception:
            pass
        if hasattr(self, "memory_card"):
            self.memory_card.status_label.setText(memory)  # type: ignore[attr-defined]
            self.cpu_card.status_label.setText(cpu)  # type: ignore[attr-defined]
            self.thread_card.status_label.setText(threads)  # type: ignore[attr-defined]
            self.preview_card.status_label.setText("INITIALIZED" if self.preview_initialized else "NOT INITIALIZED")  # type: ignore[attr-defined]
            self.provider_card.status_label.setText("LOADED" if self.provider.loaded else "NOT LOADED")  # type: ignore[attr-defined]
            self.runtime_card.status_label.setText("LOADED" if self.provider.loaded else "NOT LOADED")  # type: ignore[attr-defined]
        if hasattr(self, "runtime_state"):
            self.runtime_state.setPlainText(
                "\n".join(
                    [
                        f"Loaded modules: {'WG-20U provider' if self.provider.loaded else 'None'}",
                        "Lazy modules: Live Preview, WG-20U provider, visual validation datasets",
                        f"Provider state: {'loaded' if self.provider.loaded else 'not loaded'}",
                        f"Preview state: {'initialized' if self.preview_initialized else 'not initialized'}",
                        f"Runtime workers: {'active' if self.load_thread is not None else 'idle'}",
                        "Running tasks: none",
                        "Pending tasks: none",
                        "Execution queue: empty",
                        f"Background workers: {'runtime loader pending' if self.load_thread is not None else 'none'}",
                    ]
                )
            )
        if hasattr(self, "diagnostics_state"):
            self.diagnostics_state.setPlainText(
                "\n".join(
                    [
                        f"RAM: {memory}",
                        f"CPU: {cpu}",
                        f"Threads: {threads}",
                        "FPS (viewport): not instrumented",
                        "Qt Events: timer refresh active",
                        f"Background Jobs: {'runtime loader' if self.load_thread is not None else 'none'}",
                        "Preview Refresh: 1000 ms timer when provider loaded",
                        f"Lazy Loading Statistics: provider_loaded={self.provider.loaded}, preview_initialized={self.preview_initialized}",
                        f"Window: {self.width()}x{self.height()}",
                        f"Operations collapsed: {self.operations_collapsed}",
                    ]
                )
            )

    def _restore_layout_state(self) -> None:
        geometry = self.settings.value("windowGeometry")
        if geometry:
            self.restoreGeometry(geometry)
        workspace_sizes = self.settings.value("workspaceSplitterSizes")
        if workspace_sizes:
            QTimer.singleShot(0, lambda: self.workspace_splitter.restoreState(workspace_sizes))
        shell_sizes = self.settings.value("shellSplitterSizes")
        if shell_sizes:
            QTimer.singleShot(0, lambda: self.shell_splitter.restoreState(shell_sizes))
        self.operations_collapsed = True
        QTimer.singleShot(0, lambda: self.sidebar.setCurrentRow(13))

    def closeEvent(self, event: object) -> None:
        if hasattr(self, "timer"):
            self.timer.stop()
        if hasattr(self, "metrics_timer"):
            self.metrics_timer.stop()
        if self.load_thread is not None and self.load_thread.isRunning():
            self.load_thread.requestInterruption()
            self.load_thread.quit()
            if not self.load_thread.wait(3000):
                self._notify(
                    "Runtime loading is still finishing. Close again when it completes.",
                    "warning",
                )
                ignore = getattr(event, "ignore", None)
                if callable(ignore):
                    ignore()
                return
        self.settings.setValue("windowGeometry", self.saveGeometry())
        self.settings.setValue("workspaceSplitterSizes", self.workspace_splitter.saveState())
        self.settings.setValue("shellSplitterSizes", self.shell_splitter.saveState())
        if hasattr(self, "preview_splitter"):
            self.settings.setValue("previewSplitterSizes", self.preview_splitter.saveState())
        self.settings.setValue("theme", "dark-professional")
        self.settings.setValue("operationsCollapsed", self.operations_collapsed)
        current = self.sidebar.currentItem()
        self.settings.setValue("selectedPage", current.text() if current else "Mapping Workspace")
        super().closeEvent(event)
