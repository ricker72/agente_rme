from __future__ import annotations

from tests.ui.runtime_audit_support import audit_events


def test_runtime_event_bus_publish_receive_and_clear() -> None:
    result = audit_events()
    assert result["status"] == "PASS"
    assert result["received_events"] >= 2
    assert result["subscriber_count_after_clear"] == 0
    assert result["subscriber_leak_detected"] is False
    assert result["service_error_events_safe"] is True
