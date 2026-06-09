from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .levels import LogLevel


class Logger:
    """
    Enterprise logging system for Agente RME.

    Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

    Automatically logs to:
      - Console (stderr)
      - File: logs/agent_{date}.log

    Usage:
        log = Logger.get_logger(__name__)
        log.info("City generation started", theme="issavi")
        log.error("OTBM validation failed", tiles=500)
    """

    _instance: Optional[Logger] = None
    _initialized_handlers: bool = False
    LOG_DIR = Path("logs")

    def __init__(self, name: str = "agent_rme", level: str = "INFO"):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        if not Logger._initialized_handlers:
            self._setup_handlers()
            Logger._initialized_handlers = True

    @classmethod
    def get_logger(cls, name: str = "agent_rme", level: str = "INFO") -> logging.Logger:
        instance = cls(name, level)
        return instance._logger

    @classmethod
    def configure(cls, level: str = "INFO", log_dir: Optional[str] = None) -> None:
        """Configure global logging with the given level."""
        if log_dir:
            cls.LOG_DIR = Path(log_dir)
        cls._initialized_handlers = False
        _ = cls("agent_rme", level)

    def _setup_handlers(self) -> None:
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

        # Format
        fmt = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler (stderr)
        console = logging.StreamHandler(sys.stderr)
        console.setFormatter(fmt)
        self._logger.addHandler(console)

        # File handler
        date_str = datetime.now().strftime("%Y%m%d")
        file_path = self.LOG_DIR / f"agent_{date_str}.log"
        fh = logging.FileHandler(str(file_path), encoding="utf-8", delay=True)
        fh.setFormatter(fmt)
        self._logger.addHandler(fh)

    # ------------------------------------------------------------------
    # Structured logging helpers
    # ------------------------------------------------------------------

    @staticmethod
    def generation_start(event: str = "generation", **kwargs) -> None:
        _log_event("generation", "start", event, **kwargs)

    @staticmethod
    def generation_complete(event: str = "generation", tiles: int = 0,
                            duration_ms: float = 0, **kwargs) -> None:
        _log_event("generation", "complete", event,
                   tiles=tiles, duration_ms=duration_ms, **kwargs)

    @staticmethod
    def validation_result(event: str = "validation", passed: bool = True,
                          errors: int = 0, warnings: int = 0, **kwargs) -> None:
        _log_event("validation", "result", event,
                   passed=passed, errors=errors, warnings=warnings, **kwargs)

    @staticmethod
    def export_complete(format: str = "otbm", path: str = "",
                        size_bytes: int = 0, **kwargs) -> None:
        _log_event("export", "complete", f"{format}_export",
                   path=path, size_bytes=size_bytes, **kwargs)

    @staticmethod
    def error_summary(component: str = "", error: str = "", **kwargs) -> None:
        _log_event("error", "error", component, error_msg=error, **kwargs)


def _log_event(category: str, event_type: str, event_name: str, **kwargs) -> None:
    """Internal structured event logger."""
    log = logging.getLogger(f"agent_rme.{category}")
    extra = {f"ev_{k}": v for k, v in kwargs.items()}
    msg = f"[{event_type.upper()}] {event_name}"
    if kwargs:
        details = " ".join(f"{k}={v}" for k, v in kwargs.items())
        msg += f" | {details}"
    log.info(msg)


def get_logger(name: str = "agent_rme") -> logging.Logger:
    """Convenience function to get a named logger."""
    return logging.getLogger(name)