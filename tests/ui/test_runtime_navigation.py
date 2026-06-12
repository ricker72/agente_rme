from __future__ import annotations

from tests.ui.runtime_audit_support import audit_navigation


def test_runtime_navigation_all_pages_load() -> None:
    result = audit_navigation()
    assert result["status"] == "PASS"
    assert result["all_pages_load"] is True
    assert result["main_window_autonomous"]["status"] == "PASS"
    assert result["main_window_autonomous"]["registered"] is True
    assert result["main_window_autonomous"]["lazy_before_navigation"] is True
    assert result["main_window_autonomous"]["loaded_from_shell"] is True
    assert result["no_crash"] is True
    assert {page["page_id"] for page in result["pages"]} == {
        "dashboard",
        "world",
        "architect",
        "critic",
        "knowledge",
        "campaign",
        "otbm",
        "autonomous",
        "settings",
    }
    assert all(page["switch_time_ms"] >= 0 for page in result["pages"])
