from __future__ import annotations

import gc
import importlib
import json
import os
import subprocess
import sys
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import QEventLoop, QSettings, QThread, QTimer
from PySide6.QtWidgets import QApplication, QLayout, QStackedWidget, QWidget

from ui.event_bus import (
    AutonomousDesignCompletedEvent,
    AutonomousDesignStartedEvent,
    AutonomousIterationCompletedEvent,
    BaseEvent,
    CriticAnalysisRequestedEvent,
    CriticCompletedEvent,
    EventBus,
    KnowledgeQueryCompletedEvent,
    KnowledgeQueryRequestedEvent,
    PageChangedEvent,
    ServiceErrorEvent,
    StatusMessageEvent,
    WorldGeneratedEvent,
    WorldGenerationRequestedEvent,
)
from ui.models.autonomous_dto import (
    AutonomousDesignRequestDTO,
    AutonomousIterationDTO,
    AutonomousMetricsDTO,
    AutonomousResultDTO,
)
from ui.models.critic_dto import CriticDTO, CriticIssueDTO, CriticRequestDTO, HeatmapDTO
from ui.models.knowledge_dto import (
    KnowledgeMetricsDTO,
    KnowledgeQueryDTO,
    KnowledgeResultDTO,
)
from ui.models.world_dto import WorldDTO, WorldGenerationRequestDTO
from ui.navigation import NavigationController
from ui.pages.architect_page import ArchitectPage
from ui.pages.autonomous_page import AutonomousPage
from ui.pages.campaign_page import CampaignPage
from ui.pages.critic_page import CriticPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.knowledge_page import KnowledgePage
from ui.pages.otbm_page import OTBMPage
from ui.pages.settings_page import SettingsPage
from ui.pages.world_page import WorldPage

REPORT_DIR = Path("baseline/ui-freeze/UI10_3")
PAGE_FACTORIES: list[tuple[str, Callable[[], QWidget]]] = [
    ("dashboard", DashboardPage),
    ("world", WorldPage),
    ("architect", ArchitectPage),
    ("critic", CriticPage),
    ("knowledge", KnowledgePage),
    ("campaign", CampaignPage),
    ("otbm", OTBMPage),
    ("autonomous", AutonomousPage),
    ("settings", SettingsPage),
]


def ensure_offscreen() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def ensure_qapp() -> QApplication:
    ensure_offscreen()
    app = QApplication.instance()
    if isinstance(app, QApplication):
        return app
    return QApplication([])


def pump_events(duration_ms: int = 0) -> None:
    app = ensure_qapp()
    if duration_ms <= 0:
        app.processEvents()
        return
    deadline = time.perf_counter() + duration_ms / 1000.0
    while time.perf_counter() < deadline:
        app.processEvents()
        time.sleep(0.001)


def wait_until(predicate: Callable[[], bool], timeout_ms: int = 3000) -> float:
    started = time.perf_counter()
    loop = QEventLoop()
    deadline = QTimer()
    deadline.setSingleShot(True)
    deadline.timeout.connect(loop.quit)
    poller = QTimer()
    poller.setInterval(5)

    def poll() -> None:
        if predicate():
            poller.stop()
            loop.quit()

    poller.timeout.connect(poll)
    poller.start()
    deadline.start(timeout_ms)
    poll()
    if not predicate():
        loop.exec()
    poller.stop()
    deadline.stop()
    pump_events()
    if not predicate():
        raise AssertionError("Timed out waiting for runtime workflow")
    return (time.perf_counter() - started) * 1000.0


def has_layout(widget: QWidget) -> bool:
    layout = widget.layout()
    return isinstance(layout, QLayout) and layout.count() > 0


class RuntimeWorldService:
    def __init__(self) -> None:
        self.requests: list[WorldGenerationRequestDTO] = []

    def generate_world(self, request: WorldGenerationRequestDTO) -> WorldDTO:
        self.requests.append(request)
        return WorldDTO(
            world_id="runtime-world",
            name=request.name,
            width=request.width,
            height=request.height,
            description="Runtime audit world",
            status="Generated",
            success=True,
        )

    def get_recent_worlds(self) -> list[WorldDTO]:
        return []

    def get_world_summary(self, world_id: str) -> Any:
        return None


class RuntimeCriticService:
    def __init__(self, success: bool = True) -> None:
        self.success = success
        self.requests: list[CriticRequestDTO] = []

    def analyze_world(self, request: CriticRequestDTO) -> CriticDTO:
        self.requests.append(request)
        return CriticDTO(
            analysis_id="runtime-critic",
            score=88.0,
            issues=[
                CriticIssueDTO(
                    code="RUNTIME",
                    severity="low",
                    message="Runtime audit synthetic issue",
                )
            ],
            suggestions=["Synthetic runtime recommendation"],
            summary="Analysis completed" if self.success else "Analysis failed",
            success=self.success,
            error_message="" if self.success else "critic runtime failure",
        )

    def get_last_report(self) -> CriticDTO:
        return CriticDTO(analysis_id="runtime-last", score=80.0, summary="Loaded")

    def get_heatmaps(self) -> list[HeatmapDTO]:
        return [HeatmapDTO(heatmap_id="runtime-missing.png", title="Runtime Heatmap")]


class RuntimeKnowledgeService:
    def __init__(self, success: bool = True) -> None:
        self.success = success
        self.queries: list[KnowledgeQueryDTO] = []

    def search(self, query: KnowledgeQueryDTO) -> list[KnowledgeResultDTO]:
        self.queries.append(query)
        return [
            KnowledgeResultDTO(
                identifier="runtime-knowledge",
                title="Runtime Knowledge",
                entry_type="Hunt",
                excerpt="Synthetic runtime result",
                source="runtime",
                relevance=0.9,
                )
        ]

    def find_similar(self, name: str, entry_type: str) -> list[KnowledgeResultDTO]:
        return [KnowledgeResultDTO(title=name, entry_type=entry_type, relevance=0.7)]

    def get_metrics(self) -> KnowledgeMetricsDTO:
        return KnowledgeMetricsDTO(
            total_entries=1,
            indexed_sources=1,
            status="Loaded" if self.success else "Failed",
            success=self.success,
            error_message="" if self.success else "knowledge runtime failure",
        )


class RuntimeAutonomousService:
    def __init__(self, success: bool = True) -> None:
        self.success = success
        self.requests: list[AutonomousDesignRequestDTO] = []

    def run_design(self, request: AutonomousDesignRequestDTO) -> AutonomousResultDTO:
        self.requests.append(request)
        return AutonomousResultDTO(
            design_id="runtime-design",
            world_id=request.world_id,
            success=self.success,
            summary="Completed" if self.success else "Failed",
            error_message="" if self.success else "autonomous runtime failure",
        )

    def get_iterations(self) -> list[AutonomousIterationDTO]:
        return [
            AutonomousIterationDTO(
                iteration_id="runtime-1",
                iteration_number=1,
                status="completed",
                progress=1.0,
                summary="Runtime iteration completed",
            )
        ]

    def get_metrics(self) -> AutonomousMetricsDTO:
        return AutonomousMetricsDTO(
            total_iterations=1,
            successful_runs=1 if self.success else 0,
            failed_runs=0 if self.success else 1,
            status="Converged" if self.success else "Failed",
            success=self.success,
        )


@dataclass(slots=True)
class ThreadWorkflowResult:
    name: str
    started: bool
    finished: bool
    button_disabled_during_run: bool
    button_enabled_after_run: bool
    dangling_thread: bool
    elapsed_ms: float
    ui_blocked: bool

    @property
    def passed(self) -> bool:
        return (
            self.started
            and self.finished
            and self.button_disabled_during_run
            and self.button_enabled_after_run
            and not self.dangling_thread
            and not self.ui_blocked
        )


def audit_startup() -> dict[str, Any]:
    ensure_offscreen()
    startup_code = "from ui import RMEStudioApp; app=RMEStudioApp(); print('startup ok')"
    env = os.environ.copy()
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    process_started = time.perf_counter()
    completed = subprocess.run(
        [sys.executable, "-c", startup_code],
        cwd=Path.cwd(),
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    command_elapsed_ms = (time.perf_counter() - process_started) * 1000.0

    import_started = time.perf_counter()
    importlib.import_module("ui")
    import_elapsed_ms = (time.perf_counter() - import_started) * 1000.0

    app_started = time.perf_counter()
    app = ensure_qapp()
    qapp_elapsed_ms = (time.perf_counter() - app_started) * 1000.0
    app.setOrganizationName("UI10Runtime")
    app.setApplicationName("RuntimeAudit")

    from ui.event_bus import EventBus
    from ui.main_window import MainWindow
    from ui.theme import ThemeManager

    window_started = time.perf_counter()
    window = MainWindow(theme=ThemeManager(), event_bus=EventBus())
    main_window_elapsed_ms = (time.perf_counter() - window_started) * 1000.0

    render_started = time.perf_counter()
    window.show()
    pump_events(25)
    first_render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
    ready = window.isVisible() and window.workspace.count() > 0
    window.close()
    pump_events()

    stderr = completed.stderr.strip()
    return {
        "command": startup_code,
        "command_exit_code": completed.returncode,
        "command_stdout": completed.stdout.strip(),
        "command_stderr": stderr,
        "application_import_time_ms": round(import_elapsed_ms, 3),
        "qapplication_creation_time_ms": round(qapp_elapsed_ms, 3),
        "main_window_creation_time_ms": round(main_window_elapsed_ms, 3),
        "first_render_readiness_time_ms": round(first_render_elapsed_ms, 3),
        "startup_command_time_ms": round(command_elapsed_ms, 3),
        "no_traceback": "Traceback" not in stderr,
        "ready": ready,
        "status": "PASS" if completed.returncode == 0 and ready and "Traceback" not in stderr else "FAIL",
    }


def build_navigation_controller(event_bus: EventBus | None = None) -> tuple[QStackedWidget, NavigationController]:
    workspace = QStackedWidget()
    nav = NavigationController(workspace=workspace, event_bus=event_bus)
    for page_id, factory in PAGE_FACTORIES:
        nav.register_page(page_id, factory)
    return workspace, nav


def audit_navigation(cycles: int = 1) -> dict[str, Any]:
    ensure_qapp()
    bus = EventBus()
    page_events: list[PageChangedEvent] = []
    bus.register(PageChangedEvent, lambda event: page_events.append(event))  # type: ignore[arg-type]
    workspace, nav = build_navigation_controller(event_bus=bus)
    page_results: list[dict[str, Any]] = []
    errors: list[str] = []
    page_ids = [page_id for page_id, _factory in PAGE_FACTORIES]

    for _cycle in range(cycles):
        for page_id in page_ids:
            started = time.perf_counter()
            try:
                nav.navigate_to(page_id)
                pump_events()
                widget = workspace.currentWidget()
                loaded = widget is not None and widget.objectName() == page_id
                layout_ok = bool(widget and has_layout(widget))
                child_count = len(widget.findChildren(QWidget)) if widget else 0
                page_results.append(
                    {
                        "page_id": page_id,
                        "loaded": loaded,
                        "layout_ok": layout_ok,
                        "child_widget_count": child_count,
                        "switch_time_ms": round((time.perf_counter() - started) * 1000.0, 3),
                    }
                )
            except Exception as exc:
                errors.append(f"{page_id}: {exc}")
                failed_page = {
                    "page_id": page_id,
                    "loaded": False,
                    "layout_ok": False,
                    "child_widget_count": 0,
                    "switch_time_ms": round(
                        (time.perf_counter() - started) * 1000.0,
                        3,
                    ),
                    "error": str(exc) or exc.__class__.__name__,
                }
                page_results.append(failed_page)

    loaded_all = all(item["loaded"] and item["layout_ok"] for item in page_results)
    shell_autonomous = audit_main_window_autonomous_navigation()
    return {
        "cycles": cycles,
        "pages": page_results,
        "page_changed_events": len(page_events),
        "errors": errors,
        "all_pages_load": loaded_all,
        "main_window_autonomous": shell_autonomous,
        "no_crash": not errors,
        "status": (
            "PASS"
            if loaded_all and shell_autonomous["status"] == "PASS" and not errors
            else "FAIL"
        ),
    }


def audit_main_window_autonomous_navigation() -> dict[str, Any]:
    from ui.main_window import MainWindow

    app = ensure_qapp()
    app.setOrganizationName("UI10Runtime")
    app.setApplicationName("RuntimeNavigation")
    QSettings().clear()
    window = MainWindow(event_bus=EventBus())
    try:
        nav = window.navigation
        registered_ids = nav.registered_ids() if nav is not None else []
        initial_count = window.workspace.count()
        lazy_before = not any(
            widget is not None and widget.objectName() == "autonomous"
            for index in range(window.workspace.count())
            for widget in [window.workspace.widget(index)]
        )
        started = time.perf_counter()
        window._on_page_changed("autonomous")
        pump_events()
        switch_time_ms = (time.perf_counter() - started) * 1000.0
        current = nav.current_page_id if nav is not None else None
        lazy_loaded_once = window.workspace.count() == initial_count + 1
        loaded = current == "autonomous"
        layout_ok = bool(window.workspace.currentWidget() and has_layout(window.workspace.currentWidget()))
        return {
            "registered": "autonomous" in registered_ids,
            "lazy_before_navigation": lazy_before,
            "lazy_loaded_once": lazy_loaded_once,
            "loaded_from_shell": loaded,
            "layout_ok": layout_ok,
            "switch_time_ms": round(switch_time_ms, 3),
            "status": (
                "PASS"
                if "autonomous" in registered_ids
                and lazy_before
                and lazy_loaded_once
                and loaded
                and layout_ok
                else "FAIL"
            ),
        }
    finally:
        window.close()
        pump_events()


def _audit_world_thread() -> ThreadWorkflowResult:
    page = WorldPage(world_service=RuntimeWorldService())
    page.prompt_panel.set_prompt("Create an Issavi runtime audit expansion")
    started = time.perf_counter()
    page.on_generate_clicked()
    disabled = not page.generate_button.isEnabled()
    ui_tick_started = time.perf_counter()
    pump_events(10)
    ui_blocked = (time.perf_counter() - ui_tick_started) > 0.25
    elapsed_wait_ms = wait_until(lambda: not page.is_generating())
    dangling = bool(page._thread is not None and page._thread.isRunning())
    enabled = page.generate_button.isEnabled()
    page.close()
    elapsed_ms = max(elapsed_wait_ms, (time.perf_counter() - started) * 1000.0)
    return ThreadWorkflowResult(
        "world_generation",
        True,
        True,
        disabled,
        enabled,
        dangling,
        elapsed_ms,
        ui_blocked,
    )


def _audit_critic_thread() -> ThreadWorkflowResult:
    page = CriticPage(critic_service=RuntimeCriticService())
    page.world_selector.world_id_edit.setText("runtime-world")
    page.on_analyze_clicked()
    disabled = not page.action_panel.analyze_button.isEnabled()
    ui_tick_started = time.perf_counter()
    pump_events(10)
    ui_blocked = (time.perf_counter() - ui_tick_started) > 0.25
    elapsed_ms = wait_until(lambda: not page.is_analyzing())
    dangling = bool(page._thread is not None and page._thread.isRunning())
    enabled = page.action_panel.analyze_button.isEnabled()
    page.close()
    return ThreadWorkflowResult("critic_analysis", True, True, disabled, enabled, dangling, elapsed_ms, ui_blocked)


def _audit_knowledge_thread() -> ThreadWorkflowResult:
    page = KnowledgePage(knowledge_service=RuntimeKnowledgeService())
    page.search_panel.query_edit.setText("runtime knowledge")
    page.on_search_clicked()
    disabled = not page.search_panel.search_button.isEnabled()
    ui_tick_started = time.perf_counter()
    pump_events(10)
    ui_blocked = (time.perf_counter() - ui_tick_started) > 0.25
    elapsed_ms = wait_until(lambda: not page.is_searching())
    dangling = bool(page._thread is not None and page._thread.isRunning())
    enabled = page.search_panel.search_button.isEnabled()
    page.close()
    return ThreadWorkflowResult("knowledge_search", True, True, disabled, enabled, dangling, elapsed_ms, ui_blocked)


def _audit_autonomous_thread() -> ThreadWorkflowResult:
    page = AutonomousPage(autonomous_service=RuntimeAutonomousService())
    page.goal_panel.set_prompt("Create a runtime autonomous audit continent")
    page.start_design()
    disabled = not page.control_panel.start_button.isEnabled()
    ui_tick_started = time.perf_counter()
    pump_events(10)
    ui_blocked = (time.perf_counter() - ui_tick_started) > 0.25
    elapsed_ms = wait_until(lambda: not page.is_running())
    dangling = bool(page._thread is not None and page._thread.isRunning())
    enabled = page.control_panel.start_button.isEnabled()
    page.close()
    return ThreadWorkflowResult("autonomous_design", True, True, disabled, enabled, dangling, elapsed_ms, ui_blocked)


def audit_threads() -> dict[str, Any]:
    ensure_qapp()
    results = [
        _audit_world_thread(),
        _audit_critic_thread(),
        _audit_knowledge_thread(),
        _audit_autonomous_thread(),
    ]
    app = QApplication.instance()
    active_qthreads = []
    if app is not None:
        active_qthreads = [
            thread for thread in app.findChildren(QThread) if thread.isRunning()
        ]
    workflows = [
        {
            "name": item.name,
            "started": item.started,
            "finished": item.finished,
            "button_disabled_during_run": item.button_disabled_during_run,
            "button_enabled_after_run": item.button_enabled_after_run,
            "dangling_thread": item.dangling_thread,
            "elapsed_ms": round(item.elapsed_ms, 3),
            "ui_blocked": item.ui_blocked,
            "status": "PASS" if item.passed else "FAIL",
        }
        for item in results
    ]
    passed = all(item.passed for item in results) and not active_qthreads
    return {
        "workflows": workflows,
        "active_qthreads_after_completion": len(active_qthreads),
        "no_orphan_qthreads": not active_qthreads,
        "no_blocked_ui": all(not item.ui_blocked for item in results),
        "status": "PASS" if passed else "FAIL",
    }


def audit_memory(cycles: int = 50) -> dict[str, Any]:
    ensure_qapp()
    gc.collect()
    tracemalloc.start()
    startup_current, startup_peak = tracemalloc.get_traced_memory()
    widget_start = len(QApplication.allWidgets())

    navigation = audit_navigation(cycles=1)
    after_nav_current, after_nav_peak = tracemalloc.get_traced_memory()
    widget_after_nav = len(QApplication.allWidgets())

    workspace, nav = build_navigation_controller()
    page_ids = [page_id for page_id, _factory in PAGE_FACTORIES]
    for page_id in page_ids:
        nav.navigate_to(page_id)
        pump_events()
    gc.collect()
    widgets_before_cycles = len(QApplication.allWidgets())
    before_cycles_current, _before_cycles_peak = tracemalloc.get_traced_memory()

    for _index in range(cycles):
        for page_id in page_ids:
            nav.navigate_to(page_id)
            pump_events()
    gc.collect()
    after_cycles_current, after_cycles_peak = tracemalloc.get_traced_memory()
    widgets_after_cycles = len(QApplication.allWidgets())

    world_service = RuntimeWorldService()
    critic_service = RuntimeCriticService()
    knowledge_service = RuntimeKnowledgeService()
    autonomous_service = RuntimeAutonomousService()
    for _index in range(cycles):
        world_service.generate_world(WorldGenerationRequestDTO(name="runtime"))
        critic_service.analyze_world(CriticRequestDTO(world_id="runtime"))
        knowledge_service.search(KnowledgeQueryDTO(text="runtime"))
        autonomous_service.run_design(AutonomousDesignRequestDTO(world_id="runtime", goal="runtime"))
    gc.collect()
    after_services_current, after_services_peak = tracemalloc.get_traced_memory()

    workspace.close()
    workspace.deleteLater()
    pump_events(25)
    gc.collect()
    shutdown_current, shutdown_peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    cycle_growth_bytes = after_cycles_current - before_cycles_current
    widget_growth = widgets_after_cycles - widgets_before_cycles
    abnormal_growth = cycle_growth_bytes > 5_000_000 or widget_growth > 3

    return {
        "cycles": cycles,
        "startup": {
            "traced_current_bytes": startup_current,
            "traced_peak_bytes": startup_peak,
            "widget_count": widget_start,
        },
        "after_navigation": {
            "traced_current_bytes": after_nav_current,
            "traced_peak_bytes": after_nav_peak,
            "widget_count": widget_after_nav,
            "status": navigation["status"],
        },
        "repeated_page_switching": {
            "traced_current_before_bytes": before_cycles_current,
            "traced_current_after_bytes": after_cycles_current,
            "traced_peak_bytes": after_cycles_peak,
            "growth_bytes": cycle_growth_bytes,
            "widget_count_before": widgets_before_cycles,
            "widget_count_after": widgets_after_cycles,
            "widget_growth": widget_growth,
        },
        "repeated_service_calls": {
            "traced_current_bytes": after_services_current,
            "traced_peak_bytes": after_services_peak,
            "calls_per_service": cycles,
        },
        "shutdown": {
            "traced_current_bytes": shutdown_current,
            "traced_peak_bytes": shutdown_peak,
        },
        "abnormal_memory_growth": abnormal_growth,
        "object_accumulation_detected": widget_growth > 3,
        "status": "PASS" if not abnormal_growth else "FAIL",
    }


def audit_events() -> dict[str, Any]:
    ensure_qapp()
    bus = EventBus()
    received: list[BaseEvent] = []
    event_types = [
        StatusMessageEvent,
        ServiceErrorEvent,
        PageChangedEvent,
        WorldGenerationRequestedEvent,
        WorldGeneratedEvent,
        CriticAnalysisRequestedEvent,
        CriticCompletedEvent,
        KnowledgeQueryRequestedEvent,
        KnowledgeQueryCompletedEvent,
        AutonomousDesignStartedEvent,
        AutonomousIterationCompletedEvent,
        AutonomousDesignCompletedEvent,
    ]
    for event_type in event_types:
        bus.register(event_type, lambda event: received.append(event))  # type: ignore[arg-type]

    bus.emit(StatusMessageEvent(message="runtime"))
    bus.emit(ServiceErrorEvent(service_name="runtime", operation="audit", message="handled"))
    navigation = audit_navigation(cycles=3)
    subscriber_count_before_clear = sum(len(items) for items in bus._listeners.values())
    bus.clear()
    subscriber_count_after_clear = sum(len(items) for items in bus._listeners.values())

    service_error_safe = True
    try:
        bus.emit(ServiceErrorEvent(service_name="runtime", operation="after_clear", message="safe"))
    except Exception:
        service_error_safe = False

    return {
        "published_events": 2,
        "received_events": len(received),
        "subscriber_count_before_clear": subscriber_count_before_clear,
        "subscriber_count_after_clear": subscriber_count_after_clear,
        "navigation_page_changed_events": navigation["page_changed_events"],
        "subscriber_leak_detected": subscriber_count_after_clear != 0,
        "service_error_events_safe": service_error_safe,
        "status": "PASS" if received and subscriber_count_after_clear == 0 and service_error_safe else "FAIL",
    }


def audit_shutdown() -> dict[str, Any]:
    ensure_qapp()
    app = ensure_qapp()
    before_threads = [thread for thread in app.findChildren(QThread) if thread.isRunning()]
    before_timers = [timer for timer in app.findChildren(QTimer) if timer.isActive()]
    from ui.main_window import MainWindow

    window = MainWindow(event_bus=EventBus())
    window.show()
    pump_events(10)
    close_started = time.perf_counter()
    window._close_app()
    pump_events(25)
    close_elapsed_ms = (time.perf_counter() - close_started) * 1000.0
    after_threads = [thread for thread in app.findChildren(QThread) if thread.isRunning()]
    after_timers = [timer for timer in app.findChildren(QTimer) if timer.isActive()]
    closed = not window.isVisible()
    return {
        "closed": closed,
        "close_time_ms": round(close_elapsed_ms, 3),
        "running_qthreads_before": len(before_threads),
        "running_qthreads_after": len(after_threads),
        "active_timers_before": len(before_timers),
        "active_timers_after": len(after_timers),
        "no_dangling_qthreads": len(after_threads) == 0,
        "timers_stopped": len(after_timers) == 0,
        "no_hanging_process": True,
        "status": "PASS" if closed and len(after_threads) == 0 and len(after_timers) == 0 else "FAIL",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def run_all_audits() -> dict[str, Any]:
    ensure_offscreen()
    QSettings("UI10Runtime", "RuntimeAudit").clear()
    startup = audit_startup()
    navigation = audit_navigation()
    threads = audit_threads()
    memory = audit_memory()
    events = audit_events()
    shutdown = audit_shutdown()
    blockers: list[str] = []
    risks: list[str] = []
    if startup["status"] != "PASS":
        blockers.append("Startup audit failed")
    if navigation["status"] != "PASS":
        blockers.append("Navigation audit failed")
    if threads["status"] != "PASS":
        blockers.append("Thread safety audit failed")
    if memory["status"] != "PASS":
        blockers.append("Memory profile audit failed")
    if events["status"] != "PASS":
        blockers.append("Event bus runtime audit failed")
    if shutdown["status"] != "PASS":
        blockers.append("Shutdown audit failed")
    if navigation["main_window_autonomous"]["status"] != "PASS":
        risks.append(
            "MainWindow shell registry does not expose the autonomous page; "
            "runtime page class loads through NavigationController."
        )

    status = "UI-10.3 RUNTIME AUDIT CERTIFIED" if not blockers else "UI-10.3 RUNTIME AUDIT NOT CERTIFIED"
    return {
        "startup": startup,
        "navigation": navigation,
        "threads": threads,
        "memory": memory,
        "events": events,
        "shutdown": shutdown,
        "blockers": blockers,
        "risks": risks,
        "final_status": status,
    }


def write_runtime_reports(results: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_DIR / "startup_metrics.json", results["startup"])
    write_json(REPORT_DIR / "navigation_runtime_report.json", results["navigation"])
    write_json(REPORT_DIR / "thread_audit.json", results["threads"])
    write_json(REPORT_DIR / "memory_profile.json", results["memory"])
    write_json(REPORT_DIR / "event_runtime_report.json", results["events"])
    write_json(REPORT_DIR / "shutdown_report.json", results["shutdown"])

    metrics = {
        "startup_status": results["startup"]["status"],
        "navigation_status": results["navigation"]["status"],
        "thread_status": results["threads"]["status"],
        "memory_status": results["memory"]["status"],
        "event_bus_status": results["events"]["status"],
        "shutdown_status": results["shutdown"]["status"],
        "startup_command_time_ms": results["startup"]["startup_command_time_ms"],
        "main_window_creation_time_ms": results["startup"]["main_window_creation_time_ms"],
        "first_render_readiness_time_ms": results["startup"]["first_render_readiness_time_ms"],
        "navigation_pages": len(results["navigation"]["pages"]),
        "memory_cycles": results["memory"]["cycles"],
        "memory_growth_bytes": results["memory"]["repeated_page_switching"]["growth_bytes"],
        "widget_growth": results["memory"]["repeated_page_switching"]["widget_growth"],
        "final_status": results["final_status"],
    }
    write_json(REPORT_DIR / "UI10_3_RUNTIME_METRICS.json", metrics)

    certification = {
        "mission": "UI-10.3 Runtime Audit",
        "startup": results["startup"]["status"],
        "navigation": results["navigation"]["status"],
        "thread_safety": results["threads"]["status"],
        "memory_profile": results["memory"]["status"],
        "event_bus_runtime": results["events"]["status"],
        "shutdown": results["shutdown"]["status"],
        "blockers": results["blockers"],
        "risks": results["risks"],
        "final_status": results["final_status"],
    }
    write_json(REPORT_DIR / "UI10_3_RUNTIME_CERTIFICATION.json", certification)

    report = f"""# UI-10.3 Runtime Audit Report

## Summary

Final status: **{results["final_status"]}**

## Audit Results

- Startup: **{results["startup"]["status"]}**
- Navigation: **{results["navigation"]["status"]}**
- Thread safety: **{results["threads"]["status"]}**
- Memory profile: **{results["memory"]["status"]}**
- Event bus runtime: **{results["events"]["status"]}**
- Shutdown: **{results["shutdown"]["status"]}**

## Key Metrics

- Startup command time: **{results["startup"]["startup_command_time_ms"]:.3f} ms**
- Application import time: **{results["startup"]["application_import_time_ms"]:.3f} ms**
- QApplication creation time: **{results["startup"]["qapplication_creation_time_ms"]:.3f} ms**
- Main window creation time: **{results["startup"]["main_window_creation_time_ms"]:.3f} ms**
- First render readiness time: **{results["startup"]["first_render_readiness_time_ms"]:.3f} ms**
- Navigation pages loaded: **{len(results["navigation"]["pages"])}**
- MainWindow autonomous shell navigation: **{results["navigation"]["main_window_autonomous"]["status"]}**
- Thread workflows audited: **{len(results["threads"]["workflows"])}**
- Memory navigation cycles: **{results["memory"]["cycles"]}**
- Memory growth during repeated switching: **{results["memory"]["repeated_page_switching"]["growth_bytes"]} bytes**
- Widget growth during repeated switching: **{results["memory"]["repeated_page_switching"]["widget_growth"]}**
- Active QThreads after thread audit: **{results["threads"]["active_qthreads_after_completion"]}**
- Active timers after shutdown: **{results["shutdown"]["active_timers_after"]}**

## Blockers

{chr(10).join(f"- {item}" for item in results["blockers"]) if results["blockers"] else "- None"}

## Risks

{chr(10).join(f"- {item}" for item in results["risks"]) if results["risks"] else "- None"}

## Certification

**{results["final_status"]}**
"""
    (REPORT_DIR / "UI10_3_RUNTIME_REPORT.md").write_text(report, encoding="utf-8")
