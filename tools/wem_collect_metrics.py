"""
Collect WEM-01 workspace engineering metrics from the real PySide6 workspace.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDockWidget,
    QLineEdit,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QTabWidget,
    QToolBar,
    QWidget,
)

from ui.live_preview.main_window import LivePreviewMainWindow


def _process_events(app: QApplication, milliseconds: int = 200) -> None:
    deadline = time.perf_counter() + milliseconds / 1000
    while time.perf_counter() < deadline:
        app.processEvents()
        time.sleep(0.01)


def _count_tabs(root: QWidget) -> int:
    return sum(
        tab_widget.count()
        for tab_widget in root.findChildren(QTabWidget)
        if tab_widget.isVisible()
    )


def _complexity_level(points: int) -> str:
    if points <= 30:
        return "LOW"
    if points <= 60:
        return "MODERATE"
    if points <= 90:
        return "HIGH"
    return "CRITICAL"


def collect_metrics(workspace_root: Path) -> dict[str, object]:
    app = QApplication.instance() or QApplication([])
    QSettings("RMEAIStudio", "RMEAIStudio").clear()
    visual_dir = workspace_root / "WEM-01_visual_evidence"
    visual_dir.mkdir(exist_ok=True)

    window = LivePreviewMainWindow(workspace_root)
    window.resize(1920, 1080)
    window.show()
    _process_events(app, 250)

    labels = [window.sidebar.item(index).text() for index in range(window.sidebar.count())]
    workspace_index = labels.index("Mapping Workspace")
    window.sidebar.setCurrentRow(workspace_index)
    _process_events(app, 500)

    workspace = window.mapping_workspace_page
    workspace.profile_selector.setCurrentText("Mapping")
    _process_events(app, 150)
    mapping_screenshot = visual_dir / "WEM-01_mapping_workspace.png"
    window.grab().save(str(mapping_screenshot.resolve()))

    workspace.project_dock.setFloating(True)
    _process_events(app, 150)
    dock_screenshot = visual_dir / "WEM-01_floating_project_dock.png"
    window.grab().save(str(dock_screenshot.resolve()))

    floating_windows = sum(1 for dock in workspace.findChildren(QDockWidget) if dock.isFloating())
    dock_panels = workspace.findChildren(QDockWidget)
    toolbar_actions = [
        action
        for toolbar in workspace.findChildren(QToolBar)
        for action in toolbar.actions()
        if not action.isSeparator()
    ]
    all_actions = [action for action in workspace.findChildren(QAction) if action.text()]
    visible_widgets = [widget for widget in app.allWidgets() if widget.isVisible()]
    inspector_tabs = workspace.findChild(QTabWidget, "UX03InspectorTabs")

    metrics: dict[str, object] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "workspace_version": "UX-03",
        "safe_mode_provider_loaded": window.provider.loaded,
        "safe_mode_preview_initialized": window.preview_initialized,
        "dock_panels": len(dock_panels),
        "workspace_tabs": _count_tabs(workspace),
        "asset_categories": workspace.asset_categories.count(),
        "layer_count": len(workspace.layer_toggles),
        "visible_widgets": len(visible_widgets),
        "created_widgets": len(app.allWidgets()),
        "qobject_count": len(window.findChildren(object)),
        "floating_windows": floating_windows,
        "dock_profiles": "runtime-only",
        "workspace_profiles": workspace.profile_selector.count(),
        "toolbar_actions": len(toolbar_actions),
        "action_objects": len(all_actions),
        "sidebar_entries": window.sidebar.count(),
        "inspector_panels": inspector_tabs.count() if inspector_tabs is not None else 0,
        "dialogs": len(workspace.findChildren(QDialog)),
        "context_menus": len(workspace.findChildren(QMenu)),
        "property_editors": len(workspace.findChildren(QLineEdit)),
        "runtime_panels": 2,
        "console_panels": 2,
        "ai_panels": 1,
        "dock_titles": [dock.windowTitle() for dock in dock_panels],
        "workspace_profile_names": [
            workspace.profile_selector.itemText(index)
            for index in range(workspace.profile_selector.count())
        ],
        "screenshots": {
            "mapping_workspace": str(mapping_screenshot.resolve()),
            "floating_dock": str(dock_screenshot.resolve()),
        },
        "thresholds": {
            "dock_panels": 20,
            "workspace_tabs": 30,
            "visible_widgets": 500,
            "toolbar_actions": 60,
            "dialogs": 40,
            "created_widgets": 1000,
            "qobject_count": 5000,
            "floating_windows": 15,
            "sidebar_entries": 25,
        },
    }
    thresholds = metrics["thresholds"]
    alerts = {
        "dock_panels": metrics["dock_panels"] > thresholds["dock_panels"],
        "workspace_tabs": metrics["workspace_tabs"] > thresholds["workspace_tabs"],
        "visible_widgets": metrics["visible_widgets"] > thresholds["visible_widgets"],
        "toolbar_actions": metrics["toolbar_actions"] > thresholds["toolbar_actions"],
        "dialogs": metrics["dialogs"] > thresholds["dialogs"],
        "created_widgets": metrics["created_widgets"] > thresholds["created_widgets"],
        "qobject_count": metrics["qobject_count"] > thresholds["qobject_count"],
        "floating_windows": metrics["floating_windows"] > thresholds["floating_windows"],
        "sidebar_entries": metrics["sidebar_entries"] > thresholds["sidebar_entries"],
    }
    metrics["alerts"] = alerts
    points = int(
        metrics["dock_panels"] * 2
        + metrics["workspace_tabs"]
        + metrics["toolbar_actions"]
        + metrics["sidebar_entries"]
        + metrics["dialogs"] * 2
        + metrics["context_menus"]
        + metrics["property_editors"]
    )
    metrics["complexity_points"] = points
    metrics["complexity_level"] = _complexity_level(points)

    window.close()
    app.processEvents()
    return metrics


def main() -> None:
    root = Path.cwd()
    metrics = collect_metrics(root)
    (root / "WEM-01_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    log_lines = [
        "WEM-01 execution log",
        f"timestamp={metrics['timestamp']}",
        f"safe_mode_provider_loaded={metrics['safe_mode_provider_loaded']}",
        f"safe_mode_preview_initialized={metrics['safe_mode_preview_initialized']}",
        f"dock_panels={metrics['dock_panels']}",
        f"workspace_tabs={metrics['workspace_tabs']}",
        f"visible_widgets={metrics['visible_widgets']}",
        f"created_widgets={metrics['created_widgets']}",
        f"toolbar_actions={metrics['toolbar_actions']}",
        f"sidebar_entries={metrics['sidebar_entries']}",
        f"complexity_points={metrics['complexity_points']}",
        f"complexity_level={metrics['complexity_level']}",
        f"alerts={json.dumps(metrics['alerts'], sort_keys=True)}",
    ]
    (root / "WEM-01_EXECUTION_LOG.txt").write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
