"""
core/observability/diagnostics.py

On-demand diagnostic dump for Agente RME v1.0.0 GA.

Provides a structured snapshot of:
  - environment (python, platform)
  - paths (cwd, project root)
  - file counts (logs, output, exports)
  - top errors from the most recent log file
  - uptime
  - config presence

Usage:
    from core.observability.diagnostics import Diagnostics
    d = Diagnostics()
    report = d.collect()
    d.export(report, "diagnostics.json")
"""

from __future__ import annotations

import json
import os
import platform
import re
import sys
import time
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logger import _utc_iso


@dataclass
class DiagnosticReport:
    timestamp: str
    python: str
    platform: str
    cwd: str
    project_root: str
    uptime_seconds: float
    file_counts: Dict[str, int]
    recent_errors: List[Dict[str, Any]]
    config_present: Dict[str, bool]
    ollama_reachable: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Diagnostics:
    """Collect a diagnostic snapshot."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        self._start = time.time()
        self._project_root = project_root or Path(__file__).resolve().parents[2]

    def collect(self) -> DiagnosticReport:
        file_counts = self._count_files()
        recent_errors = self._recent_errors()
        config_present = self._check_configs()
        ollama = self._check_ollama()
        return DiagnosticReport(
            timestamp=_utc_iso(),
            python=sys.version.split()[0],
            platform=platform.platform(),
            cwd=os.getcwd(),
            project_root=str(self._project_root),
            uptime_seconds=time.time() - self._start,
            file_counts=file_counts,
            recent_errors=recent_errors,
            config_present=config_present,
            ollama_reachable=ollama,
        )

    def _count_files(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for sub in ("logs", "output", "exports", "release"):
            p = self._project_root / sub
            if p.exists() and p.is_dir():
                files = [f for f in p.rglob("*") if f.is_file()]
                out[sub] = len(files)
            else:
                out[sub] = 0
        return out

    def _recent_errors(self, max_lines: int = 5000) -> List[Dict[str, Any]]:
        log_dir = self._project_root / "logs"
        if not log_dir.exists():
            return []
        logs = sorted(log_dir.glob("*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not logs:
            return []
        latest = logs[0]
        try:
            text = latest.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return []
        lines = text.splitlines()[-max_lines:]
        err_re = re.compile(r"\b(ERROR|CRITICAL)\b")
        errors: List[Dict[str, Any]] = []
        for line in lines:
            if err_re.search(line):
                errors.append({"file": latest.name, "line": line})
        # Aggregate by message prefix
        counter: Counter = Counter()
        for e in errors[-200:]:
            counter[e["line"][:120]] += 1
        return [{"message": k, "count": v} for k, v in counter.most_common(10)]

    def _check_configs(self) -> Dict[str, bool]:
        return {
            "config/production.yaml": (self._project_root / "config/production.yaml").exists(),
            "config/development.yaml": (self._project_root / "config/development.yaml").exists(),
            "config/default.yaml": (self._project_root / "config/default.yaml").exists(),
            "config.json": (self._project_root / "config.json").exists(),
            "pyproject.toml": (self._project_root / "pyproject.toml").exists(),
            "requirements.txt": (self._project_root / "requirements.txt").exists(),
            "requirements-lock.txt": (self._project_root / "requirements-lock.txt").exists(),
        }

    def _check_ollama(self) -> bool:
        try:
            import requests  # type: ignore
            r = requests.get("http://localhost:11434/api/tags", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def export(self, report: DiagnosticReport, path: str = "diagnostics.json") -> str:
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        return str(out)
