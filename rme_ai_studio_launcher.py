"""Production launcher for the RME AI Studio desktop shell."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from ui.live_preview.main_window import LivePreviewMainWindow
from ui.live_preview.app_paths import get_user_projects_root
from core.opentibia.assets.asset_registry import AssetRegistry
from ui.project_wizard import NecroProjectCreator, default_necro_config
from core.maintenance import cleanup_expired_artifacts
from core.world_generator.planner_database_client import PlannerDatabaseClient


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _workspace_root(runtime_root: Path) -> Path:
    bundled_root = runtime_root / "_internal"
    if getattr(sys, "frozen", False) and bundled_root.exists():
        return bundled_root
    return runtime_root


def _write_startup_log(root: Path, message: str) -> None:
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    with (logs / "RME_AI_Studio_startup.log").open("a", encoding="utf-8") as handle:
        handle.write(message.rstrip() + "\n")


def main() -> int:
    root = _runtime_root()
    workspace_root = _workspace_root(root)
    cleanup_expired_artifacts(workspace_root)
    database_server = PlannerDatabaseClient(workspace_root)
    os.environ.setdefault("RME_AI_ENV", "Production")
    _write_startup_log(root, "RME AI Studio launcher starting; Safe Mode expected.")
    _write_startup_log(
        root,
        f"Planner database server: {database_server.health().get('status', 'UNKNOWN')} "
        f"at {database_server.base_url}",
    )
    if "--create-necro-project" in sys.argv and "--exit" in sys.argv:
        projects_root = get_user_projects_root(workspace_root)
        result = NecroProjectCreator(projects_root=projects_root).create_project(default_necro_config())
        _write_startup_log(root, f"PROJECT-01B-R1 packaged creation smoke: {result['project_root']}")
        return 0
    if "--asset-health" in sys.argv and "--exit" in sys.argv:
        registry = AssetRegistry().load()
        health = registry.health_report()
        _write_startup_log(
            root,
            "PROJECT-01B-R2 packaged asset health: "
            f"assets={health['asset_count']} categories={health['category_count']} "
            f"brushes={health['brush_count']} tilesets={health['tileset_count']}",
        )
        return 0 if int(health["asset_count"]) > 10000 else 2
    app = QApplication(sys.argv)
    retention_timer = QTimer(app)
    retention_timer.setInterval(60 * 60 * 1000)
    retention_timer.timeout.connect(lambda: cleanup_expired_artifacts(workspace_root))
    retention_timer.start()
    try:
        window = LivePreviewMainWindow(workspace_root=workspace_root)
        window.show()
        _write_startup_log(
            root,
            f"Main window shown; provider_loaded={window.provider.loaded}; preview_initialized={window.preview_initialized}",
        )
        return app.exec()
    except Exception as exc:  # pragma: no cover - production safety path
        details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        _write_startup_log(root, "STARTUP_ERROR\n" + details)
        QMessageBox.critical(None, "RME AI Studio startup error", f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
