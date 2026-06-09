"""
core/observability/metrics.py

Performance & runtime metrics for Agente RME v1.0.0 GA.

Tracks:
  - agent execution (count, latency, success rate)
  - errors
  - performance (CPU, memory, generation speed)
  - memory (peak RSS, current RSS)
  - OTBM operations (tiles, items, spawns)

Export:
  - metrics.json  (latest snapshot)

Usage:
    from core.observability.metrics import MetricsCollector
    mc = MetricsCollector()
    mc.start_agent("world")
    mc.end_agent("world", success=True, tiles=4200)
    mc.export("metrics.json")
"""

from __future__ import annotations

import json
import os
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import psutil  # type: ignore
    _HAVE_PSUTIL = True
except ImportError:
    _HAVE_PSUTIL = False

from .logger import _utc_iso


@dataclass
class AgentMetric:
    name: str
    count: int = 0
    success: int = 0
    failure: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0
    min_ms: float = float("inf")
    last_ms: float = 0.0


@dataclass
class OTBMSnapshot:
    tiles: int = 0
    items: int = 0
    spawns: int = 0
    regions: int = 0
    last_export_ms: float = 0.0


@dataclass
class MetricsSnapshot:
    timestamp: str = ""
    uptime_seconds: float = 0.0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_peak_mb: float = 0.0
    agents: Dict[str, AgentMetric] = field(default_factory=dict)
    otbm: OTBMSnapshot = field(default_factory=OTBMSnapshot)
    errors_total: int = 0
    generations_total: int = 0
    last_generation_ms: float = 0.0


class MetricsCollector:
    """Thread-safe metrics collector."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._start_ts = time.time()
        self._agents: Dict[str, AgentMetric] = defaultdict(lambda: AgentMetric(name=""))
        self._active: Dict[str, float] = {}
        self._otbm = OTBMSnapshot()
        self._errors = 0
        self._generations = 0
        self._last_generation_ms = 0.0
        self._peak_rss_mb = 0.0

    # ------------------------------------------------------------------
    # Agent execution
    # ------------------------------------------------------------------

    def start_agent(self, name: str) -> None:
        with self._lock:
            self._active[name] = time.time()

    def end_agent(self, name: str, success: bool = True, **extra: Any) -> None:
        now = time.time()
        with self._lock:
            start = self._active.pop(name, None)
            if start is None:
                return
            elapsed = (now - start) * 1000.0
            m = self._agents[name]
            if m.name == "":
                m.name = name
            m.count += 1
            if success:
                m.success += 1
            else:
                m.failure += 1
            m.total_ms += elapsed
            m.last_ms = elapsed
            if elapsed > m.max_ms:
                m.max_ms = elapsed
            if elapsed < m.min_ms:
                m.min_ms = elapsed

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def record_generation(self, duration_ms: float, tiles: int = 0) -> None:
        with self._lock:
            self._generations += 1
            self._last_generation_ms = duration_ms

    # ------------------------------------------------------------------
    # Errors
    # ------------------------------------------------------------------

    def record_error(self, component: str = "", **extra: Any) -> None:
        with self._lock:
            self._errors += 1

    # ------------------------------------------------------------------
    # OTBM
    # ------------------------------------------------------------------

    def record_otbm(self, tiles: int = 0, items: int = 0, spawns: int = 0,
                    regions: int = 0, duration_ms: float = 0.0) -> None:
        with self._lock:
            self._otbm.tiles += tiles
            self._otbm.items += items
            self._otbm.spawns += spawns
            self._otbm.regions += regions
            self._otbm.last_export_ms = duration_ms

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def snapshot(self) -> MetricsSnapshot:
        cpu = 0.0
        rss_mb = 0.0
        if _HAVE_PSUTIL:
            try:
                proc = psutil.Process(os.getpid())
                cpu = proc.cpu_percent(interval=None)
                rss_mb = proc.memory_info().rss / (1024.0 * 1024.0)
                if rss_mb > self._peak_rss_mb:
                    self._peak_rss_mb = rss_mb
            except Exception:
                pass
        with self._lock:
            snap = MetricsSnapshot(
                timestamp=_utc_iso(),
                uptime_seconds=time.time() - self._start_ts,
                cpu_percent=cpu,
                memory_mb=rss_mb,
                memory_peak_mb=self._peak_rss_mb,
                errors_total=self._errors,
                generations_total=self._generations,
                last_generation_ms=self._last_generation_ms,
                otbm=OTBMSnapshot(
                    tiles=self._otbm.tiles,
                    items=self._otbm.items,
                    spawns=self._otbm.spawns,
                    regions=self._otbm.regions,
                    last_export_ms=self._otbm.last_export_ms,
                ),
            )
            for name, m in self._agents.items():
                snap.agents[name] = AgentMetric(
                    name=m.name,
                    count=m.count,
                    success=m.success,
                    failure=m.failure,
                    total_ms=m.total_ms,
                    max_ms=m.max_ms,
                    min_ms=m.min_ms if m.min_ms != float("inf") else 0.0,
                    last_ms=m.last_ms,
                )
        return snap

    def export(self, path: str = "metrics.json") -> str:
        """Write the current snapshot to JSON."""
        snap = self.snapshot()
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(_snapshot_to_dict(snap), f, indent=2, ensure_ascii=False, default=str)
        return str(out_path)

    def reset(self) -> None:
        with self._lock:
            self._start_ts = time.time()
            self._agents = defaultdict(lambda: AgentMetric(name=""))
            self._active = {}
            self._otbm = OTBMSnapshot()
            self._errors = 0
            self._generations = 0
            self._last_generation_ms = 0.0
            self._peak_rss_mb = 0.0


def _snapshot_to_dict(snap: MetricsSnapshot) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "timestamp": snap.timestamp,
        "uptime_seconds": round(snap.uptime_seconds, 3),
        "cpu_percent": round(snap.cpu_percent, 2),
        "memory_mb": round(snap.memory_mb, 2),
        "memory_peak_mb": round(snap.memory_peak_mb, 2),
        "errors_total": snap.errors_total,
        "generations_total": snap.generations_total,
        "last_generation_ms": round(snap.last_generation_ms, 2),
        "otbm": asdict(snap.otbm),
        "agents": {k: asdict(v) for k, v in snap.agents.items()},
    }
    return data
