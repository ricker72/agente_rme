from __future__ import annotations

from tests.ui.runtime_audit_support import audit_startup


def test_runtime_startup_metrics() -> None:
    result = audit_startup()
    assert result["status"] == "PASS"
    assert result["command_stdout"] == "startup ok"
    assert result["no_traceback"] is True
    assert result["startup_command_time_ms"] >= 0
    assert result["main_window_creation_time_ms"] >= 0
    assert result["first_render_readiness_time_ms"] >= 0
