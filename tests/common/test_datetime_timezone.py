"""
Tests verifying that ``datetime.utcnow()`` has been eliminated from the project
and replaced with timezone-aware ``datetime.now(timezone.utc)``.

Verifies:
  * All agent dataclasses produce ISO-8601 timestamps with a +00:00 suffix
  * The MultiAgentResult.completed_at, AgentResponse.timestamp,
    AgentTask.created_at, and WorkflowState timestamps are timezone-aware
  * No source file in the repository still uses datetime.utcnow()
"""

import os
import sys
import subprocess
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datetime import datetime, timezone


class TestTimezoneAwareTimestamps:
    """Verify the agent dataclasses produce timezone-aware timestamps."""

    def test_multi_agent_result_timestamp_is_timezone_aware(self):
        from agente_rme.core.agents.agent_result import MultiAgentResult
        r = MultiAgentResult()
        # Must be a string ending in +00:00 (timezone-aware)
        assert isinstance(r.completed_at, str)
        assert r.completed_at.endswith("+00:00"), \
            f"Missing +00:00 suffix: {r.completed_at}"
        # Must NOT contain the bare utcnow call
        assert "utcnow" not in r.completed_at.lower()

    def test_agent_response_timestamp_is_timezone_aware(self):
        from agente_rme.core.agents.contracts.agent_response import AgentResponse
        ar = AgentResponse(agent_id="test")
        assert ar.timestamp.endswith("+00:00"), \
            f"Missing +00:00 suffix: {ar.timestamp}"
        assert "utcnow" not in ar.timestamp.lower()

    def test_agent_task_timestamps_are_timezone_aware(self):
        from agente_rme.core.agents.contracts.agent_task import AgentTask
        at = AgentTask(agent_id="test")
        assert at.created_at.endswith("+00:00"), \
            f"Missing +00:00 suffix: {at.created_at}"
        # Complete the task to populate completed_at
        at.status = "running"
        from agente_rme.core.agents.contracts.agent_response import AgentResponse
        at.mark_completed(AgentResponse(agent_id="test", success=True))
        assert at.completed_at.endswith("+00:00"), \
            f"Missing +00:00 suffix: {at.completed_at}"
        assert "utcnow" not in at.created_at.lower()
        assert "utcnow" not in (at.completed_at or "").lower()

    def test_workflow_state_timestamps_are_timezone_aware(self):
        from agente_rme.core.agents.contracts.workflow_state import WorkflowState
        ws = WorkflowState()
        ws.start()
        assert ws.started_at is not None
        assert ws.started_at.endswith("+00:00"), \
            f"Missing +00:00 suffix: {ws.started_at}"
        ws.complete()
        assert ws.completed_at is not None
        assert ws.completed_at.endswith("+00:00"), \
            f"Missing +00:00 suffix: {ws.completed_at}"
        assert "utcnow" not in ws.started_at.lower()
        assert "utcnow" not in ws.completed_at.lower()


class TestNoDatetimeUtcnowInSource:
    """Verify that no source file outside of tests / diagnostics
    still calls ``datetime.utcnow()``."""

    EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "node_modules", "logs"}
    # Files in the repository root that are *not* part of the production
    # codebase and are allowed to mention ``utcnow`` for documentation /
    # migration purposes.
    ROOT_EXCLUDE_FILES = {
        os.path.join("check_utcnow.py"),
        os.path.join("fix_utcnow.py"),
        os.path.join("test_utcnow.py"),
        os.path.join("validate_hito_26_1e.py"),
    }

    def _walk_source_files(self):
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        for r, dirs, files in os.walk(root):
            # Skip excluded directories AND the tests directory (whose
            # mention of ``utcnow`` is part of the validation logic).
            dirs[:] = [d for d in dirs if d not in self.EXCLUDE_DIRS]
            if "tests" in dirs:
                dirs.remove("tests")
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(r, f)
                    rel = os.path.relpath(path, root)
                    if rel in self.ROOT_EXCLUDE_FILES:
                        continue
                    yield path

    def test_no_utcnow_in_source(self):
        offenders = []
        for path in self._walk_source_files():
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        # Strip out obvious comment-only lines.
                        stripped = line.strip()
                        if stripped.startswith("#"):
                            continue
                        if "utcnow" in line:
                            offenders.append((path, i, line.rstrip()))
            except Exception:
                # Binary or unreadable — skip.
                pass
        assert not offenders, (
            "datetime.utcnow() is still used in:\n"
            + "\n".join(f"  {p}:{i}: {l}" for p, i, l in offenders)
        )


class TestStandardDatetime:
    """Sanity checks for the standard datetime library usage."""

    def test_datetime_now_utc_is_timezone_aware(self):
        now = datetime.now(timezone.utc)
        assert now.tzinfo is not None
        assert now.utcoffset().total_seconds() == 0

    def test_iso_format_includes_timezone(self):
        now = datetime.now(timezone.utc)
        iso = now.isoformat()
        assert iso.endswith("+00:00")
