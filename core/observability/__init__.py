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
from .event_bus import EventBus, get_event_bus, reset_event_bus
from .event_emitter import EventEmitter, emit_generation_event
from .event_models import EventCategory, EventSeverity, GenerationEvent
from .event_storage import EventStorage
from .observability_reporter import ObservabilityReporter
from .trace_manager import TraceContext, TraceManager

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
    "EventBus",
    "get_event_bus",
    "reset_event_bus",
    "EventEmitter",
    "emit_generation_event",
    "EventCategory",
    "EventSeverity",
    "GenerationEvent",
    "EventStorage",
    "ObservabilityReporter",
    "TraceContext",
    "TraceManager",
]
