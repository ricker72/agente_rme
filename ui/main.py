"""Production launcher for Agente RME Studio UI."""

from __future__ import annotations

import json
import os
import sys
from typing import Any


def _run_packaging_smoke(argv: list[str]) -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    from ui.event_bus import EventBus
    from ui.main_window import MainWindow
    from ui.widgets.autonomous_chart_viewer import AutonomousChartViewer
    from ui.widgets.critic_heatmap_viewer import CriticHeatmapViewer
    from ui.widgets.world_preview_widget import WorldPreviewWidget

    app = QApplication.instance()
    if app is None:
        app = QApplication(argv)

    bus = EventBus()
    window = MainWindow(event_bus=bus)
    page_ids = [
        "dashboard",
        "world",
        "architect",
        "critic",
        "knowledge",
        "campaign",
        "otbm",
        "autonomous",
        "settings",
    ]
    pages: list[dict[str, Any]] = []
    for page_id in page_ids:
        window._on_page_changed(page_id)
        app.processEvents()
        widget = window.workspace.currentWidget()
        pages.append(
            {
                "page_id": page_id,
                "loaded": widget is not None and widget.objectName() == page_id,
                "layout": widget is not None and widget.layout() is not None,
            }
        )

    preview = WorldPreviewWidget()
    heatmap = CriticHeatmapViewer()
    charts = AutonomousChartViewer()
    resource_checks = {
        "theme_loads": bool(window.styleSheet()),
        "preview_fallback": preview.load_preview("__missing_preview__.png") is False
        and preview.preview_label.text() == "No preview available",
        "heatmap_fallback": heatmap._load_into_label("Density Heatmap", "__missing_heatmap__.png") is False
        and heatmap.labels["Density Heatmap"].text() == "No heatmap available",
        "chart_fallback": charts._load_chart("Iteration Scores", "__missing_chart__.png") is False
        and charts.labels["Iteration Scores"].text() == "No chart available",
        "config_available": os.path.exists("config.json") or os.path.exists("_internal/config.json"),
    }
    payload = {
        "startup": True,
        "main_window": window.objectName() == "",
        "pages": pages,
        "all_pages_loaded": all(item["loaded"] and item["layout"] for item in pages),
        "resource_checks": resource_checks,
        "resources_loaded": all(resource_checks.values()),
    }
    smoke_output = os.environ.get("RME_PACKAGING_SMOKE_OUTPUT")
    if smoke_output:
        with open(smoke_output, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
    print(json.dumps(payload, sort_keys=True))
    window.close()
    app.processEvents()
    return 0 if payload["all_pages_loaded"] and payload["resources_loaded"] else 1


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv if argv is None else argv)
    if "--packaging-smoke" in args:
        return _run_packaging_smoke(args)

    from ui.app import RMEStudioApp

    return RMEStudioApp(args).run()


if __name__ == "__main__":
    raise SystemExit(main())
