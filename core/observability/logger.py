"""
core/observability/logger.py

Enterprise observability logger for Agente RME v1.0.0 GA.

Provides structured JSON logging for:
  - agent execution
  - errors
  - performance metrics
  - memory
  - OTBM operations

Exports log events to:
  - logs/agent_{date}.log    (rotating)
  - logs/events.jsonl        (structured JSONL stream)

Usage:
    from core.observability.logger import get_observability_logger
    log = get_observability_logger()
    log.event("agent.start", agent="world", level=300)
    log.error("OTBM write failed", component="otbm_exporter")
"""

from __future__ import annotations

import json
import logging
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_OBS_LOCK = threading.Lock()
_OBS_LOGGER: Optional["ObservabilityLogger"] = None
_OBS_DIR: Path = Path("logs")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObservabilityLogger:
    """Structured JSON logger for observability events."""

    LOG_DIR = Path("logs")
    EVENTS_FILE = "events.jsonl"

    def __init__(self, name: str = "agent_rme.observability", level: str = "INFO"):
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
            self._setup_handlers()

    def _setup_handlers(self) -> None:
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

        fmt = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(fmt)
        self._logger.addHandler(console)

        date_str = datetime.now().strftime("%Y%m%d")
        fh = logging.FileHandler(
            self.LOG_DIR / f"observability_{date_str}.log", encoding="utf-8"
        )
        fh.setFormatter(fmt)
        self._logger.addHandler(fh)

    # ------------------------------------------------------------------
    # Event helpers
    # ------------------------------------------------------------------

    def event(self, name: str, **fields: Any) -> None:
        """Emit a structured event (info-level)."""
        self._emit(logging.INFO, name, fields)

    def warn(self, name: str, **fields: Any) -> None:
        self._emit(logging.WARNING, name, fields)

    def error(self, name: str, **fields: Any) -> None:
        self._emit(logging.ERROR, name, fields)

    def debug(self, name: str, **fields: Any) -> None:
        self._emit(logging.DEBUG, name, fields)

    def _emit(self, level: int, name: str, fields: Dict[str, Any]) -> None:
        record = {
            "ts": _utc_iso(),
            "event": name,
            **fields,
        }
        try:
            line = json.dumps(record, default=str, ensure_ascii=False)
        except (TypeError, ValueError):
            line = json.dumps(
                {"ts": record["ts"], "event": name, "error": "non-serializable"}
            )
        self._logger.log(level, line)
        # Also append to JSONL stream
        try:
            with _OBS_LOCK:
                with open(self.LOG_DIR / self.EVENTS_FILE, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
        except OSError:
            pass


def get_observability_logger() -> ObservabilityLogger:
    """Return a singleton observability logger."""
    global _OBS_LOGGER
    with _OBS_LOCK:
        if _OBS_LOGGER is None:
            _OBS_LOGGER = ObservabilityLogger()
    return _OBS_LOGGER


def reset_observability_logger() -> None:
    """Reset the singleton (for tests)."""
    global _OBS_LOGGER
    with _OBS_LOCK:
        _OBS_LOGGER = None
