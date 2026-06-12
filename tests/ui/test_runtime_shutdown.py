from __future__ import annotations

from tests.ui.runtime_audit_support import audit_shutdown


def test_runtime_shutdown_closes_cleanly() -> None:
    result = audit_shutdown()
    assert result["status"] == "PASS"
    assert result["closed"] is True
    assert result["no_dangling_qthreads"] is True
    assert result["timers_stopped"] is True
    assert result["no_hanging_process"] is True
