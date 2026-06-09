"""
core/observability/__init__.py

Public exports for the Agente RME v1.0.0 GA observability layer.
"""

from __future__ import annotations

from .logger import (
    ObservabilityLogger,
    get_observability_logger,
    reset_observability_logger,
)
from .metrics import (
    AgentMetric,
    MetricsCollector,
    MetricsSnapshot,
    OTBMSnapshot,
)
from .health import (
    CheckResult,
    HealthChecker,
    HealthReport,
    HealthStatus,
)
from .diagnostics import DiagnosticReport, Diagnostics

__all__ = [
    "ObservabilityLogger",
    "get_observability_logger",
    "reset_observability_logger",
    "AgentMetric",
    "MetricsCollector",
    "MetricsSnapshot",
    "OTBMSnapshot",
    "CheckResult",
    "HealthChecker",
    "HealthReport",
    "HealthStatus",
    "DiagnosticReport",
    "Diagnostics",
]
