"""
hotfix_audit.py — v1.0.1 HOTFIX Post-GA Audit.

Phase 1 of the v1.0.1 HOTFIX mission.

Analyzes:
    logs/
    metrics.json
    health_report.json
    diagnostics.json
    GA_METRICS.json
    GA_CERTIFICATION.json

Detects:
    exceptions
    warnings
    slow paths
    memory spikes
    OTBM anomalies

Generates:
    HOTFIX_AUDIT.json
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ── Helpers ──────────────────────────────────────────────────────────────────


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_load_json(path: Path) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


# Patterns: each one is intentionally narrow to avoid false positives from
# workflow JSON keys like "error" or "failed".
LEVEL_RE = re.compile(r"\b(DEBUG|INFO|WARN|WARNING|ERROR|CRITICAL|FATAL)\b")
SLOW_RE = re.compile(
    r"(?i)(?:\bslow\b|\btimeout\b|\belapsed\b|"
    r"took\s*[:=]?\s*(\d+(?:\.\d+)?)\s*s|"
    r"duration\s*[:=]?\s*(\d+(?:\.\d+)?)\s*ms)"
)
MEM_RE = re.compile(
    r"(?i)\b(memory\s*leak|\boom\b|memory\s*spike|\brss\b|"
    r"peak\s*memory|tracemalloc)\b"
)
# Match only real error indicators, not bare JSON keys.
EXC_RE = re.compile(
    r"(?i)(?:\|\s*ERROR\s*\|"
    r"|\|\s*FATAL\s*\|"
    r"|\|\s*CRITICAL\s*\|"
    r"|Traceback\s*\(most recent call last\)"
    r"|unhandled\s*exception"
    r"|segmentation\s*fault"
    r"|stack\s*trace"
    r"|fatal\s*error"
    r"|\bcrash(?:ed)?\b"
    r"|Traceback)"
)
WARN_RE = re.compile(
    r"(?i)(?:\|\s*WARN(?:ING)?\s*\|"
    r"|\bwarning\s*[:=]"
    r"|\bdeprecat(?:ed|ion)\b"
    r"|\bcaution\b)"
)


def _scan_log_file(path: Path) -> Dict[str, Any]:
    """Scan a single .log file for genuine errors/warnings/slow paths."""
    findings: Dict[str, Any] = {
        "path": str(path.relative_to(PROJECT_ROOT)),
        "size_bytes": 0,
        "line_count": 0,
        "levels": Counter(),
        "exceptions": [],
        "warnings": [],
        "slow_paths": [],
        "memory_mentions": [],
    }
    if not path.exists():
        findings["error"] = "file_not_found"
        return findings
    findings["size_bytes"] = path.stat().st_size
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                findings["line_count"] += 1
                lvl = LEVEL_RE.search(line)
                if lvl:
                    findings["levels"][lvl.group(1)] += 1
                if EXC_RE.search(line):
                    findings["exceptions"].append(
                        {
                            "line": i,
                            "text": line.strip()[:240],
                        }
                    )
                if WARN_RE.search(line):
                    findings["warnings"].append(
                        {
                            "line": i,
                            "text": line.strip()[:240],
                        }
                    )
                m = SLOW_RE.search(line)
                if m:
                    try:
                        val = float(m.group(1) or m.group(2) or 0)
                        unit = "s" if m.group(1) else "ms"
                        findings["slow_paths"].append(
                            {
                                "line": i,
                                "value": val,
                                "unit": unit,
                                "text": line.strip()[:240],
                            }
                        )
                    except (ValueError, TypeError):
                        pass
                if MEM_RE.search(line):
                    findings["memory_mentions"].append(
                        {
                            "line": i,
                            "text": line.strip()[:240],
                        }
                    )
    except OSError as e:
        findings["scan_error"] = str(e)
    # Cap findings
    for k in ("exceptions", "warnings", "slow_paths", "memory_mentions"):
        findings[k] = findings[k][:25]
    return findings


def _scan_workflow_file(path: Path) -> Dict[str, Any]:
    """Analyze a workflow JSON for failures, warnings, and durations."""
    info: Dict[str, Any] = {"path": str(path.relative_to(PROJECT_ROOT))}
    if not path.exists():
        return {"path": info["path"], "error": "not_found"}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError) as e:
        return {"path": info["path"], "error": str(e)}
    tasks = data.get("tasks", {}) or {}
    agent_failures = 0
    agent_warnings = 0
    error_tasks: List[Dict[str, Any]] = []
    durations: List[float] = []
    per_agent: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"ok": 0, "fail": 0, "warn": 0}
    )
    for tid, task in tasks.items():
        agent = task.get("agent_id", "unknown")
        status = task.get("status", "unknown")
        resp = task.get("response", {}) or {}
        if status != "completed":
            agent_failures += 1
            per_agent[agent]["fail"] += 1
            err = resp.get("error")
            error_tasks.append(
                {
                    "task_id": tid,
                    "agent": agent,
                    "error": str(err)[:240],
                }
            )
        else:
            per_agent[agent]["ok"] += 1
        for w in resp.get("warnings", []) or []:
            agent_warnings += 1
            per_agent[agent]["warn"] += 1
        try:
            durations.append(float(resp.get("metrics", {}).get("execution_time", 0.0)))
        except (TypeError, ValueError):
            pass
    return {
        "path": info["path"],
        "workflow_id": data.get("workflow_id"),
        "status": data.get("status"),
        "agents": len(tasks),
        "agent_failures": agent_failures,
        "agent_warnings": agent_warnings,
        "error_tasks": error_tasks[:5],
        "max_duration_s": round(max(durations) if durations else 0.0, 4),
        "total_duration_s": round(sum(durations), 4),
        "per_agent": dict(per_agent),
    }


# ── Main audit ───────────────────────────────────────────────────────────────


def run_audit() -> Dict[str, Any]:
    audit: Dict[str, Any] = {
        "audit_version": "1.0.1",
        "generated_at": _utc_iso(),
        "project_root": str(PROJECT_ROOT),
        "phase": "FASE 1 - POST-GA AUDIT",
    }

    # 1. Logs directory
    logs_dir = PROJECT_ROOT / "logs"
    log_files = sorted(logs_dir.rglob("*.log")) if logs_dir.exists() else []
    workflow_files = (
        sorted(logs_dir.rglob("workflow_*.json")) if logs_dir.exists() else []
    )

    log_scan: List[Dict[str, Any]] = []
    workflow_scan: List[Dict[str, Any]] = []
    total_exc = 0
    total_warn = 0
    total_slow = 0
    total_mem = 0
    level_agg: Counter = Counter()

    for p in log_files:
        s = _scan_log_file(p)
        log_scan.append(s)
        total_exc += len(s.get("exceptions", []))
        total_warn += len(s.get("warnings", []))
        total_slow += len(s.get("slow_paths", []))
        total_mem += len(s.get("memory_mentions", []))
        for k, v in s.get("levels", {}).items():
            level_agg[k] += v

    for p in workflow_files:
        workflow_scan.append(_scan_workflow_file(p))
    fail_workflows = sum(1 for w in workflow_scan if w.get("agent_failures", 0) > 0)

    audit["logs"] = {
        "scanned_files": len(log_files),
        "workflow_files": len(workflow_files),
        "levels": dict(level_agg),
        "totals": {
            "exceptions": total_exc,
            "warnings": total_warn,
            "slow_paths": total_slow,
            "memory_mentions": total_mem,
            "failed_workflows": fail_workflows,
        },
    }
    audit["log_files"] = log_scan[:50]
    audit["workflow_files_sample"] = workflow_scan[:25]

    # 2. Top-level artifacts
    artifacts: Dict[str, Any] = {}
    for name in (
        "metrics.json",
        "health_report.json",
        "diagnostics.json",
        "GA_METRICS.json",
        "GA_CERTIFICATION.json",
    ):
        artifacts[name] = _safe_load_json(PROJECT_ROOT / name)
    audit["artifacts"] = artifacts

    # 3. Anomaly detection
    anomalies: List[Dict[str, Any]] = []
    diag = artifacts.get("diagnostics.json") or {}
    if diag.get("recent_errors"):
        anomalies.append(
            {
                "source": "diagnostics.json",
                "kind": "recent_errors",
                "count": len(diag["recent_errors"]),
            }
        )
    metrics = artifacts.get("metrics.json") or {}
    if metrics.get("errors_total", 0) > 0:
        anomalies.append(
            {
                "source": "metrics.json",
                "kind": "errors_total",
                "value": metrics["errors_total"],
            }
        )
    if metrics.get("memory_peak_mb", 0) > 0:
        anomalies.append(
            {
                "source": "metrics.json",
                "kind": "memory_peak_mb",
                "value": metrics["memory_peak_mb"],
            }
        )
    health = artifacts.get("health_report.json") or {}
    summary = health.get("summary", {}) or {}
    if summary.get("unhealthy", 0) > 0:
        anomalies.append(
            {
                "source": "health_report.json",
                "kind": "unhealthy_checks",
                "value": summary["unhealthy"],
            }
        )
    if summary.get("degraded", 0) > 0:
        anomalies.append(
            {
                "source": "health_report.json",
                "kind": "degraded_checks",
                "value": summary["degraded"],
            }
        )
    ga_metrics = artifacts.get("GA_METRICS.json") or {}
    if ga_metrics.get("benchmark", {}).get("success_rate", 1.0) < 0.99:
        anomalies.append(
            {
                "source": "GA_METRICS.json",
                "kind": "benchmark_success_rate_below_target",
                "value": ga_metrics["benchmark"]["success_rate"],
            }
        )
    ga_cert = artifacts.get("GA_CERTIFICATION.json") or {}
    if not ga_cert.get("overall_pass", False):
        anomalies.append(
            {
                "source": "GA_CERTIFICATION.json",
                "kind": "ga_overall_pass_false",
            }
        )
    audit["anomalies"] = anomalies

    # 4. OTBM anomalies
    otbm_issues: List[Dict[str, Any]] = []
    for sub in ("exports", "output"):
        d = PROJECT_ROOT / sub
        if not d.exists():
            continue
        for otbm in d.rglob("*.otbm"):
            try:
                size = otbm.stat().st_size
            except OSError:
                continue
            if size < 16:
                otbm_issues.append(
                    {
                        "path": str(otbm.relative_to(PROJECT_ROOT)),
                        "issue": "too_small",
                        "size": size,
                    }
                )
    audit["otbm_anomalies"] = {
        "count": len(otbm_issues),
        "issues": otbm_issues[:20],
    }

    # 5. Hotfix classifications
    error_counter: Counter = Counter()
    for _w in workflow_scan:
        for _et in _w.get("error_tasks", []) or []:
            _err = _et.get("error") or "unknown"
            _key = _err[:60] if _err and _err != "None" else "unknown"
            error_counter[_key] += 1
    error_signatures: List[Dict[str, Any]] = [
        {"signature": k, "count": v} for k, v in error_counter.most_common(10)
    ]
    classifications: List[Dict[str, Any]] = []
    if total_exc > 0:
        classifications.append(
            {
                "category": "bug_fix",
                "severity": "high",
                "summary": f"{total_exc} exception mentions in .log files",
            }
        )
    if total_warn > 0:
        classifications.append(
            {
                "category": "stability_fix",
                "severity": "medium",
                "summary": f"{total_warn} warning mentions in .log files",
            }
        )
    if total_slow > 0:
        classifications.append(
            {
                "category": "performance",
                "severity": "low",
                "summary": f"{total_slow} slow-path mentions in .log files",
            }
        )
    if fail_workflows > 0:
        classifications.append(
            {
                "category": "stability_fix",
                "severity": "high",
                "summary": f"{fail_workflows} workflows with agent failures",
            }
        )
    if not classifications:
        classifications.append(
            {
                "category": "no_action",
                "severity": "info",
                "summary": "No anomalies detected; baseline is clean.",
            }
        )
    audit["hotfix_classifications"] = classifications
    audit["error_signatures"] = error_signatures

    # 6. Verdict
    critical = total_exc + fail_workflows + summary.get("unhealthy", 0)
    audit["verdict"] = {
        "critical_count": critical,
        "ready_for_hotfix": critical == 0,
    }

    return audit


def main() -> int:
    audit = run_audit()
    out_path = PROJECT_ROOT / "HOTFIX_AUDIT.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2, ensure_ascii=False, default=str)
    print(f"[hotfix-audit] wrote {out_path}")
    print(f"  scanned_logs={audit['logs']['scanned_files']}")
    print(f"  workflows={audit['logs']['workflow_files']}")
    print(f"  exceptions={audit['logs']['totals']['exceptions']}")
    print(f"  warnings={audit['logs']['totals']['warnings']}")
    print(f"  slow_paths={audit['logs']['totals']['slow_paths']}")
    print(f"  memory_mentions={audit['logs']['totals']['memory_mentions']}")
    print(f"  anomalies={len(audit['anomalies'])}")
    print(f"  otbm_anomalies={audit['otbm_anomalies']['count']}")
    print(f"  verdict_ready={audit['verdict']['ready_for_hotfix']}")
    if audit["error_signatures"]:
        print("  top_error_signatures:")
        for s in audit["error_signatures"][:5]:
            print(f"    - {s['signature']}  x{s['count']}")
    return 0 if audit["verdict"]["ready_for_hotfix"] else 1


if __name__ == "__main__":
    sys.exit(main())
