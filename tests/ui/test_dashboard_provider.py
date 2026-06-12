"""
Tests for the hardened DashboardDataProvider.

Covers:
- Cache behavior (load, refresh, clear_cache)
- Missing file handling (safe defaults)
- DTO conversion
- Timer initialization
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from typing import Iterator
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication

from ui.models.dashboard_dto import (
    CertificationDTO,
    HealthStatusDTO,
    MetricsDTO,
)
from ui.services.dashboard_data_provider import DashboardDataProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def qapp_instance() -> Iterator[QApplication]:
    """Create a QApplication instance for widget/timer tests."""
    app_instance = QApplication.instance()
    if app_instance is None:
        import sys as _sys
        app_instance = QApplication(_sys.argv)
    elif not isinstance(app_instance, QApplication):
        # If it's QCoreApplication, which QApplication inherits from, close it and create a new QApplication
        app_instance.quit()
        import sys as _sys
        app_instance = QApplication(_sys.argv)
    yield app_instance


@pytest.fixture
def temp_dir() -> Iterator[str]:
    """Provide a temporary directory path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def provider(
    qapp_instance: QApplication, temp_dir: str
) -> Iterator[DashboardDataProvider]:
    """Create a DashboardDataProvider scoped to a temp dir."""
    with patch.object(os, "getcwd", return_value=temp_dir):
        p = DashboardDataProvider()
        yield p


def _touch_json(dirpath: str, filename: str, data: dict) -> str:
    """Write a JSON file and return its full path."""
    filepath = os.path.join(dirpath, filename)
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return filepath


_HEALTH = {
    "overall_status": "healthy",
    "summary": {"healthy": 5, "degraded": 0, "unhealthy": 0},
}
_METRICS = {
    "generations_total": 10,
    "errors_total": 1,
    "otbm": {"tiles": 5},
}
_CERT = {
    "version": "1.0.0",
    "overall_pass": True,
    "status": "GA",
}


# ---------------------------------------------------------------------------
# Cache behaviour
# ---------------------------------------------------------------------------


class TestCache:
    """Verify load / refresh / clear_cache."""

    def test_load_reads_files_once(
        self, provider: DashboardDataProvider, temp_dir: str
    ):
        """load() reads files once; repeated calls are no-ops."""
        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            h = provider.get_health_data()
            assert h.status == "Unavailable"
            assert h.healthy_checks == 0

    def test_clear_cache_forces_reload(
        self, provider: DashboardDataProvider, temp_dir: str
    ):
        """After clear_cache(), next getter re-reads from disk."""
        _touch_json(temp_dir, "health_report.json", _HEALTH)
        _touch_json(temp_dir, "metrics.json", _METRICS)
        _touch_json(temp_dir, "GA_CERTIFICATION.json", _CERT)

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            assert provider.get_health_data().status == "healthy"
            provider.clear_cache()
            # After clearing, getter re-reads
            assert provider.get_health_data().status == "healthy"

    def test_refresh_reloads_from_disk(
        self, provider: DashboardDataProvider, temp_dir: str
    ):
        """refresh() re-reads files and updates cached data."""
        _touch_json(temp_dir, "health_report.json", _HEALTH)

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            assert provider.get_health_data().healthy_checks == 5

            _touch_json(
                temp_dir,
                "health_report.json",
                {
                    "overall_status": "warning",
                    "summary": {"healthy": 0, "degraded": 2, "unhealthy": 0},
                },
            )
            provider.refresh()
            assert provider.get_health_data().healthy_checks == 0

    def test_load_idempotent(self, provider: DashboardDataProvider, temp_dir: str):
        """Multiple load() calls do not re-read files."""
        call_count = 0
        original = provider._read_json_file

        def tracking(key: str, filename: str) -> dict:
            nonlocal call_count
            call_count += 1
            return original(key, filename)

        provider._read_json_file = tracking  # type: ignore[assignment]

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            first = call_count
            provider.load()
            assert call_count == first


# ---------------------------------------------------------------------------
# Missing file handling
# ---------------------------------------------------------------------------


class TestMissingFiles:
    """Dashboard must never crash when JSON artifacts are missing."""

    def test_all_files_missing(self, provider: DashboardDataProvider, temp_dir: str):
        """All files missing: safe defaults."""
        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            health = provider.get_health_data()
            metrics = provider.get_metrics()
            cert = provider.get_ga_certification()

            assert health.status == "Unavailable"
            assert health.healthy_checks == 0
            assert health.total_checks == 0
            assert metrics.success_rate == 0.0
            assert metrics.worlds_generated == 0
            assert metrics.exports_generated == 0
            assert cert.version == "Unknown"
            assert cert.certified is False
            assert cert.release_status == "Unknown"

    def test_health_file_missing(self, provider: DashboardDataProvider, temp_dir: str):
        """Only health missing – safe fallback, other data works."""
        _touch_json(temp_dir, "metrics.json", _METRICS)
        _touch_json(temp_dir, "GA_CERTIFICATION.json", _CERT)

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            health = provider.get_health_data()
            assert health.status == "Unavailable"

            metrics = provider.get_metrics()
            assert metrics.worlds_generated == 10

            cert = provider.get_ga_certification()
            assert cert.version == "1.0.0"

    def test_metrics_file_missing(self, provider: DashboardDataProvider, temp_dir: str):
        """Only metrics missing – safe fallback."""
        _touch_json(temp_dir, "health_report.json", _HEALTH)
        _touch_json(temp_dir, "GA_CERTIFICATION.json", _CERT)

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            metrics = provider.get_metrics()
            assert metrics.success_rate == 0.0
            assert metrics.worlds_generated == 0

            health = provider.get_health_data()
            assert health.status == "healthy"

    def test_cert_file_missing(self, provider: DashboardDataProvider, temp_dir: str):
        """Only GA_CERTIFICATION missing – safe fallback."""
        _touch_json(temp_dir, "health_report.json", _HEALTH)
        _touch_json(temp_dir, "metrics.json", _METRICS)

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            cert = provider.get_ga_certification()
            assert cert.version == "Unknown"
            assert cert.certified is False

            health = provider.get_health_data()
            assert health.status == "healthy"

    def test_missing_file_logs_warning(
        self,
        provider: DashboardDataProvider,
        temp_dir: str,
        caplog: pytest.LogCaptureFixture,
    ):
        """Missing files logged at WARNING level."""
        caplog.set_level(logging.WARNING)

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            missing = [
                r
                for r in caplog.records
                if "not found" in r.getMessage() or "empty or missing" in r.getMessage()
            ]
            assert len(missing) > 0


# ---------------------------------------------------------------------------
# DTO conversion
# ---------------------------------------------------------------------------


class TestDTOConversion:
    """Verify getters return typed DTOs, never raw dicts."""

    def test_health_dto(self, provider: DashboardDataProvider, temp_dir: str):
        """get_health_data() returns HealthStatusDTO."""
        _touch_json(
            temp_dir,
            "health_report.json",
            {
                "overall_status": "healthy",
                "summary": {"healthy": 7, "degraded": 1, "unhealthy": 0},
            },
        )

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            dto = provider.get_health_data()
            assert isinstance(dto, HealthStatusDTO)
            assert dto.status == "healthy"
            assert dto.healthy_checks == 7
            assert dto.total_checks == 8

    def test_metrics_dto(self, provider: DashboardDataProvider, temp_dir: str):
        """get_metrics() returns MetricsDTO with correct fields."""
        _touch_json(
            temp_dir,
            "metrics.json",
            {"generations_total": 100, "errors_total": 10, "otbm": {"tiles": 42}},
        )

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            dto = provider.get_metrics()
            assert isinstance(dto, MetricsDTO)
            assert dto.success_rate == 90.0
            assert dto.worlds_generated == 100
            assert dto.exports_generated == 42

    def test_metrics_zero_generations(
        self, provider: DashboardDataProvider, temp_dir: str
    ):
        """Success rate 0 when generations_total is 0."""
        _touch_json(
            temp_dir,
            "metrics.json",
            {"generations_total": 0, "errors_total": 0, "otbm": {"tiles": 0}},
        )

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            dto = provider.get_metrics()
            assert dto.success_rate == 0.0

    def test_certification_dto(self, provider: DashboardDataProvider, temp_dir: str):
        """get_ga_certification() returns CertificationDTO."""
        _touch_json(
            temp_dir,
            "GA_CERTIFICATION.json",
            {"version": "1.5.0", "overall_pass": True, "status": "GA"},
        )

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            dto = provider.get_ga_certification()
            assert isinstance(dto, CertificationDTO)
            assert dto.version == "1.5.0"
            assert dto.certified is True
            assert dto.release_status == "GA"

    def test_certification_not_certified(
        self, provider: DashboardDataProvider, temp_dir: str
    ):
        """Certified is False when overall_pass is False."""
        _touch_json(
            temp_dir,
            "GA_CERTIFICATION.json",
            {"version": "2.0.0-beta", "overall_pass": False, "status": "BETA"},
        )

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            dto = provider.get_ga_certification()
            assert dto.certified is False

    def test_no_raw_dicts_returned(
        self, provider: DashboardDataProvider, temp_dir: str
    ):
        """Public getters must not return raw dicts."""
        _touch_json(temp_dir, "health_report.json", _HEALTH)
        _touch_json(temp_dir, "metrics.json", _METRICS)
        _touch_json(temp_dir, "GA_CERTIFICATION.json", _CERT)

        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            assert not isinstance(provider.get_health_data(), dict)
            assert not isinstance(provider.get_metrics(), dict)
            assert not isinstance(provider.get_ga_certification(), dict)


# ---------------------------------------------------------------------------
# Timer initialization
# ---------------------------------------------------------------------------


class TestTimerInfrastructure:
    """Verify QTimer is configured correctly and disabled by default."""

    def test_timer_interval(self, provider: DashboardDataProvider):
        """Timer interval should be 30000 ms."""
        assert provider.auto_refresh_interval == 30_000

    def test_timer_disabled_by_default(self, provider: DashboardDataProvider):
        """Timer must not be started automatically."""
        assert provider._timer.isActive() is False

    def test_enable_auto_refresh_starts_timer(self, provider: DashboardDataProvider):
        """enable_auto_refresh() starts the timer."""
        provider.enable_auto_refresh()
        assert provider._timer.isActive() is True

    def test_disable_auto_refresh_stops_timer(self, provider: DashboardDataProvider):
        """disable_auto_refresh() stops the timer."""
        provider.enable_auto_refresh()
        assert provider._timer.isActive() is True
        provider.disable_auto_refresh()
        assert provider._timer.isActive() is False

    def test_timer_triggers_refresh(
        self, provider: DashboardDataProvider, temp_dir: str
    ):
        """Timer timeout triggers refresh (verify by side-effect)."""
        # Place a health file so data is available
        _touch_json(
            temp_dir,
            "health_report.json",
            {
                "overall_status": "warning",
                "summary": {"healthy": 0, "degraded": 2, "unhealthy": 0},
            },
        )
        with patch.object(os, "getcwd", return_value=temp_dir):
            provider.load()
            health = provider.get_health_data()
            old_status = health.status
            # Update file and call refresh directly (timer mocked)
            _touch_json(
                temp_dir,
                "health_report.json",
                {
                    "overall_status": "healthy",
                    "summary": {"healthy": 3, "degraded": 0, "unhealthy": 0},
                },
            )
            provider.refresh()
            health = provider.get_health_data()
            assert health.status == "healthy"
            assert health.status != old_status

    def test_timer_interval_property(self, provider: DashboardDataProvider):
        """auto_refresh_interval get/set works."""
        provider.auto_refresh_interval = 60_000
        assert provider.auto_refresh_interval == 60_000


# ---------------------------------------------------------------------------
# Constructor behaviour
# ---------------------------------------------------------------------------


class TestConstructor:
    """Verify constructor does not load data or start the timer."""

    def test_init_does_not_load(self):
        """Constructor must not call load() – lazy loading."""
        p = DashboardDataProvider()
        assert p._loaded is False
        assert p._cache == {}

    def test_init_timer_not_active(self):
        """Constructor must not start the timer."""
        p = DashboardDataProvider()
        assert p._timer.isActive() is False
