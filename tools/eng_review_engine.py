"""
ENG-01 deterministic engineering review engine.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List


def _exists(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def _read_text(root: Path, relative: str) -> str:
    path = root / relative
    if not path.exists():
        return ""
    data = path.read_bytes()
    if b"\x00" in data[:200]:
        try:
            return data.decode("utf-16")
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace")
    return data.decode("utf-8", errors="replace")


def _pytest_passed(text: str) -> bool:
    lines = [line.strip().lower() for line in text.splitlines() if line.strip()]
    summary = lines[-1] if lines else ""
    return " passed " in summary and " failed " not in summary and " error " not in summary


def _gate_status(gates: Dict[str, str]) -> str:
    if any(value == "FAIL" for value in gates.values()):
        return "FAIL"
    if any(value == "WARNING" for value in gates.values()):
        return "WARNING"
    return "PASS"


def _score_status(score: int) -> str:
    if score >= 95:
        return "ENGINEERING READY"
    if score >= 85:
        return "READY FOR HUMAN REVIEW"
    if score >= 70:
        return "CONTINUE DEVELOPMENT"
    if score >= 60:
        return "ENGINEERING REMEDIATION REQUIRED"
    return "DEVELOPMENT BLOCKED"


def evaluate(root: Path) -> Dict[str, Any]:
    required_reports = [
        "reports/MAP/MAP-01/MANIFEST.md",
        "reports/MAP/MAP-01/01_IMPLEMENTATION_REPORT.md",
        "reports/MAP/MAP-01/02_EXECUTION_REPORT.md",
        "reports/MAP/MAP-01/03_TEST_RESULTS.md",
        "reports/MAP/MAP-01/04_CHECKLIST.md",
        "reports/MAP/MAP-01/05_VALIDATION_REPORT.md",
        "reports/MAP/MAP-01/06_SCORE.md",
        "reports/MAP/MAP-01/07_KNOWN_ISSUES.md",
        "reports/MAP/MAP-01/08_PERFORMANCE_REPORT.md",
        "reports/MAP/MAP-01/09_FINAL_REVIEW.md",
        "reports/MAP/MAP-01/09_ENGINEERING_PASSPORT.md",
        "reports/MAP/MAP-01/10_TRACEABILITY_REPORT.md",
        "reports/PROJECTS/NECRO/PROJECT-01_NECRO_STATUS.md",
        "reports/PROJECTS/NECRO/PROJECT-01_NECRO_MAP_PROGRESS.md",
        "reports/PROJECTS/NECRO/PROJECT-01_NECRO_OPEN_ISSUES.md",
        "reports/PROJECTS/NECRO/PROJECT-01_NECRO_EXECUTION_LOG.txt",
        "reports/WEM/WEM-02/WEM-02_QUALITY_GATES.md",
        "reports/WEM/WEM-02/WEM-02_ENGINEERING_DECISIONS.md",
        "reports/PERF/PERF-01/PERF-01_BENCHMARK.md",
    ]
    missing_reports = [report for report in required_reports if not _exists(root, report)]

    pytest_log_path = "MAP-01_NECRO_pytest.log" if _exists(root, "MAP-01_NECRO_pytest.log") else "MAP-01_pytest.log"
    execution_profile_path = "MAP-01_NECRO_execution_profile.json" if _exists(root, "MAP-01_NECRO_execution_profile.json") else "MAP-01_execution_profile.json"
    execution_log_path = (
        "reports/PROJECTS/NECRO/PROJECT-01_NECRO_EXECUTION_LOG.txt"
        if _exists(root, "reports/PROJECTS/NECRO/PROJECT-01_NECRO_EXECUTION_LOG.txt")
        else "MAP-01_execution.log"
    )
    pytest_log = _read_text(root, pytest_log_path)
    regression_log = _read_text(root, "MAP-01_NECRO_regression.log")
    pytest_ok = _pytest_passed(pytest_log) and (not regression_log or _pytest_passed(regression_log))
    execution_profile_exists = _exists(root, execution_profile_path)
    execution_log_exists = _exists(root, execution_log_path)
    necro_visual_dir = root / "reports" / "PROJECTS" / "NECRO" / "PROJECT-01_NECRO_VISUAL_EVIDENCE"
    visual_evidence = sorted(necro_visual_dir.glob("*.png")) if necro_visual_dir.exists() else []
    if not visual_evidence and (root / "MAP-01_visual_evidence").exists():
        visual_evidence = sorted((root / "MAP-01_visual_evidence").glob("*.png"))
    perf_profile = json.loads(_read_text(root, execution_profile_path) or "{}")
    wem_gates = json.loads(_read_text(root, "WEM-02_quality_gates.json") or "{}")
    gates = wem_gates.get("gates", {})
    gate_summary = _gate_status(gates)

    safe_mode_ok = (
        perf_profile.get("provider_loaded") is False
        and perf_profile.get("preview_initialized") is False
    )
    perf_ok = safe_mode_ok and float(perf_profile.get("ram_mb", 9999)) < 100
    compatibility_ok = all(
        phrase in _read_text(root, "reports/MAP/MAP-01/01_IMPLEMENTATION_REPORT.md")
        for phrase in [
            "No OTBM serialization modified",
            "No Export Center modified",
            "Safe Mode remains preserved",
        ]
    )

    decisions = {
        "Documentation": "PASS" if not missing_reports else "FAIL",
        "Execution": "PASS" if execution_profile_exists and execution_log_exists and visual_evidence else "FAIL",
        "Performance": "PASS" if perf_ok else "WARNING",
        "Workspace": "WARNING" if gate_summary == "WARNING" else gate_summary,
        "Compatibility": "PASS" if compatibility_ok else "FAIL",
        "Testing": "PASS" if pytest_ok else "FAIL",
        "Quality Gates": gate_summary,
    }

    scores = {
        "Documentation": 15 if decisions["Documentation"] == "PASS" else 0,
        "Execution Evidence": 20 if decisions["Execution"] == "PASS" else 0,
        "Testing": 20 if decisions["Testing"] == "PASS" else 0,
        "Performance": 15 if decisions["Performance"] == "PASS" else 10,
        "Workspace Quality": 12 if decisions["Workspace"] == "WARNING" else 15 if decisions["Workspace"] == "PASS" else 0,
        "Compatibility": 10 if decisions["Compatibility"] == "PASS" else 0,
        "Quality Gates": 3 if decisions["Quality Gates"] == "WARNING" else 5 if decisions["Quality Gates"] == "PASS" else 0,
        "Engineering Consistency": 10
        if "No SUCCESS or CERTIFIED status is claimed" in _read_text(root, "reports/MAP/MAP-01/09_FINAL_REVIEW.md")
        else 5,
    }
    raw_score = sum(scores.values())
    readiness_score = round(raw_score / 110 * 100)

    blockers = []
    if not pytest_ok:
        blockers.append("pytest failed or missing pass evidence")
    if decisions["Execution"] == "FAIL":
        blockers.append("execution evidence missing")
    if missing_reports:
        blockers.append("mandatory reports missing")
    if decisions["Compatibility"] == "FAIL":
        blockers.append("compatibility evidence failed")
    if decisions["Quality Gates"] == "FAIL":
        blockers.append("workspace quality gates failed")

    remediations: List[Dict[str, Any]] = []
    if decisions["Workspace"] == "WARNING":
        remediations.append(
            {
                "issue": "Workspace tabs exceed WEM-02 budget",
                "severity": "Medium",
                "evidence": "WEM-02 WG-02 and WG-03 are WARNING; workspace_tabs=34 budget=30",
                "affected_files": ["ui/live_preview/mapping_workspace.py"],
                "recommended_action": "Reduce visible tabs by grouping asset/inspector panels or lazy-loading tab contents.",
                "blocking_status": "Non-blocking for development; requires engineering review.",
                "priority": "P2",
                "owner": "UX/WEM",
            }
        )
    if readiness_score < 95:
        remediations.append(
            {
                "issue": "Human review required before any certification",
                "severity": "Governance",
                "evidence": f"Engineering readiness score is {readiness_score}",
                "affected_files": ["reports/ENG/ENG-01/"],
                "recommended_action": "Submit ENG-01 evidence to human review.",
                "blocking_status": "Blocks certification only.",
                "priority": "P1",
                "owner": "Engineering",
            }
        )

    overall = "REMEDIATION" if blockers else "REVIEW" if any(value == "WARNING" for value in decisions.values()) else "PASS"

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "milestone": "MAP-01",
        "decisions": decisions,
        "scores": scores,
        "raw_score": raw_score,
        "raw_score_max": 110,
        "readiness_score": readiness_score,
        "readiness_level": _score_status(readiness_score),
        "overall_decision": overall,
        "blockers": blockers,
        "remediations": remediations,
        "inputs": {
            "missing_reports": missing_reports,
            "pytest_log": pytest_log_path,
            "regression_log": "MAP-01_NECRO_regression.log",
            "execution_log": execution_log_path,
            "execution_profile": execution_profile_path,
            "visual_evidence_count": len(visual_evidence),
            "wem_quality_gates": "WEM-02_quality_gates.json",
        },
    }


def main() -> None:
    root = Path.cwd()
    result = evaluate(root)
    (root / "ENG-01_review.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    lines = [
        "ENG-01 execution log",
        f"timestamp={result['timestamp']}",
        f"milestone={result['milestone']}",
        f"readiness_score={result['readiness_score']}",
        f"readiness_level={result['readiness_level']}",
        f"overall_decision={result['overall_decision']}",
    ]
    lines.extend(f"{key}={value}" for key, value in result["decisions"].items())
    for blocker in result["blockers"]:
        lines.append(f"BLOCKER={blocker}")
    (root / "ENG-01_EXECUTION_LOG.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
