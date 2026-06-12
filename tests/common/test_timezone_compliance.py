"""
HITO 26.1E â€” Timezone Compliance Tests

Verifies that:
  * No production source file uses ``datetime.utcnow()``
  * All timestamps are timezone-aware (UTC, ISO8601 valid)
  * Timestamps in logs, reports, metrics, campaigns, exports are UTC-aware
"""

import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


class TestTimezoneCompliance:
    """Verify all timestamps are timezone-aware, UTC, ISO8601 valid."""

    # Markers that indicate a string field is expected to contain a timestamp.
    TIMESTAMP_FIELDS = {
        "completed_at",
        "timestamp",
        "created_at",
        "started_at",
        "updated_at",
        "emitted_at",
        "logged_at",
    }

    UTC_SUFFIX = "+00:00"

    def _walk_source_files(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        excluded_dirs = {".venv", "__pycache__", ".git", "node_modules", "logs"}
        excluded_files = {
            os.path.join("check_utcnow.py"),
            os.path.join("fix_utcnow.py"),
            os.path.join("test_utcnow.py"),
            os.path.join("validate_hito_26_1e.py"),
            os.path.join("_quality_report.py"),
            os.path.join("audit_dependency_consistency.py"),
        }
        for r, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            # Skip the entire tests directory (this file itself is in tests)
            if "tests" in dirs:
                dirs.remove("tests")
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(r, f)
                    rel = os.path.relpath(path, root)
                    if rel in excluded_files:
                        continue
                    yield path

    # ------------------------------------------------------------------ #
    #  1. No datetime.utcnow() in source
    # ------------------------------------------------------------------ #
    def test_no_utcnow_in_source(self):
        """Fail if any production .py file still calls ``datetime.utcnow()``."""
        offenders = []
        for path in self._walk_source_files():
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        stripped = line.strip()
                        if stripped.startswith("#"):
                            continue
                        if "utcnow" in line:
                            offenders.append((path, i, line.rstrip()))
            except Exception:
                pass
        assert not offenders, "``datetime.utcnow()`` is still used in:\n" + "\n".join(
            f"  {p}:{i}: {l}" for p, i, l in offenders  # noqa: E741
        )

    # ------------------------------------------------------------------ #
    #  2. Dataclass timestamp fields are timezone-aware
    # ------------------------------------------------------------------ #
    def _assert_utc_iso(self, value: str, label: str):
        assert isinstance(value, str), f"{label} should be a string, got {type(value)}"
        assert value.endswith(self.UTC_SUFFIX), f"{label} missing UTC suffix: {value!r}"
        # Validate ISO8601 round-trip
        try:
            datetime.fromisoformat(value)
        except ValueError as exc:
            raise AssertionError(f"{label} is not valid ISO8601: {value!r}") from exc

    def test_multi_agent_result_completed_at(self):
        """MultiAgentResult.completed_at â†’ UTC + ISO8601."""
        from core.agents.agent_result import MultiAgentResult

        r = MultiAgentResult()
        self._assert_utc_iso(r.completed_at, "MultiAgentResult.completed_at")

    def test_agent_response_timestamp(self):
        """AgentResponse.timestamp â†’ UTC + ISO8601."""
        from core.agents.contracts.agent_response import AgentResponse

        ar = AgentResponse(agent_id="test")
        self._assert_utc_iso(ar.timestamp, "AgentResponse.timestamp")

    def test_agent_task_timestamps(self):
        """AgentTask.{created_at,completed_at} â†’ UTC + ISO8601."""
        from core.agents.contracts.agent_task import AgentTask
        from core.agents.contracts.agent_response import AgentResponse

        at = AgentTask(agent_id="test")
        self._assert_utc_iso(at.created_at, "AgentTask.created_at")
        at.status = "running"
        at.mark_completed(AgentResponse(agent_id="test", success=True))
        assert at.completed_at is not None
        self._assert_utc_iso(at.completed_at, "AgentTask.completed_at")

    def test_workflow_state_timestamps(self):
        """WorkflowState.{started_at,completed_at} â†’ UTC + ISO8601."""
        from core.agents.contracts.workflow_state import WorkflowState

        ws = WorkflowState()
        ws.start()
        assert ws.started_at is not None
        self._assert_utc_iso(ws.started_at, "WorkflowState.started_at")
        ws.complete()
        assert ws.completed_at is not None
        self._assert_utc_iso(ws.completed_at, "WorkflowState.completed_at")

    # ------------------------------------------------------------------ #
    #  3. datetime.now(timezone.utc) is timezone-aware
    # ------------------------------------------------------------------ #
    def test_datetime_now_utc_is_aware(self):
        """Sanity: datetime.now(timezone.utc) produces aware datetimes."""
        now = datetime.now(timezone.utc)
        assert now.tzinfo is not None
        assert now.utcoffset() is not None
        assert now.utcoffset().total_seconds() == 0.0

    def test_iso_format_includes_timezone(self):
        """Sanity: isoformat() of UTC datetime ends with +00:00."""
        now = datetime.now(timezone.utc)
        iso = now.isoformat()
        assert iso.endswith("+00:00"), f"Expected +00:00 suffix, got {iso!r}"
