"""Import-boundary tests for UI core adapters."""

from __future__ import annotations

import ast
from pathlib import Path

from ui.services.null_services import NullWorldService
from ui.services.service_container import ServiceContainer

ROOT = Path(__file__).resolve().parents[2]


def _imports_core(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name in {"core", "agents"}
                or alias.name.startswith(("core.", "agents."))
                for alias in node.names
            ):
                return True
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if module in {"core", "agents"} or module.startswith(("core.", "agents.")):
                return True
    return False


def _python_files(relative: str) -> list[Path]:
    base = ROOT / relative
    return list(base.rglob("*.py")) if base.exists() else []


def test_only_ui_adapters_import_core_modules() -> None:
    forbidden = [
        path
        for folder in ("ui/pages", "ui/widgets", "ui/services")
        for path in _python_files(folder)
        if _imports_core(path)
    ]
    assert forbidden == []
    adapter_text = "\n".join(
        path.read_text(encoding="utf-8-sig") for path in _python_files("ui/adapters")
    )
    assert "core." in adapter_text


def test_null_services_remain_default_until_explicit_activation() -> None:
    container = ServiceContainer()
    container.register_defaults()
    assert isinstance(container.get_world_service(), NullWorldService)


def test_core_adapters_activate_only_when_requested() -> None:
    from ui.adapters.world_adapter import WorldAdapter

    container = ServiceContainer()
    container.register_defaults()
    container.register_core_adapters()
    assert isinstance(container.get_world_service(), WorldAdapter)
