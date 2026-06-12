from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from ui.dashboard_data_provider import DashboardDataProvider
from ui.plugins import PluginBase, PluginManager


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_legacy_dashboard_provider_defaults_and_metrics(tmp_path: Path) -> None:
    provider = DashboardDataProvider(str(tmp_path))

    metrics = provider.get_metrics()
    assert [metric.title for metric in metrics] == [
        "Worlds Generated",
        "Knowledge Entries",
        "Critic Score",
        "Success Rate",
        "OTBM Exports",
        "Campaigns Generated",
    ]
    assert metrics[0].value == "0"
    assert provider.get_health().healthy == 0
    assert provider.get_artifacts() == []
    assert provider.get_activity()[0].timestamp == "No Data"
    assert provider.get_system_status().ui_status == "ONLINE"
    assert provider.get_all_data().release_info.name == "RME Agente AI"


def test_legacy_dashboard_provider_reads_output_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    (output / "generated.otbm").write_bytes(b"abc")
    (output / "big.otbm").write_bytes(b"x")
    _write_json(output / "knowledge_metrics.json", {"total_entries": 9})
    _write_json(output / "critic.json", {"score": 87.25})
    _write_json(output / "agent_metrics.json", {"agent_success_rate": 91.5})
    _write_json(output / "campaign.json", {"name": "Campaign"})
    _write_json(output / "health_report.json", {"status": "warning"})
    _write_json(output / "report.json", {"ok": True})

    provider = DashboardDataProvider(str(tmp_path))

    assert [metric.value for metric in provider.get_metrics()] == [
        "2",
        "9",
        "87.2%",
        "91.5%",
        "2",
        "1",
    ]
    assert provider.get_health().warning == 1
    assert provider.get_artifacts()[0].name in {"generated.otbm", "report.json", "campaign.json"}
    activity = {item.label: item.timestamp for item in provider.get_activity()}
    assert activity["Last Export"] != "No Data"
    assert activity["Last Critic"] != "No Data"
    assert activity["Last Knowledge Build"] != "No Data"
    assert activity["Last Campaign"] != "No Data"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        ("healthy", (1, 0, 0)),
        ("error", (0, 0, 1)),
        ("unknown", (0, 0, 0)),
    ],
)
def test_legacy_dashboard_provider_health_variants(
    tmp_path: Path, status: str, expected: tuple[int, int, int]
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    _write_json(output / "health_report.json", {"status": status})

    health = DashboardDataProvider(str(tmp_path)).get_health()

    assert (health.healthy, health.warning, health.error) == expected


def test_legacy_dashboard_provider_reads_root_json_invalid_json_and_file_sizes(
    tmp_path: Path,
) -> None:
    _write_json(tmp_path / "critic.json", {"score": ""})
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    output = tmp_path / "output"
    output.mkdir()
    small = output / "small.txt"
    kb = output / "kb.txt"
    mb = output / "mb.txt"
    small.write_bytes(b"x" * 42)
    kb.write_bytes(b"x" * 2048)
    mb.write_bytes(b"x" * (2 * 1024 * 1024))

    provider = DashboardDataProvider(str(tmp_path))

    assert provider._read_json("critic.json") == {"score": ""}
    assert provider._read_json("bad.json") == {}
    assert provider._read_json("missing.json") == {}
    assert provider._get_file_info(tmp_path / "missing.txt") is None
    small_info = provider._get_file_info(small)
    kb_info = provider._get_file_info(kb)
    mb_info = provider._get_file_info(mb)
    assert small_info is not None
    assert kb_info is not None
    assert mb_info is not None
    assert small_info.size == "42 B"
    assert kb_info.size == "2.0 KB"
    assert mb_info.size == "2.0 MB"


def test_legacy_dashboard_provider_release_info_sources(tmp_path: Path) -> None:
    version_file = tmp_path / "VERSION"
    version_file.write_text("10.2-R", encoding="utf-8")
    assert DashboardDataProvider(str(tmp_path)).get_release_info().version == "10.2-R"

    version_file.unlink()
    (tmp_path / "version.py").write_text('__version__ = "2.5.0"\n', encoding="utf-8")
    assert DashboardDataProvider(str(tmp_path)).get_release_info().version == "2.5.0"

    (tmp_path / "version.py").unlink()
    (tmp_path / "pyproject.toml").write_text(
        '[build-system]\nrequires = []\n[project]\nversion = "3.1.4"\n',
        encoding="utf-8",
    )
    assert DashboardDataProvider(str(tmp_path)).get_release_info().version == "v3.1.4"


def test_plugin_base_defaults_and_manual_lifecycle() -> None:
    class DemoPlugin(PluginBase):
        def __init__(self) -> None:
            self.events: list[str] = []

        def on_load(self, app: Any) -> None:
            self.events.append(f"load:{app}")

        def on_unload(self) -> None:
            self.events.append("unload")

    plugin = DemoPlugin()
    manager = PluginManager()
    manager.register(plugin)

    assert plugin.plugin_id == "DemoPlugin"
    assert set(manager.plugins) == {"DemoPlugin"}
    assert manager.loaded == set()
    assert manager.load_all("app") == ["DemoPlugin"]
    assert manager.load_all("app") == []
    assert manager.loaded == {"DemoPlugin"}
    assert manager.unload_all() == ["DemoPlugin"]
    assert plugin.events == ["load:app", "unload"]
    assert manager.loaded == set()


def test_plugin_manager_discovers_plugins_and_skips_broken_modules(tmp_path: Path) -> None:
    package_dir = tmp_path / "sample_plugins"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "good.py").write_text(
        "from ui.plugins import PluginBase\n"
        "class ExternalPlugin(PluginBase):\n"
        "    def on_load(self, app):\n"
        "        self.app = app\n",
        encoding="utf-8",
    )
    (package_dir / "broken.py").write_text("raise RuntimeError('broken')\n", encoding="utf-8")

    sys.path.insert(0, str(tmp_path))
    try:
        manager = PluginManager()
        found = manager.discover("sample_plugins")
    finally:
        sys.path.remove(str(tmp_path))
        sys.modules.pop("sample_plugins", None)
        sys.modules.pop("sample_plugins.good", None)

    assert found == ["ExternalPlugin"]
    assert set(manager.plugins) == {"ExternalPlugin"}


def test_plugin_manager_handles_import_and_lifecycle_failures() -> None:
    class FailingLoadPlugin(PluginBase):
        def on_load(self, app: Any) -> None:
            raise RuntimeError("load failed")

    class FailingUnloadPlugin(PluginBase):
        def on_unload(self) -> None:
            raise RuntimeError("unload failed")

    manager = PluginManager()
    manager.register(FailingLoadPlugin())
    manager.register(FailingUnloadPlugin())

    assert manager.discover("missing_plugin_package") == []
    assert manager.load_all(object()) == ["FailingUnloadPlugin"]
    assert manager.unload_all() == ["FailingUnloadPlugin"]
