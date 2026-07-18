"""
core/observability/health.py

System health checks for Agente RME v1.0.0 GA.

Monitors:
  - system health   (CPU, memory, disk)
  - module health   (knowledge, blueprint, generator modules loadable)
  - pipeline health (Lua/OTBM exporters work)
  - knowledge health (dataset present and valid)
  - blueprint health (blueprint files present)

CLI:
    rme health        # run all checks, print & export health_report.json

Usage:
    from core.observability.health import HealthChecker
    hc = HealthChecker()
    report = hc.run_all()
    print(report.overall_status)   # "healthy" | "degraded" | "unhealthy"
"""

from __future__ import annotations

import json
import shutil
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List

from .logger import _utc_iso


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class CheckResult:
    name: str
    category: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class HealthReport:
    timestamp: str
    overall_status: str
    summary: Dict[str, int]
    checks: List[CheckResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status,
            "summary": self.summary,
            "checks": [c.to_dict() for c in self.checks],
        }


# ── Individual check functions ──────────────────────────────────────────────


def _check_system() -> CheckResult:
    details: Dict[str, Any] = {}
    status = HealthStatus.HEALTHY
    msg = "system operational"
    try:
        details["python"] = sys.version.split()[0]
        details["platform"] = sys.platform
        try:
            import psutil  # type: ignore

            vm = psutil.virtual_memory()
            details["cpu_count"] = psutil.cpu_count()
            details["memory_total_mb"] = round(vm.total / (1024 * 1024), 2)
            details["memory_available_mb"] = round(vm.available / (1024 * 1024), 2)
            details["memory_percent"] = vm.percent
            if vm.percent > 90:
                status = HealthStatus.UNHEALTHY
                msg = "memory critical"
            elif vm.percent > 75:
                status = HealthStatus.DEGRADED
                msg = "memory high"
        except ImportError:
            details["psutil"] = "unavailable"
        du = shutil.disk_usage(".")
        details["disk_total_gb"] = round(du.total / (1024**3), 2)
        details["disk_free_gb"] = round(du.free / (1024**3), 2)
        details["disk_percent"] = round((du.used / du.total) * 100, 2)
        if details["disk_percent"] > 95:
            status = HealthStatus.UNHEALTHY
            msg = "disk critical"
    except Exception as e:
        status = HealthStatus.UNHEALTHY
        msg = f"system check failed: {e}"
    return CheckResult(
        name="system",
        category="system",
        status=status,
        message=msg,
        details=details,
        timestamp=_utc_iso(),
    )


def _check_module(name: str, import_path: str) -> CheckResult:
    try:
        __import__(import_path)
        return CheckResult(
            name=name,
            category="module",
            status=HealthStatus.HEALTHY,
            message=f"import ok: {import_path}",
            timestamp=_utc_iso(),
        )
    except Exception as e:
        return CheckResult(
            name=name,
            category="module",
            status=HealthStatus.DEGRADED,
            message=f"import failed: {e}",
            timestamp=_utc_iso(),
        )


def _check_generators() -> CheckResult:
    return _check_module("generators", "core.generators")


def _check_exporters() -> CheckResult:
    return _check_module("exporters", "core.exporters")


def _check_otbm() -> CheckResult:
    return _check_module("otbm", "core.otbm")


def _check_preview() -> CheckResult:
    return _check_module("preview", "core.preview")


def _check_knowledge_mod() -> CheckResult:
    return _check_module("knowledge", "core.knowledge")


def _check_critic() -> CheckResult:
    return _check_module("critic", "core.critic")


def _check_blueprint_intelligence() -> CheckResult:
    return _check_module("blueprint_intelligence", "core.blueprint_intelligence")


def _check_pipeline() -> CheckResult:
    try:
        from core.generators import WorldGenerator

        gen = WorldGenerator(seed=42)
        world = gen.generate(
            {
                "type": "hunt",
                "theme": "issavi",
                "level_min": 250,
                "level_max": 320,
                "width": 8,
                "height": 8,
            }
        )
        tiles = world.tile_count() if hasattr(world, "tile_count") else 0
        if tiles == 0:
            return CheckResult(
                name="pipeline",
                category="pipeline",
                status=HealthStatus.UNHEALTHY,
                message="pipeline produced empty world",
                timestamp=_utc_iso(),
            )
        return CheckResult(
            name="pipeline",
            category="pipeline",
            status=HealthStatus.HEALTHY,
            message=f"pipeline ok ({tiles} tiles)",
            details={"tiles": tiles},
            timestamp=_utc_iso(),
        )
    except Exception as e:
        return CheckResult(
            name="pipeline",
            category="pipeline",
            status=HealthStatus.UNHEALTHY,
            message=f"pipeline failed: {e}",
            timestamp=_utc_iso(),
        )


def _check_knowledge() -> CheckResult:
    candidates = [
        Path("output/knowledge_dataset.json"),
        Path("rme_knowledge_cache.json"),
        Path("data/knowledge_dataset.json"),
    ]
    for p in candidates:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entries = data.get("entries", []) if isinstance(data, dict) else data
                count = len(entries) if isinstance(entries, list) else 0
                return CheckResult(
                    name="knowledge",
                    category="knowledge",
                    status=HealthStatus.HEALTHY,
                    message=f"dataset ok ({count} entries)",
                    details={"path": str(p), "entries": count},
                    timestamp=_utc_iso(),
                )
            except Exception as e:
                return CheckResult(
                    name="knowledge",
                    category="knowledge",
                    status=HealthStatus.DEGRADED,
                    message=f"dataset unreadable: {e}",
                    details={"path": str(p)},
                    timestamp=_utc_iso(),
                )
    return CheckResult(
        name="knowledge",
        category="knowledge",
        status=HealthStatus.DEGRADED,
        message="no knowledge dataset found",
        timestamp=_utc_iso(),
    )


def _check_blueprints() -> CheckResult:
    candidates = [
        Path("data/blueprints"),
        Path("data/demo_blueprints"),
        Path("blueprints"),
    ]
    found = 0
    for d in candidates:
        if d.exists() and d.is_dir():
            found += sum(1 for _ in d.glob("*.json"))
    if found == 0:
        return CheckResult(
            name="blueprints",
            category="blueprint",
            status=HealthStatus.DEGRADED,
            message="no blueprints found",
            details={"checked": [str(c) for c in candidates]},
            timestamp=_utc_iso(),
        )
    return CheckResult(
        name="blueprints",
        category="blueprint",
        status=HealthStatus.HEALTHY,
        message=f"{found} blueprint file(s) present",
        details={"count": found},
        timestamp=_utc_iso(),
    )


# ── Aggregator ──────────────────────────────────────────────────────────────


class HealthChecker:
    """Aggregator for health checks."""

    def __init__(self) -> None:
        # Use individual check functions so each runs independently.
        self._checks: List[Callable[[], CheckResult]] = [
            _check_system,
            _check_generators,
            _check_exporters,
            _check_otbm,
            _check_preview,
            _check_knowledge_mod,
            _check_critic,
            _check_blueprint_intelligence,
            _check_pipeline,
            _check_knowledge,
            _check_blueprints,
        ]

    def run_all(self) -> HealthReport:
        results: List[CheckResult] = []
        for c in self._checks:
            try:
                results.append(c())
            except Exception as e:
                results.append(
                    CheckResult(
                        name=getattr(c, "__name__", "check"),
                        category="unknown",
                        status=HealthStatus.UNHEALTHY,
                        message=f"check raised: {e}",
                        timestamp=_utc_iso(),
                    )
                )
        summary = {"healthy": 0, "degraded": 0, "unhealthy": 0}
        for r in results:
            summary[r.status.value] += 1
        if summary["unhealthy"] > 0:
            overall = HealthStatus.UNHEALTHY
        elif summary["degraded"] > 0:
            overall = HealthStatus.DEGRADED
        else:
            overall = HealthStatus.HEALTHY
        return HealthReport(
            timestamp=_utc_iso(),
            overall_status=overall.value,
            summary=summary,
            checks=results,
        )

    def export(self, report: HealthReport, path: str = "health_report.json") -> str:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        return str(out)
