"""
Dashboard Data Provider for Agente RME Studio.

Provides cached access to health_report.json, metrics.json,
and GA_CERTIFICATION.json. Returns typed DTOs instead of raw
dictionaries. Includes auto-refresh infrastructure via QTimer
(disabled by default). Missing files are handled safely with
default DTO values and are logged.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

from ui.models.dashboard_dto import (
    CertificationDTO,
    HealthStatusDTO,
    MetricsDTO,
)

logger = logging.getLogger(__name__)

_JSON_FILES: dict[str, str] = {
    "health": "health_report.json",
    "metrics": "metrics.json",
    "ga_cert": "GA_CERTIFICATION.json",
}

_AUTO_REFRESH_INTERVAL_MS: int = 30_000  # 30 seconds


class DashboardDataProvider(QObject):
    """Cached provider for dashboard JSON data.

    Reads artifacts once on first access, then serves from memory.
    Supports explicit refresh(), clear_cache(), and optional auto-refresh
    via a QTimer (disabled by default).
    """

    data_updated = Signal(dict)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._cache: dict[str, dict] = {}
        self._loaded: bool = False
        self._timer: QTimer = QTimer(self)
        self._timer.setInterval(_AUTO_REFRESH_INTERVAL_MS)
        self._timer.timeout.connect(self.refresh)

        # Path resolution: check ui/services/ first, then project root
        self._search_paths: list[str] = [
            os.path.join("ui", "services"),
            os.getcwd(),
        ]

    # ------------------------------------------------------------------
    # Public cache API
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Read all JSON artifacts once and cache them in memory.

        Subsequent calls are no-ops unless clear_cache() or refresh()
        has been called.
        """
        if self._loaded:
            return
        self._read_all()
        self._loaded = True
        self.data_updated.emit(self._cache)

    def refresh(self) -> None:
        """Reload all artifacts from disk and replace cached data."""
        self._read_all()
        self._loaded = True
        self.data_updated.emit(self._cache)

    def clear_cache(self) -> None:
        """Clear all cached content.

        The next call to any getter will re-read from disk.
        """
        self._cache.clear()
        self._loaded = False

    # ------------------------------------------------------------------
    # Auto-refresh infrastructure
    # ------------------------------------------------------------------

    @property
    def auto_refresh_interval(self) -> int:
        """Return the auto-refresh interval in milliseconds."""
        interval: int = self._timer.interval()
        return interval

    @auto_refresh_interval.setter
    def auto_refresh_interval(self, ms: int) -> None:
        """Set the auto-refresh interval in milliseconds."""
        self._timer.setInterval(ms)

    def enable_auto_refresh(self) -> None:
        """Start the periodic refresh timer.

        Does nothing if the timer is already running.
        """
        if not self._timer.isActive():
            self._timer.start()

    def disable_auto_refresh(self) -> None:
        """Stop the periodic refresh timer.

        Does nothing if the timer is not running.
        """
        if self._timer.isActive():
            self._timer.stop()

    # ------------------------------------------------------------------
    # Public accessors – return DTOs
    # ------------------------------------------------------------------

    def get_health_data(self) -> HealthStatusDTO:
        """Return health status as a typed DTO.

        Missing or malformed files produce a safe default DTO.
        """
        self._ensure_loaded()
        raw = self._cache.get("health", {})

        if not raw:
            logger.warning(
                "health_report.json data is empty or missing – returning default DTO"
            )
            return HealthStatusDTO()

        overall_status = raw.get("overall_status", "Unavailable")
        summary = raw.get("summary", {})
        healthy = summary.get("healthy", 0)
        total = healthy + summary.get("degraded", 0) + summary.get("unhealthy", 0)

        return HealthStatusDTO(
            status=overall_status,
            healthy_checks=healthy,
            total_checks=total,
        )

    def get_metrics(self) -> MetricsDTO:
        """Return metrics as a typed DTO.

        Missing or malformed files produce a safe default DTO.
        """
        self._ensure_loaded()
        raw = self._cache.get("metrics", {})

        if not raw:
            logger.warning(
                "metrics.json data is empty or missing – returning default DTO"
            )
            return MetricsDTO()

        otbm_data = raw.get("otbm", {})
        generations_total = raw.get("generations_total", 0)
        errors_total = raw.get("errors_total", 0)

        success_rate = 0.0
        if generations_total > 0:
            success_rate = (
                (generations_total - errors_total) / generations_total * 100.0
            )

        return MetricsDTO(
            success_rate=round(success_rate, 2),
            worlds_generated=generations_total,
            exports_generated=otbm_data.get("tiles", 0),
        )

    def get_ga_certification(self) -> CertificationDTO:
        """Return GA certification as a typed DTO.

        Missing or malformed files produce a safe default DTO.
        """
        self._ensure_loaded()
        raw = self._cache.get("ga_cert", {})

        if not raw:
            logger.warning(
                "GA_CERTIFICATION.json data is empty or missing – returning default DTO"
            )
            return CertificationDTO()

        return CertificationDTO(
            version=raw.get("version", "Unknown"),
            certified=raw.get("overall_pass", False),
            release_status=raw.get("status", "Unknown"),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_loaded(self) -> None:
        """Lazy-load if not already cached."""
        if not self._loaded:
            self.load()

    def _read_all(self) -> None:
        """Read all JSON files from disk into the cache.

        Missing files are logged and stored as empty dicts so that
        the corresponding getter can return a safe default DTO.
        """
        for key, filename in _JSON_FILES.items():
            self._cache[key] = self._read_json_file(key, filename)

    def _read_json_file(self, key: str, filename: str) -> dict:
        # type: ignore[return]
        """Attempt to read and parse a JSON file.

        Searches self._search_paths in order. Returns an empty dict
        and logs a warning if the file is missing or corrupt.
        """
        for base_path in self._search_paths:
            filepath = os.path.join(base_path, filename)
            if os.path.isfile(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as fh:
                        result: dict = json.load(fh)
                        return result
                except (json.JSONDecodeError, PermissionError, OSError) as exc:
                    logger.warning("Failed to read %s (%s): %s", filename, key, exc)
                    return {}
        logger.warning(
            "Artifact file '%s' not found in search paths: %s",
            filename,
            self._search_paths,
        )
        return {}
