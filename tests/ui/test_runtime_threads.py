from __future__ import annotations

from tests.ui.runtime_audit_support import audit_threads


def test_runtime_thread_workflows_complete_cleanly() -> None:
    result = audit_threads()
    assert result["status"] == "PASS"
    assert result["no_orphan_qthreads"] is True
    assert result["no_blocked_ui"] is True
    assert result["active_qthreads_after_completion"] == 0
    assert all(workflow["button_disabled_during_run"] for workflow in result["workflows"])
    assert all(workflow["button_enabled_after_run"] for workflow in result["workflows"])
