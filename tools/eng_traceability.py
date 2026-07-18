"""
Generate ENG-03 engineering traceability chain.
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List


def _exists(root: Path, path: str) -> bool:
    return (root / path).exists()


def _git_commit(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"
    except Exception:
        return "UNAVAILABLE"


def _json(root: Path, path: str) -> Dict[str, Any]:
    target = root / path
    return json.loads(target.read_text(encoding="utf-8")) if target.exists() else {}


def build_trace(root: Path) -> Dict[str, Any]:
    commit = _git_commit(root)
    passport = _json(root, "ENGINEERING_PASSPORT.json")
    eng = _json(root, "ENG-01_review.json")
    stages = [
        {
            "stage": "Implementation",
            "status": "PASS",
            "evidence": [
                "reports/MAP/MAP-01/01_IMPLEMENTATION_REPORT.md",
                "ui/live_preview/mapping_engine.py",
                "ui/live_preview/map_project.py",
            ],
            "blocking": False,
            "responsible_engine": "MAP-01",
        },
        {
            "stage": "Compilation",
            "status": "PASS",
            "evidence": ["reports/MAP/MAP-01/02_EXECUTION_REPORT.md", "MAP-01_NECRO_pytest.log"],
            "blocking": True,
            "responsible_engine": "pytest/py_compile",
        },
        {
            "stage": "Testing",
            "status": "PASS",
            "evidence": ["MAP-01_NECRO_pytest.log", "MAP-01_NECRO_regression.log", "reports/MAP/MAP-01/03_TEST_RESULTS.md"],
            "blocking": True,
            "responsible_engine": "pytest",
        },
        {
            "stage": "Performance",
            "status": "PASS",
            "evidence": ["reports/PERF/PERF-01/PERF-01_BENCHMARK.md", "MAP-01_NECRO_execution_profile.json"],
            "blocking": True,
            "responsible_engine": "PERF-01",
        },
        {
            "stage": "Workspace Engineering",
            "status": "WARNING",
            "evidence": ["reports/WEM/WEM-01/WEM-01_ENGINEERING_COMPLEXITY_MODEL.md", "reports/WEM/WEM-02/WEM-02_QUALITY_GATES.md"],
            "blocking": True,
            "responsible_engine": "WEM-01/WEM-02",
        },
        {
            "stage": "Documentation",
            "status": "PASS",
            "evidence": [
                "docs/standards/EDS-01_ENGINEERING_DOCUMENTATION_STANDARD.md",
                "reports/MAP/MAP-01/MANIFEST.md",
                "reports/PROJECTS/NECRO/PROJECT-01_NECRO_STATUS.md",
            ],
            "blocking": True,
            "responsible_engine": "EDS",
        },
        {
            "stage": "Engineering Review",
            "status": "PASS",
            "evidence": ["reports/ENG/ENG-01/ENG-01_DECISION_MATRIX.md", "ENG-01_review.json"],
            "blocking": True,
            "responsible_engine": "ENG-01",
        },
        {
            "stage": "Engineering Passport",
            "status": "PASS",
            "evidence": ["ENGINEERING_PASSPORT.md", "ENGINEERING_PASSPORT.json", "ENGINEERING_PASSPORT.pdf"],
            "blocking": False,
            "responsible_engine": "ENG-02",
        },
        {
            "stage": "Human Review",
            "status": "PENDING",
            "evidence": ["Manual approval required"],
            "blocking": True,
            "responsible_engine": "Human",
        },
    ]
    broken = []
    for stage in stages:
        missing = [item for item in stage["evidence"] if not item.startswith("Manual") and not _exists(root, item)]
        stage["missing_evidence"] = missing
        if missing and stage["blocking"]:
            broken.append({"stage": stage["stage"], "missing": missing})

    trace_broken = bool(broken)
    return {
        "document_id": "ENG-03_ENGINEERING_TRACEABILITY",
        "version": "1.0.0",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "project": "RME AI Studio",
        "milestone": "MAP-01",
        "milestone_version": passport.get("milestone_version", "UNKNOWN"),
        "git_commit": commit,
        "readiness_score": eng.get("readiness_score"),
        "engineering_decision": passport.get("engineering_decision", "READY FOR HUMAN REVIEW"),
        "human_review": "PENDING",
        "certification": "NOT REQUESTED",
        "traceability_status": "BROKEN" if trace_broken else "COMPLETE_WITH_HUMAN_REVIEW_PENDING",
        "broken_conditions": broken,
        "stages": stages,
        "change_history": [
            {
                "milestone": "MAP-01",
                "milestone_version": passport.get("milestone_version", "UNKNOWN"),
                "date": time.strftime("%Y-%m-%d"),
                "engineering_version": passport.get("engineering_version", "UNKNOWN"),
                "git_commit": commit,
                "decision": passport.get("engineering_decision", "READY FOR HUMAN REVIEW"),
                "readiness_score": eng.get("readiness_score"),
                "open_remediations": len(passport.get("active_remediations", [])),
            }
        ],
    }


def markdown(trace: Dict[str, Any]) -> str:
    lines = [
        "# ENG-03 Engineering Traceability",
        "",
        f"Document ID: {trace['document_id']}",
        f"Version: {trace['version']}",
        f"Project: {trace['project']}",
        f"Milestone: {trace['milestone']}",
        f"Milestone Version: {trace['milestone_version']}",
        f"Git Commit: {trace['git_commit']}",
        f"Status: {trace['traceability_status']}",
        "",
        "No SUCCESS or CERTIFIED status is claimed.",
        "",
        "## Traceability Matrix",
        "",
        "| Stage | Status | Evidence | Blocking | Missing Evidence |",
        "|---|---|---|---|---|",
    ]
    for stage in trace["stages"]:
        lines.append(
            f"| {stage['stage']} | {stage['status']} | {', '.join(stage['evidence'])} | {'Yes' if stage['blocking'] else 'No'} | {', '.join(stage['missing_evidence']) or 'None'} |"
        )
    lines.extend(
        [
            "",
            "## Blocking Conditions",
            "",
        ]
    )
    if trace["broken_conditions"]:
        for condition in trace["broken_conditions"]:
            lines.append(f"- {condition['stage']}: missing {', '.join(condition['missing'])}")
    else:
        lines.append("- No broken blocking evidence chain detected.")
        lines.append("- Human review remains pending and blocks certification.")
    return "\n".join(lines) + "\n"


def graph_markdown(trace: Dict[str, Any]) -> str:
    return """# ENG-03 Traceability Graph

```mermaid
flowchart TD
    A["Engineering Constitution"] --> B["Implementation"]
    B --> C["Compilation"]
    C --> D["Testing"]
    D --> E["Performance Validation"]
    E --> F["Workspace Validation"]
    F --> G["Quality Gates"]
    G --> H["Engineering Review"]
    H --> I["Engineering Passport"]
    I --> J["Human Review"]
    J --> K["Engineering Certification (when applicable)"]
```
"""


def change_history(trace: Dict[str, Any]) -> str:
    lines = [
        "# ENG-03 Change History",
        "",
        "| Milestone | Version | Date | Engineering Version | Git Commit | Decision | Readiness Score | Open Remediations |",
        "|---|---|---|---|---|---|---:|---:|",
    ]
    for item in trace["change_history"]:
        lines.append(
            f"| {item['milestone']} | {item['milestone_version']} | {item['date']} | {item['engineering_version']} | {item['git_commit']} | {item['decision']} | {item['readiness_score']} | {item['open_remediations']} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    root = Path.cwd()
    out_dir = root / "reports" / "ENG" / "ENG-03"
    out_dir.mkdir(parents=True, exist_ok=True)
    trace = build_trace(root)
    outputs = {
        "ENG-03_TRACEABILITY.md": markdown(trace),
        "ENG-03_TRACEABILITY_GRAPH.md": graph_markdown(trace),
        "ENG-03_CHANGE_HISTORY.md": change_history(trace),
        "ENG-03_EXECUTION_LOG.txt": "\n".join(
            [
                "ENG-03 execution log",
                f"timestamp={trace['timestamp']}",
                f"milestone={trace['milestone']}",
                f"milestone_version={trace['milestone_version']}",
                f"git_commit={trace['git_commit']}",
                f"traceability_status={trace['traceability_status']}",
                f"human_review={trace['human_review']}",
                f"broken_conditions={len(trace['broken_conditions'])}",
            ]
        )
        + "\n",
    }
    for filename, content in outputs.items():
        (root / filename).write_text(content, encoding="utf-8")
        (out_dir / filename).write_text(content, encoding="utf-8")
    for base in [root, out_dir]:
        (base / "ENG-03_TRACEABILITY.json").write_text(json.dumps(trace, indent=2), encoding="utf-8")
    print(json.dumps(trace, indent=2))


if __name__ == "__main__":
    main()
